import { z } from "zod";

const bytes = (value: unknown): number =>
  new TextEncoder().encode(JSON.stringify(value)).byteLength;
const digest = z.string().regex(/^[a-f0-9]{64}$/);
const uuid = z.uuid();
const iso = z.iso.datetime({ offset: true });

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
const error = z.strictObject({ code: z.string().max(64), message: z.string().max(256) });
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
  candidate_id: uuid.nullable(),
  publication_id: uuid.nullable(),
  error: error.nullable(),
});
export type JobV2 = z.infer<typeof jobV2>;

const historyEntry = z.strictObject({
  answer_id: uuid,
  source: sourceV2,
  text: z.string().max(1024),
  accepted_at: iso,
  unavailable: z.literal(false),
});
const journalEntry = z.strictObject({
  request_id: uuid,
  input_sha256: digest,
  job_id: uuid,
  terminal_code: z.string().max(64).nullable(),
  publication_id: uuid.nullable(),
});
export const sessionStateV2 = z.strictObject({
  version: z.literal("2"),
  revision: z.number().int().nonnegative(),
  selected_source: sourceV2.nullable(),
  selected_catalog_revision: z.literal("m3-catalog.v1").nullable(),
  history: z.array(historyEntry).max(12),
  accepted_answers: z.array(historyEntry).max(4),
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
  | { kind: "conflict"; code: "request_conflict" | "request_outcome_unavailable" }
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
    selected_source: SALES_SOURCE,
    selected_catalog_revision: "m3-catalog.v1",
    history: [],
    accepted_answers: [],
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
  sourceV2.parse(source);
  return parseSessionState({
    ...state,
    selected_source: source,
    active_job: null,
    generation: state.generation + 1,
    cancel_epoch: state.cancel_epoch + 1,
    revision: state.revision + 1,
  });
}

export function resetSession(state: SessionStateV2, now = new Date()): SessionStateV2 {
  const next = initialSessionState(now);
  return { ...next, generation: state.generation + 1, cancel_epoch: state.cancel_epoch + 1 };
}

export function beginJob(state: SessionStateV2, job: JobV2): SessionOutcome {
  jobV2.parse(job);
  const prior = state.request_journal.find((entry) => entry.request_id === job.request_id);
  if (prior) {
    return prior.input_sha256 === job.input_sha256
      ? { kind: "replay", entry: prior }
      : { kind: "conflict", code: "request_conflict" };
  }
  if (state.active_job !== null) return { kind: "busy", code: "request_conflict" };
  return { kind: "new", job };
}

export function storeJob(state: SessionStateV2, job: JobV2): SessionStateV2 {
  if (job.generation !== state.generation || job.cancel_epoch !== state.cancel_epoch) {
    throw new Error("stale_job");
  }
  return parseSessionState({ ...state, active_job: job, revision: state.revision + 1 });
}

export function cancelJob(state: SessionStateV2): SessionStateV2 {
  if (state.active_job === null) return state;
  return parseSessionState({
    ...state,
    active_job: { ...state.active_job, phase: "cancel_requested" },
    cancel_epoch: state.cancel_epoch + 1,
    revision: state.revision + 1,
  });
}

export function finishJob(
  state: SessionStateV2,
  jobId: string,
  generation: number,
  cancelEpoch: number,
  terminal: Pick<JobV2, "phase" | "error" | "publication_id">,
): SessionStateV2 {
  const active = state.active_job;
  if (
    active === null ||
    active.job_id !== jobId ||
    active.generation !== generation ||
    active.cancel_epoch !== cancelEpoch ||
    state.cancel_epoch !== cancelEpoch
  )
    throw new Error("stale_job");
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
        publication_id: terminal.publication_id,
      })
      .slice(-32),
    revision: state.revision + 1,
  });
}

export function publicSnapshot(state: SessionStateV2): SessionStateV2 {
  return parseSessionState(JSON.parse(JSON.stringify(state)));
}
