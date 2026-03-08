const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * API client targeting the API Gateway.
 */
export async function apiGet(path) {
  const url = `${API_BASE_URL}${path}`;
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (err) {
    console.error("API request failed:", err);
    throw err;
  }
}

