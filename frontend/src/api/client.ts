export async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${endpoint.startsWith("http") ? endpoint : `${import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"}${endpoint}`}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}
