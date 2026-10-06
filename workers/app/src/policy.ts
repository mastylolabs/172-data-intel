export class SafeError extends Error {
  constructor(readonly code: "invalid_result" | "result_limit") {
    super(code);
  }
}
export function unicode(value: string): boolean {
  return Array.from(value).every((char) => {
    const point = char.codePointAt(0)!;
    return point < 0xd800 || point > 0xdfff;
  });
}
function keyOrder(left: string, right: string): number {
  const a = Array.from(left);
  const b = Array.from(right);
  for (let index = 0; index < Math.min(a.length, b.length); index++) {
    const difference = a[index].codePointAt(0)! - b[index].codePointAt(0)!;
    if (difference !== 0) return difference;
  }
  return a.length - b.length;
}
export function canonicalJson(value: unknown): string {
  if (Array.isArray(value)) return `[${Array.from(value, canonicalJson).join(",")}]`;
  if (value !== null && typeof value === "object" && Object.getPrototypeOf(value) === Object.prototype) {
    const record = value as Record<string, unknown>;
    return `{${Object.keys(record).sort(keyOrder).map((key) =>
      `${canonicalJson(key)}:${canonicalJson(record[key])}`).join(",")}}`;
  }
  if (value === null || typeof value === "boolean" ||
    (typeof value === "string" && unicode(value)) ||
    (typeof value === "number" && Number.isSafeInteger(value) && !Object.is(value, -0))) {
    return JSON.stringify(value);
  }
  throw new SafeError("invalid_result");
}
export function bound(value: unknown, maximum: number): void {
  if (new TextEncoder().encode(canonicalJson(value)).byteLength > maximum) {
    throw new SafeError("result_limit");
  }
}
export async function payloadSha256(value: unknown): Promise<string> {
  const hash = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(canonicalJson(value)));
  return Array.from(new Uint8Array(hash), (byte) => byte.toString(16).padStart(2, "0")).join("");
}
export function supportedClaims(
  overall: "pass" | "fail" | "needs_clarification",
  claims: readonly { claim_id: string; disposition: string }[],
  expected: readonly string[], deterministicPassed: boolean,
): boolean {
  const returned = claims.map((claim) => claim.claim_id);
  return deterministicPassed && overall === "pass" && expected.length > 0 &&
    new Set(expected).size === expected.length && returned.length === expected.length &&
    new Set(returned).size === returned.length && expected.every((id) => returned.includes(id)) &&
    claims.every((claim) => claim.disposition === "supported");
}
