# ADR-0001: Reasoning and deterministic execution

- Status: **Proposed — awaiting approval**
- Original proposal date: 2026-10-04
- Scope: MVP roles and enforcement; additional deployment separation is future work.
- Traces: BR-03–BR-06, AC-04/09; DEC-02/04

## Context

The initial architecture §§2–8/13 separates reasoning from execution, but assigns
schema/statistics duties to a named Data Profiler Agent even though most are
deterministic. Deploying four autonomous services would add state, failure and
testing work without evidence that independent deployment improves the MVP.

## Proposed decision

Preserve data/agent/durable execution separation. Use a deterministic Orchestrator,
a deterministic profiling service with optional interpretation of ambiguous
findings, conditional semantic reasoning, an Analyst and a separate Validator
invocation. Use Workers AI with Llama 3.3 for MVP model calls, with separate Analyst
and Validator contexts. Runtime compatibility and model behavior remain unverified
until tested. Treat reasoning roles as public Python application modules/capabilities;
they do not imply one deployment or Durable Object per role. Infrastructure owns
generated-SQL validation/execution, parsing, statistics, coverage, arithmetic and retries.
Agents propose/interpret; authorized infrastructure enforces every plan.

## Alternatives and consequences

Always invoking four LLMs adds cost and correlated failure; collapsing Analyst and
Validator removes an independent challenge. Keep separate analytical review while
avoiding unnecessary model calls. Reconsider deployment separation only after
measured workload, ownership or isolation needs justify it.

## Evidence and validation

See [architecture findings](../architecture-review.md) and original §§2/5/13/16.
Validate a known schema without any profiling/semantic model call; ambiguous
business meaning triggers clarification, not invented definitions. Verify that
numeric calculation/retry paths run without LLM arithmetic or decisions.
No implementation evidence exists yet.
