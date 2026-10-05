172X Data Intelligence
Agentic Data Analysis Architecture
Status: Initial Architecture
Project: 172X Ecosystem / Mastylo Labs LLC
Philosophy: Evidence first. Pragmatic architecture. Agents reason; deterministic infrastructure executes.
1. Vision
172X Data Intelligence is an open-source, agentic data-analysis platform that allows users to connect data sources and ask questions about their data in natural language.
The system is designed to work with both structured and unstructured information without loading large datasets directly into an LLM context.
A user should be able to connect a data source and ask questions such as:
- Which customers increased billable usage the most this month?
- Which geographic regions experienced the largest increase in cancellations?
- What were the major customer complaints in the support Slack channel during the last 24 hours?
- Which customers increased usage while revenue declined?
- What unusual patterns in this dataset deserve investigation?
The platform determines how to retrieve, process, analyze, validate, and explain the answer.
2. Core Architectural Principle
The fundamental separation is:
Agents reason and make decisions.
Deterministic infrastructure performs deterministic work.
An LLM should not perform work that a database, parser, query engine, workflow engine, or deterministic algorithm can perform more reliably and cheaply.
For example:
- File-format detection → deterministic code
- SQL aggregation → database/query engine
- Retry after network timeout → workflow infrastructure
- Determining what an ambiguous field means → agent
- Choosing SQL versus semantic retrieval → agent
- Deciding whether evidence supports a conclusion → agent
This prevents unnecessary agent proliferation and keeps the architecture understandable.
3. High-Level Architecture
                         ┌─────────────────────┐
                         │        User         │
                         │     172X UI/API     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Orchestrator     │
                         │ Durable Control     │
                         │       Plane         │
                         └──────────┬──────────┘
                                    │
                   ┌────────────────┼────────────────┐
                   │                │                │
                   ▼                ▼                ▼
             Data Profiler    Semantic Agent    Analyst Agent
                 Agent          when needed          │
                   │                                │
                   │                         AnalysisPlan
                   │                                │
                   └──────────────┬─────────────────┘
                                  ▼
                         ┌─────────────────────┐
                         │ Execution / Tools   │
                         │ SQL / Search / RAG  │
                         │ Partition / Compute │
                         └──────────┬──────────┘
                                    │
                                    ▼
                              Results/Evidence
                                    │
                                    ▼
                              Analyst Agent
                                    │
                             Candidate Answer
                                    │
                                    ▼
                            ┌───────────────┐
                            │   Validator   │
                            │     Agent     │
                            └───────┬───────┘
                                    │
                         PASS ──────┼────── FAIL
                           │        │          │
                           ▼        │          ▼
                         User       │       Analyst
                                    │       Replan
                                    │
                           repeated failure
                                    │
                                    ▼
                              Human Review
4. The Orchestrator
The Orchestrator is the control plane of the system.
It should not necessarily be an LLM agent.
Its responsibilities include:
- workflow state
- agent routing
- durable execution
- checkpoints
- retry policies
- budgets
- tool invocation
- human-in-the-loop escalation
- execution history
- provenance propagation
- failure handling
The Orchestrator determines which capabilities are required for a particular request.
The architecture is therefore a graph, not a rigid pipeline.
For example:
Known Slack source
    ↓
Profiler
    ↓
Semantic model already trusted?
    ↓ YES
Analyst
versus:
Unknown database
    ↓
Profiler
    ↓
Semantics ambiguous?
    ↓ YES
Semantic Agent
    ↓
Analyst
5. Agent 1: Data Profiler
Question it answers
What structure does this data have?
The Data Profiler understands the physical characteristics of a data source.
It can work with sources such as:
- CSV
- JSON
- Parquet
- PostgreSQL
- object storage
- analytical databases
- Slack exports
- email datasets
- future connectors
Whenever possible, deterministic tooling should perform format detection, schema extraction, sampling, and statistics.
The agent reasons primarily about ambiguous findings.
Example responsibilities
- detect schema
- identify field types
- calculate row/document counts
- identify candidate keys
- calculate null rates
- identify distributions
- detect malformed records
- detect duplicates
- identify anomalies
- characterize structured versus unstructured fields
- identify available retrieval capabilities
Important rule
The DataProfile never contains the bulk dataset.
It contains knowledge about the data and references to the data.
Example:
DataProfile

