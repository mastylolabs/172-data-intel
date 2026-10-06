import { describe, expect, it } from "vitest";
import meta from "./fixtures/metadata.json";
import receipt from "./fixtures/result.json";
import {
  agentRuntime,
  boundedJson,
  metadata,
  result,
  runtime,
  serviceError,
  sqlInput,
  validatedResult,
} from "../src/contracts";

describe("Python wire boundary", () => {
  it("accepts generated Python metadata and verifies its exact result hashes", async () => {
    expect(metadata.parse(meta)).toEqual(meta);
    expect(await validatedResult(receipt)).toEqual(receipt);
  });
  it.each([
    { ...receipt, version: "2" },
    { ...receipt, unknown: true },
    { ...receipt, row_count: 20 },
    { ...receipt, columns: ["total", "total"] },
    { ...receipt, truncated: true },
    { ...receipt, analytical_validated: true },
    { ...receipt, limits: { ...receipt.limits, max_rows: 21 } },
  ])("rejects malformed result shape", (value) => {
    expect(result.safeParse(value).success).toBe(false);
  });
  it.each(["sql_sha256", "result_sha256"])("rejects tampered %s", async (key) => {
    await expect(validatedResult({ ...receipt, [key]: "0".repeat(64) })).rejects.toThrow(
      "invalid_result",
    );
  });
  it.each(["oops", "9223372036854775808", "-9223372036854775809", "01"])(
    "refuses invalid integer %s safely",
    (value) => {
      expect(
        result.safeParse({ ...receipt, rows: [[{ type: "integer", value, exact: true }]] }).success,
      ).toBe(false);
    },
  );
  it("preserves all typed cells and refuses unsafe text/real encodings", () => {
    for (const cell of [
      { type: "integer", value: "9223372036854775807", exact: true },
      { type: "real", value: "1.0", exact: false },
      { type: "text", value: "é" },
      { type: "null", value: null },
    ]) {
      expect(result.parse({ ...receipt, rows: [[cell]] }).rows[0][0]).toEqual(cell);
    }
    for (const cell of [
      { type: "real", value: "Infinity", exact: false },
      { type: "text", value: "é".repeat(129) },
      { type: "text", value: "\ud800" },
    ]) {
      expect(result.safeParse({ ...receipt, rows: [[cell]] }).success).toBe(false);
    }
  });
  it("validates independent deployed provenance and permits truthful local nulls", () => {
    expect(runtime.safeParse({ ...meta.runtime, build_revision: null }).success).toBe(false);
    expect(
      agentRuntime.safeParse({
        runtime_mode: "deployed",
        build_revision: "a".repeat(40),
        worker_version_id: "deployment-object-id",
      }).success,
    ).toBe(false);
    expect(
      agentRuntime.parse({ runtime_mode: "local", build_revision: null, worker_version_id: null })
        .runtime_mode,
    ).toBe("local");
  });
  it("rejects source substitution, malformed metadata and raw provider errors", () => {
    expect(
      metadata.safeParse({ ...meta, source: { ...meta.source, source_id: "support" } }).success,
    ).toBe(false);
    expect(metadata.safeParse({ ...meta, fields: [] }).success).toBe(false);
    expect(serviceError.safeParse({ code: "private-token", provider_reason: "raw" }).success).toBe(
      false,
    );
  });
  it("bounds SQL by UTF-8 bytes and refuses coercion, extras and whitespace", () => {
    const input = {
      version: "1",
      request_id: receipt.job_id,
      question: "Total?",
      sql: "SELECT 1",
      max_rows: 20,
    };
    expect(sqlInput.parse(input)).toEqual(input);
    expect(sqlInput.parse({ ...input, question: "😀".repeat(2000) }).question).toHaveLength(4000);
    for (const patch of [
      { max_rows: "20" },
      { sql: "é".repeat(4001) },
      { sql: " " },
      { question: " " },
      { question: "😀".repeat(2001) },
      { extra: true },
    ]) {
      expect(sqlInput.safeParse({ ...input, ...patch }).success).toBe(false);
    }
  });
});
describe("bounded JSON stream", () => {
  it("reads split multibyte UTF-8 without corrupting content", async () => {
    const bytes = new TextEncoder().encode('{"value":"é"}');
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(bytes.slice(0, 11));
        controller.enqueue(bytes.slice(11));
        controller.close();
      },
    });
    expect(await boundedJson(new Response(stream))).toEqual({ value: "é" });
  });
  it("accepts the exact byte limit and refuses one extra byte", async () => {
    expect(await boundedJson(new Response('"ok"'), 4)).toBe("ok");
    await expect(boundedJson(new Response('"ok"'), 3)).rejects.toThrow("result_limit");
  });
  it("preserves size failure when cancellation itself throws", async () => {
    const stream = new ReadableStream({
      start(c) {
        c.enqueue(new Uint8Array(10));
      },
      cancel() {
        throw new Error("ffi-cancel");
      },
    });
    await expect(boundedJson(new Response(stream), 1)).rejects.toThrow("result_limit");
  });
  it("refuses missing bodies, invalid JSON, malformed UTF-8 and FFI read errors", async () => {
    const broken = new ReadableStream({
      start(c) {
        c.error(new Error("ffi-read"));
      },
    });
    for (const response of [
      new Response(),
      new Response("{"),
      new Response(new Uint8Array([255])),
      new Response(broken),
    ]) {
      await expect(boundedJson(response)).rejects.toThrow();
    }
  });
});
