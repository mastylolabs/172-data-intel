import { z } from "zod";

const canonical = (value: unknown): string => {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value !== null && typeof value === "object") {
    const record = value as Record<string, unknown>;
    return `{${Object.keys(record).sort().map((key) => `${JSON.stringify(key)}:${canonical(record[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
};
const bytes = (value: unknown): number => new TextEncoder().encode(canonical(value)).byteLength;
const unicode = (value: string): boolean =>
  Array.from(value).every((char) => {
    const code = char.codePointAt(0) ?? 0;
    return code < 0xd800 || code > 0xdfff;
  });
const boundedText = (maximum: number) =>
  z.string().refine((value) => bytes(value) <= maximum && unicode(value));
const sourceKey = (value: SourceV2): string =>
  `${value.version}:${value.source_id}:${value.snapshot_sha256}:${value.meaning_revision}`;
const digest = z.string().regex(/^[a-f0-9]{64}$/);
const uuid = z.uuid();
const iso = z.iso.datetime({ offset: false }).refine((value) => value.endsWith("Z"));

export const sourceV2 = z.discriminatedUnion("source_id", [
  z.strictObject({
    version: z.literal("1"),
    source_id: z.literal("sales"),
    snapshot_sha256: z.literal(
      "a55c2b2a8a9378830e8e8dd13e7df1dcf9de6d87ce39f13f97aa4c48ed7ca84f",
    ),
    meaning_revision: z.literal("sales-demo.v1"),
  }),
  z.strictObject({
    version: z.literal("1"),
    source_id: z.literal("support"),
    snapshot_sha256: z.literal(
      "c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536",
    ),
    meaning_revision: z.literal("support-demo.v1"),
  }),
]);
export type SourceV2 = z.infer<typeof sourceV2>;

export const jobPhase = z.enum([
  "queued",
  "profiling",
  "semantic",
  "planning",
  "executing",
  "candidate",
  "validating",
  "cancel_requested",
  "completed",
  "awaiting_clarification",
  "failed",
  "interrupted",
  "cancelled",
  "budget_exhausted",
]);
const error = z.strictObject({
  code: z.enum(["stale_job", "publication_conflict", "state_limit", "model_unavailable", "validation_failed"]),
  stage: z.enum(["planning", "candidate", "validation", "publication", "transport"]),
});
const clarification = z.strictObject({ question: boundedText(512), created_at: iso });
export const jobV2 = z.strictObject({
  job_id: uuid,
  request_id: uuid,
  input_sha256: digest,
  source: sourceV2,
  generation: z.number().int().nonnegative(),
  cancel_epoch: z.number().int().nonnegative(),
  phase: jobPhase,
  started_at: iso,
  deadline_at: iso,
  active_run_id: uuid.nullable(),
  error: error.nullable(),
  clarification: clarification.nullable(),
});
export type JobV2 = z.infer<typeof jobV2>;

const journalEntry = z.strictObject({
  request_id: uuid,
  input_sha256: digest,
  job_id: uuid,
  terminal_code: z.string().max(64).nullable(),
  publication_id: uuid.nullable(),
}).refine((value) => bytes(value) <= 256);
export const sessionStateV2 = z.strictObject({
  version: z.literal("2"),
  revision: z.number().int().nonnegative(),
  selected_source: sourceV2.nullable(),
  selected_catalog_revision: z.literal("m4-catalog.v1").nullable(),
  history: z.array(z.never()).max(12),
  accepted_answers: z.array(z.never()).max(4),
  accepted_memory: z.array(z.never()).max(4),
  dropped_history: z.literal(0),
  active_job: jobV2.nullable(),
  expires_at: iso,
  generation: z.number().int().nonnegative(),
  cancel_epoch: z.number().int().nonnegative(),
  request_journal: z.array(journalEntry).max(32),
});
export type SessionStateV2 = z.infer<typeof sessionStateV2>;
export type SessionOutcome =
  | { kind: "new"; job: JobV2 }
  | { kind: "replay"; entry: z.infer<typeof journalEntry> }
  | { kind: "conflict"; code: "request_conflict" | "request_outcome_unavailable" | "source_mismatch" }
  | { kind: "busy"; code: "request_conflict" };

export const SALES_SOURCE: SourceV2 = {
  version: "1",
  source_id: "sales",
  snapshot_sha256: "a55c2b2a8a9378830e8e8dd13e7df1dcf9de6d87ce39f13f97aa4c48ed7ca84f",
  meaning_revision: "sales-demo.v1",
};
export const SUPPORT_SOURCE: SourceV2 = {
  version: "1",
  source_id: "support",
  snapshot_sha256: "c6365aa74909b4deb09bb00114f7b489dcc8c9c152c57855db95fd6304e1e536",
  meaning_revision: "support-demo.v1",
};

export function initialSessionState(now = new Date()): SessionStateV2 {
  return {
    version: "2",
    revision: 0,
    selected_source: null,
    selected_catalog_revision: null,
    history: [],
    accepted_answers: [],
    accepted_memory: [],
    dropped_history: 0,
    active_job: null,
    expires_at: new Date(now.getTime() + 7 * 86_400_000).toISOString(),
    generation: 0,
    cancel_epoch: 0,
    request_journal: [],
  };
}

export function parseSessionState(value: unknown): SessionStateV2 {
  const state = sessionStateV2.parse(value);
  if (bytes(state) > 65_536) throw new Error("state_limit");
  return state;
}

export function selectSource(state: SessionStateV2, source: SourceV2): SessionStateV2 {
  const parsedSource = sourceV2.parse(JSON.parse(JSON.stringify(sourceV2.parse(source))));
  const nextEpoch = state.cancel_epoch + 1;
  const fencedJob = state.active_job
    ? { ...state.active_job, phase: "cancelled" as const, cancel_epoch: nextEpoch }
    : null;
  const cancellation = state.active_job
    ? {
        request_id: state.active_job.request_id,
        input_sha256: state.active_job.input_sha256,
        job_id: state.active_job.job_id,
        terminal_code: "cancelled",
        publication_id: null,
      }
    : null;
  return parseSessionState({
    ...state,
    selected_source: parsedSource,
    selected_catalog_revision: "m4-catalog.v1",
    active_job: fencedJob,
    request_journal: cancellation
      ? state.request_journal.concat(cancellation).slice(-32)
      : state.request_journal,
    generation: state.generation + 1,
    cancel_epoch: nextEpoch,
    revision: state.revision + 1,
  });
}

export function resetSession(state: SessionStateV2, now = new Date()): SessionStateV2 {
  const next = initialSessionState(now);
  return {
    ...next,
    revision: state.revision + 1,
    generation: state.generation + 1,
    cancel_epoch: state.cancel_epoch + 1,
  };
}

export function beginJob(state: SessionStateV2, job: JobV2): SessionOutcome {
  const parsedJob = jobV2.parse(JSON.parse(JSON.stringify(jobV2.parse(job))));
  const prior = state.request_journal.find((entry) => entry.request_id === parsedJob.request_id);
  if (prior) {
    return prior.input_sha256 === parsedJob.input_sha256
      ? { kind: "replay", entry: prior }
      : { kind: "conflict", code: "request_conflict" };
  }
  const terminal = new Set([
    "completed",
    "awaiting_clarification",
    "failed",
    "interrupted",
    "cancelled",
    "budget_exhausted",
  ]);
  if (state.selected_source === null || sourceKey(parsedJob.source) !== sourceKey(state.selected_source)) {
    return { kind: "conflict", code: "source_mismatch" };
  }
  if (state.active_job !== null && !terminal.has(state.active_job.phase)) {
    return { kind: "busy", code: "request_conflict" };
  }
  return { kind: "new", job: parsedJob };
}

export function storeJob(state: SessionStateV2, job: JobV2): SessionStateV2 {
  const parsedJob = jobV2.parse(JSON.parse(JSON.stringify(jobV2.parse(job))));
  if (state.selected_source === null || sourceKey(parsedJob.source) !== sourceKey(state.selected_source)) {
    throw new Error("source_mismatch");
  }
  if (parsedJob.generation !== state.generation || parsedJob.cancel_epoch !== state.cancel_epoch) {
    throw new Error("stale_job");
  }
  return parseSessionState({ ...state, active_job: parsedJob, revision: state.revision + 1 });
}

export function cancelJob(state: SessionStateV2): SessionStateV2 {
  if (state.active_job === null) return state;
  const nextEpoch = state.cancel_epoch + 1;
  return parseSessionState({
    ...state,
    active_job: { ...state.active_job, phase: "cancel_requested", cancel_epoch: nextEpoch },
    cancel_epoch: nextEpoch,
    revision: state.revision + 1,
  });
}

export function finishJob(
  state: SessionStateV2,
  jobId: string,
  generation: number,
  cancelEpoch: number,
  terminal: Pick<JobV2, "phase" | "error">,
): SessionStateV2 {
  const active = state.active_job;
  if (
    active === null ||
    active.job_id !== jobId ||
    active.generation !== state.generation ||
    active.generation !== generation ||
    active.cancel_epoch !== cancelEpoch ||
    state.cancel_epoch !== cancelEpoch ||
    ["cancelled", "completed", "failed", "interrupted", "budget_exhausted"].includes(active.phase)
  )
    throw new Error("stale_job");
  const terminalPhases = ["completed", "awaiting_clarification", "failed", "interrupted", "cancelled", "budget_exhausted"];
  if (!terminalPhases.includes(terminal.phase) || (active.phase === "cancel_requested" && terminal.phase !== "cancelled")) {
    throw new Error("stale_job");
  }
  const finished = { ...active, ...terminal };
  return parseSessionState({
    ...state,
    active_job: finished,
    request_journal: state.request_journal
      .concat({
        request_id: active.request_id,
        input_sha256: active.input_sha256,
        job_id: active.job_id,
        terminal_code: terminal.error?.code ?? null,
        publication_id: null,
      })
      .slice(-32),
    revision: state.revision + 1,
  });
}

type PublicJobV2 = Pick<
  JobV2,
  "job_id" | "request_id" | "source" | "phase" | "active_run_id" | "error" | "clarification" | "started_at" | "deadline_at"
> & { candidate_visible: false };
export type PublicSessionSnapshot = Omit<
  SessionStateV2,
  "request_journal" | "generation" | "cancel_epoch" | "active_job"
> & { active_job: PublicJobV2 | null };
export function publicSnapshot(state: SessionStateV2): PublicSessionSnapshot {
  const parsed = parseSessionState(JSON.parse(JSON.stringify(state)));
  const { request_journal: _journal, generation: _generation, cancel_epoch: _epoch, active_job, ...publicState } = parsed;
  return {
    ...publicState,
    active_job: active_job
      ? {
          job_id: active_job.job_id,
          request_id: active_job.request_id,
          source: active_job.source,
          phase: active_job.phase,
          active_run_id: active_job.active_run_id,
          error: active_job.error,
          clarification: active_job.clarification,
          started_at: active_job.started_at,
          deadline_at: active_job.deadline_at,
          candidate_visible: false,
        }
      : null,
  };
}