source:
    type: slack
    dataset: customer-support

scope:
    channel: #support
    time_range: last_24_hours

record_count:
    18,421

fields:
    timestamp
    author
    channel
    thread_id
    message_body

unstructured_fields:
    message_body

capabilities:
    filtering
    full_text_search
    vector_search

data_reference:
    <internal source reference>
This contract may be kilobytes even when the underlying dataset is terabytes.
Principle
Contracts move knowledge about data.
References point to data.
Tools operate on data.
6. Agent 2: Semantic Agent
Question it answers
What does this data mean?
The Semantic Agent is invoked only when semantic understanding is missing, incomplete, or ambiguous.
It should not necessarily run for every request.
For a well-known Slack connector, the semantics may already be established.
For an unfamiliar database containing:
acct_no
evt_ts
qty
amt
st_cd
semantic reasoning becomes valuable.
The Semantic Agent might infer:
acct_no → customer account identifier
evt_ts  → event timestamp
qty     → billable usage quantity
amt     → invoice amount
st_cd   → account status
If confidence is insufficient, the system asks a human instead of inventing meaning.
Semantic model
The output may include:
- domain
- entities
- measures
- dimensions
- events
- relationships
- business definitions
- ambiguous concepts
- confidence
- optional sensitivity classification
Example:
Domain:
    Billing

Entities:
    Customer
    Account
    Invoice

Measures:
    Usage
    Revenue
    Amount Paid

Dimensions:
    Geography
    Plan
    Billing Period

Events:
    Invoice Issued
    Payment Received
    Subscription Cancelled
7. Classification
Classification is not a separate pipeline stage.
It is optional semantic metadata.
Classification should exist only where it changes system behavior.
Useful examples include:
domain: financial-markets
subtype: market-microstructure
sensitivity: restricted
or:
domain: healthcare
sensitivity: sensitive-personal-data
These classifications could activate different:
- policies
- validators
- tools
- access restrictions
- retention behavior
- analytical assumptions
Principle
Classification is valuable when classification changes behavior.
The system should not attempt to build an enormous universal taxonomy.
8. Agent 3: Analyst
The Analyst is the primary interactive intelligence of the platform.
Question it answers
How should I answer the user's analytical question?
The Analyst receives:
User Question
+
DataProfile
+
Semantic Model, when available
+
Data Source Capabilities
Example:
Which customers increased billable usage the most this month?

The Analyst constructs an AnalysisPlan.
9. AnalysisPlan
The plan should be a strongly typed machine-readable contract.
It may also be rendered as Markdown for humans.
Example:
AnalysisPlan

1. Filter billing records to current month.
2. Aggregate usage by customer.
3. Retrieve previous-month usage.
4. Calculate month-over-month change.
5. Rank customers.
6. Return top 10.
7. Preserve source provenance.
For Slack:
AnalysisPlan

1. Filter #support messages to last 24 hours.
2. Restrict to customer-related conversations.
3. Partition remaining messages.
4. Analyze each partition.
5. Aggregate recurring themes.
6. Retrieve supporting source messages.
7. Synthesize findings.
8. Validate claims.
10. Retrieval Strategy
The Analyst also acts as the retrieval planner.
It chooses the appropriate strategy based on the question and data.
Possible strategies include:
Structured query
Question
    ↓
SQL
    ↓
Database
    ↓
Results
Best for structured analytical questions.
Semantic retrieval
Useful for meaning-oriented questions over unstructured content.
Hybrid retrieval
Structured filtering
        ↓
Reduced dataset
        ↓
Semantic/vector retrieval
        ↓
Relevant evidence
        ↓
