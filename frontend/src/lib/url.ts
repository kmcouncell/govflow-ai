/** Join API origin and a path from configuration (both from env). */

export function joinApiUrl(apiBaseUrl: string, pathname: string): string {
  const base = apiBaseUrl.replace(/\/$/, "");
  const path = pathname.startsWith("/") ? pathname : `/${pathname}`;
  return `${base}${path}`;
}
