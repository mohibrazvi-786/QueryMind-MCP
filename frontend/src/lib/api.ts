export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"

async function request(path: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  })
  if (!res.ok) {
    throw new Error(`API ${init?.method || "GET"} ${path} failed: ${res.status}`)
  }
  return res
}

export async function getJSON<T>(path: string): Promise<T> {
  const res = await request(path)
  return (await res.json()) as T
}

export async function postJSON<T = unknown>(
  path: string,
  body: unknown,
): Promise<T> {
  const res = await request(path, {
    method: "POST",
    body: JSON.stringify(body),
  })
  return (await res.json()) as T
}