LLM analysis
Partitioned analysis
For questions requiring broad corpus coverage:
Filter
  ↓
Partition
  ↓
Analyze partitions
  ↓
Aggregate
  ↓
Synthesize
This prevents the system from blindly placing large datasets into an LLM context.
11. RAG
RAG means:
Retrieval-Augmented Generation
Retrieval by itself is not RAG.
For example:
Semantic search
      ↓
100 candidates
      ↓
Filter / rerank
      ↓
10 candidates
This is retrieval and reranking.
It becomes RAG when retrieved evidence is supplied to a generative model:
Retrieve evidence
      ↓
Select/rerank evidence
      ↓
Place evidence in LLM context
      ↓
LLM generates grounded answer
Therefore:
Retrieval + grounded generation = RAG
Vector search is only one possible retrieval mechanism.
Evidence can be retrieved through:
- SQL
- vector search
- full-text search
- APIs
- graph traversal
- hybrid retrieval
- other tools
12. Data Plane vs Agent Plane
The architecture separates two worlds.
Data Plane
Contains potentially enormous datasets.
Examples:
- databases
- Parquet
- object storage
- Slack messages
- email
- analytical warehouses
- future lakehouse storage
Agent Plane
Contains compact reasoning artifacts:
- schemas
- metadata
- statistics
- semantic models
- samples
- plans
- retrieved evidence
- execution results
Example:
100 GB dataset
      ↓
profiling/query engine
      ↓
50 KB profile
      ↓
LLM reasoning
Principle
Push computation to the data.
Do not pull the data into the model.
13. Execution Layer
The Analyst plans execution.
The Orchestrator executes the plan through deterministic infrastructure.
No separate Execution Agent is required.
Responsibilities may include:
- SQL execution
- filtering
- aggregation
- partitioning
- vector search
- full-text search
- sampling
- batch processing
- LLM invocation
- checkpointing
Responsibility split
Analyst: decides what should happen.
Orchestrator/Workflow: makes it happen reliably.
Tools: perform the actual operations.
14. Durable Execution
Long-running analysis must be checkpointed.
Suppose an analysis contains 100 partitions:
1–72  PASS
73    FAIL
74–100 pending
The system should retry partition 73.
It should not restart the entire analysis.
Work units should therefore be designed to be idempotent whenever possible.
15. Two Types of Retry
Technical retry
Example:
Network timeout
The workflow engine retries the same operation, potentially with backoff.
No LLM reasoning is required.
Reasoning retry
Example:
Query references nonexistent column.
Partition strategy exceeds resource limits.
Retrieved evidence is insufficient.
The failure is returned to the Analyst.
The Analyst revises the plan.
Principle
Infrastructure retries failures.
Agents reconsider decisions.
Humans resolve ambiguity or repeated failure.
16. Agent 4: Validator
The Validator provides independent analytical verification.
It operates after execution and after the Analyst has produced a candidate answer.
The Validator receives:
Original Question
AnalysisPlan
Execution Results
Candidate Answer
Provenance
It evaluates:
- Does the answer address the question?
- Are calculations correct?
- Are claims supported by evidence?
- Were records double-counted?
- Were time windows interpreted correctly?
- Was important information lost during aggregation?
- Does provenance support each important claim?
- Did the Analyst infer something unsupported?
PASS
Validator
    ↓
PASS
    ↓
User
FAIL
The Validator returns a structured failure:
FAIL

reason:
    Incorrect aggregation

evidence:
    Customer IDs duplicated across partitions

required_action:
    Recalculate using distinct customer IDs
The Orchestrator routes this back appropriately.
Validator FAIL
      ↓
Analyst
      ↓
Replan
      ↓
Execute
      ↓
Validate again
After a bounded number of unsuccessful correction loops:
Human-in-the-loop
17. Execution Correctness vs Analytical Correctness
These are intentionally separate.
Execution correctness
Did the operation execute correctly?
Handled primarily by infrastructure.
Analytical correctness
Does the conclusion actually follow from the evidence?
Handled by the Validator Agent.
The Validator should not inspect every tiny infrastructure operation. That would unnecessarily increase latency and cost.
18. Provenance
Provenance is a first-class property.
Every important conclusion should be traceable backward:
Final Claim
    ↓
