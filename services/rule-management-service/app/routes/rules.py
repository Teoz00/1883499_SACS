from fastapi import APIRouter, status

router = APIRouter(prefix="/rules", tags=["rules"])


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Create rule (placeholder)")
async def create_rule() -> dict:
    """
    Placeholder endpoint for creating a new rule.
    """
    return {"detail": "create rule placeholder"}


@router.get("/", summary="List rules (placeholder)")
async def list_rules() -> dict:
    """
    Placeholder endpoint for listing rules.
    """
    return {"detail": "list rules placeholder"}


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete rule (placeholder)")
async def delete_rule(rule_id: str) -> None:
    """
    Placeholder endpoint for deleting a rule.
    """
    return None

