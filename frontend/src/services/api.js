const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * Placeholder API client targeting the API Gateway.
 * Business logic and concrete endpoints will be added later.
 */
export async function apiGet(path) {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url);
  return response.json();
}