Intermediate Finding
    ↓
Query / Calculation
    ↓
Retrieved Evidence
    ↓
Source Records
    ↓
Original Data Source
This enables:
- validation
- explainability
- debugging
- reproducibility
- user trust
An answer should not merely say:
Customer cancellations increased.

It should be possible to inspect why the system believes that statement.
19. Human-in-the-Loop
Humans enter when judgment cannot be resolved reliably.
Example:
Semantic Agent:
"I believe `amt` means invoice amount,
but confidence is only 52%."

Human:
"`amt` is net invoice amount in USD.
Negative values are credits."
That definition becomes part of the semantic model.
Human intervention is also triggered after bounded retry or validation loops.
Example:
Attempt 1 → fail
Attempt 2 → fail
Attempt 3 requested
        ↓
STOP
        ↓
Human decision
20. Scalability
The architecture should behave conceptually the same whether the source contains:
20 MB
20 GB
2 TB
The execution infrastructure changes, not the agent architecture.
For an MVP, a lightweight analytical engine may be sufficient.
At larger scale, implementations could use technologies such as:
- PostgreSQL
- DuckDB
- Parquet
- object storage
- ClickHouse
- Trino
- Iceberg
- distributed query engines
The agents remain insulated through stable tool and data contracts.
21. Example: Slack Analysis
User asks:
Analyze the #support channel from the last 24 hours and tell me the major customer problems.

Possible execution:
User
 ↓
Orchestrator
 ↓
Profiler
 ↓
Known Slack semantics?
 ↓ YES
Skip Semantic Agent
 ↓
Analyst
 ↓
AnalysisPlan
 ↓
Filter by channel/time
 ↓
Partition / semantic retrieval
 ↓
Analyze evidence
 ↓
Aggregate themes
 ↓
Analyst synthesizes candidate answer
 ↓
Validator
 ↓
PASS
 ↓
User
If semantics are unknown:
Profiler
 ↓
Semantic Agent
 ↓
Analyst
22. Final Component Model
172X Data Intelligence initially contains:
Control Plane
Orchestrator
Deterministic durable workflow and routing.
Intelligent Agents
1. Data Profiler Agent
What structure does this data have?

2. Semantic Agent
What does this data mean?

Invoked conditionally.
3. Analyst Agent
How should I answer this question?

Plans retrieval, analysis, and execution.
4. Validator Agent
Does this answer actually follow from the evidence?

Infrastructure
Not agents:
- data connectors
- data stores
- query engines
- vector retrieval
- full-text search
- workflow engine
- LLM providers
- observability
- provenance store
- execution tools
23. Design Principles
1. Do not create an agent when deterministic code will do.
2. Contracts contain metadata and references, not bulk datasets.
3. Push computation to the data.
4. Use semantic reasoning only where meaning is ambiguous.
5. Classification is metadata, not a mandatory stage.
6. The Analyst chooses the retrieval strategy.
7. RAG is retrieval plus grounded generation, not retrieval alone.
8. Durable infrastructure handles mechanical retries.
9. Agents handle reasoning failures and replanning.
10. Validation is independent from analysis.
11. Preserve provenance from final claim to original source.
12. Escalate unresolved ambiguity to humans.
13. Prefer four meaningful agents over twenty decorative ones.
14. Optimize cost only subject to correctness.
24. Core Identity
172X Data Intelligence should not be described simply as:
“Chat with your data.”

Its stronger identity is:
An evidence-first agentic data intelligence system that understands heterogeneous data, plans its own analytical strategy, executes against data at its source, validates conclusions independently, and preserves provenance from answer to evidence.

The architecture is intentionally small.
Its power comes from the separation of responsibilities:
Agents reason.
Infrastructure executes.
Evidence grounds.
Validators challenge.
Humans govern.

