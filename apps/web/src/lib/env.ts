export function isMockMode(): boolean {
  return process.env.NEXT_PUBLIC_MOCK_MODE === 'true';
}

export function apiBaseUrl(): string {
  const v = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (v && v.length > 0) {
    return v;
  }
  return 'http://localhost:8000';
}
