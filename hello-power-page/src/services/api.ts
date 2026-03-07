import type { ODataResponse } from "../types";

const IS_DEV = import.meta.env.DEV;
const API_BASE = "/_api";

let cachedToken: string | null = null;

async function getAntiForgeryToken(): Promise<string> {
  if (IS_DEV) return "dev-token";
  if (cachedToken) return cachedToken;
  const response = await fetch("/_api/antiforgery/token");
  if (!response.ok) throw new Error("Failed to fetch anti-forgery token");
  const data = await response.json();
  cachedToken = data.token;
  return data.token;
}

export async function apiFetch<T = unknown>(
  url: string,
  options: RequestInit = {},
): Promise<T> {
  if (IS_DEV) return devMockFetch<T>(url);
  const method = (options.method || "GET").toUpperCase();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...Object.fromEntries(
      Object.entries(options.headers || {}).map(([k, v]) => [k, String(v)]),
    ),
  };
  if (method !== "GET") {
    const token = await getAntiForgeryToken();
    headers.__RequestVerificationToken = token;
  }
  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API ${response.status}: ${text}`);
  }
  if (response.status === 204) return null as T;
  return response.json();
}

function buildUrl(entitySet: string, params?: Record<string, string>): string {
  const base = `${API_BASE}/${entitySet}`;
  if (!params) return base;
  const qs = new URLSearchParams(params).toString();
  return `${base}?${qs}`;
}

export async function getRecords<T>(
  entitySet: string,
  params?: Record<string, string>,
): Promise<ODataResponse<T>> {
  return apiFetch<ODataResponse<T>>(buildUrl(entitySet, params));
}

// ── Dev mock ──
import { MOCK_CASES } from "./mockData";

async function devMockFetch<T>(url: string): Promise<T> {
  await new Promise((r) => setTimeout(r, 300));
  if (url.includes("/incidents")) return { value: MOCK_CASES } as T;
  throw new Error(`[Dev] No mock for: ${url}`);
}
