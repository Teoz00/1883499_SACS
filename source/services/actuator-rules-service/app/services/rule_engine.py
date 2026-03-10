import logging
import re
from dataclasses import dataclass
from typing import List

from app.models.actuator_command import ActuatorCommand
from app.models.unified_event import UnifiedEvent
from app.services.rules_repository import Rule


logger = logging.getLogger(__name__)


_RULE_PATTERN_WITH_UNIT = re.compile(
    r"""
    ^IF\s+
    (?P<sensor>[a-zA-Z0-9_]+)\s*
    (?P<op><=|>=|<|>|=)\s*
    (?P<value>\d+(?:\.\d+)?)      # numeric threshold
    \s+
    (?P<unit>.+?)                 # unit (lazy, up to 'THEN')
    \s+THEN\s+set\s+
    (?P<actuator>[a-zA-Z0-9_]+)\s+
    to\s+
    (?P<command>ON|OFF)
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

_RULE_PATTERN_NO_UNIT = re.compile(
    r"""
    ^IF\s+
    (?P<sensor>[a-zA-Z0-9_]+)\s*
    (?P<op><=|>=|<|>|=)\s*
    (?P<value>\d+(?:\.\d+)?)      # numeric threshold
    \s+THEN\s+set\s+
    (?P<actuator>[a-zA-Z0-9_]+)\s+
    to\s+
    (?P<command>ON|OFF)
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)


@dataclass(slots=True)
class ParsedRule:
    sensor_name: str
    operator: str
    threshold: float
    unit: str | None
    actuator_id: str
    command: str
    rule_id: str
    rule_name: str


class RuleEngine:
    """
    Parses rule conditions from the DSL and evaluates them against events.
    """

    def parse_condition(self, rule: Rule) -> ParsedRule | None:
        """
        Parse the DSL rule stored in rule.condition into a structured ParsedRule.
        Returns None if the rule cannot be parsed.
        """
        text = rule.condition.strip()

        match = _RULE_PATTERN_WITH_UNIT.match(text) or _RULE_PATTERN_NO_UNIT.match(text)
        if not match:
            logger.error("Failed to parse rule condition: %s (rule_id=%s)", text, rule.id)
            return None

        sensor = match.group("sensor")
        operator = match.group("op")
        value_str = match.group("value")
        unit = match.groupdict().get("unit")
        actuator = match.group("actuator")
        command = match.group("command").upper()

        try:
            threshold = float(value_str)
        except ValueError:
            logger.error(
                "Invalid numeric threshold in rule condition: %s (rule_id=%s)",
                text,
                rule.id,
            )
            return None

        return ParsedRule(
            sensor_name=sensor,
            operator=operator,
            threshold=threshold,
            unit=unit.strip() if unit else None,
            actuator_id=actuator,
            command=command,
            rule_id=rule.id,
            rule_name=rule.name,
        )

    def _compare(self, value: float, operator: str, threshold: float) -> bool:
        if operator == "<":
            return value < threshold
        if operator == "<=":
            return value <= threshold
        if operator == "=":
            return abs(value - threshold) < 0.001
        if operator == ">":
            return value > threshold
        if operator == ">=":
            return value >= threshold
        logger.error("Unsupported operator '%s' in rule engine.", operator)
        return False

    def evaluate_event(self, event: UnifiedEvent, rules: List[Rule]) -> List[ActuatorCommand]:
        """
        Evaluate the given event against all rules and return a list of
        actuator commands to be emitted.
        """
        commands: List[ActuatorCommand] = []

        for rule in rules:
            parsed = self.parse_condition(rule)
            if parsed is None:
                continue

            # Match the incoming event to the sensor referenced in the rule.
            # Use source_id for matching with new unified event schema
            if event.source_id != parsed.sensor_name:
                continue

            # Use metrics[0].value as the comparison value for all rule evaluations
            event_value = None
            if event.metrics and len(event.metrics) > 0:
                event_value = event.metrics[0].value

            if event_value is None:
                logger.warning(
                    "Event from source_id=%s has empty metrics, skipping rule evaluation",
                    event.source_id
                )
                continue

            if not self._compare(event_value, parsed.operator, parsed.threshold):
                continue

            logger.info(
                "Rule matched: rule_id=%s name=%s source_id=%s value=%s op=%s threshold=%s",
                parsed.rule_id,
                parsed.rule_name,
                event.source_id,
                event_value,
                parsed.operator,
                parsed.threshold,
            )

            commands.append(
                ActuatorCommand(
                    actuator_id=parsed.actuator_id,
                    command=parsed.command,  # type: ignore[arg-type]
                )
            )

        return commands

