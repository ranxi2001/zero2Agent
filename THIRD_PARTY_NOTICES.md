# Third-Party Attribution

The Agent Basic discussion of model API messages, context engineering, cache-aware context design, and controlled ablation experiments was conceptually informed by:

- Bojie Li, *AI Agents in Depth: Design Principles and Engineering Practice*, [`bojieli/ai-agent-book@e3883f8c`](https://github.com/bojieli/ai-agent-book/tree/e3883f8cec222c31e59c646be96641120863027e), Apache License 2.0, Copyright 2025 Bojie Li.

The corresponding zero2Agent prose, diagrams, examples, and `examples/agent-api-lab` implementation are independently written for this repository. No upstream source code, generated figures, or book text is included in this adaptation. Refer to the upstream repository for its full license and for separately licensed subprojects.

## DeepSeek Harness Module

The DeepSeek Harness module uses the following public projects as reference material. The article prose and diagrams are independently written; no upstream source code or book text is copied into this repository.

- [deepseek-ai/deepseek-harness@dsh-v0.1.0-rc.8](https://github.com/deepseek-ai/deepseek-harness/tree/dsh-v0.1.0-rc.8) — official architecture, service seams, and subsystem API documentation, MIT License.
- [libukai/awesome-deepseek-harness](https://github.com/libukai/awesome-deepseek-harness) — community resource index used to discover the tutorials, books, whitepaper, interactive anatomy, and teaching implementation reviewed for this module.
- [shigma/Cordis](https://github.com/shigma/Cordis) and [cordiverse/paper](https://github.com/cordiverse/paper) — plugin kernel, lifecycle implementation, and the spatiotemporal-composability design paper; Cordis is MIT licensed and the paper repository states its own terms.
- [yanhua1010/dsh-harness-tutorial](https://github.com/yanhua1010/dsh-harness-tutorial) — Chinese demos and mini-harness teaching project, MIT License.
- [SheltonLiu-N/nano-cordis](https://github.com/SheltonLiu-N/nano-cordis) — runnable teaching implementation, MIT License.
- [Electricitysheep/dsh-handbook](https://github.com/Electricitysheep/dsh-handbook) and [alchaincyf/deepseek-harness-orange-book](https://github.com/alchaincyf/deepseek-harness-orange-book) — community handbooks and electronic books used for background comparison. These materials are licensed CC BY-NC-SA 4.0 where stated by their authors and describe earlier `0.1.0-rc.6`-era behavior; they are not the API source of truth for this module.
- [xueai.app interactive anatomy](https://xueai.app/slides/learn.html#dsh-1.html) and [Cordis architecture note](https://blog.antinomie.org) — online explanatory references; no local copy of their prose is published here.
- [DeepSeek Harness Agent OS](https://blog.anionex.me/archives/deepseek-harness-agent-os) — user-provided reading reference for the functional-programming and Agent OS perspective; no local copy of its prose is published here.

The local research checkout and downloaded releases are kept under the Git-ignored `.codex-tmp/` directory and are not published as site content.

## Pi Coding Agent Module

The Pi module uses the following public sources as references. Its Chinese prose, examples, comparisons, and learning structure are independently adapted and rewritten for zero2Agent; no upstream source code or textbook prose is copied verbatim into this repository.

- [badlogic/pi-mono@a470b121bf683b4c2b9fc0b3a7c807de7e0cfe9c](https://github.com/badlogic/pi-mono/tree/a470b121bf683b4c2b9fc0b3a7c807de7e0cfe9c) — official implementation and documentation baseline, verified on 2026-08-24. Refer to the upstream repository for package-specific licenses and notices.
- [Pi official documentation](https://pi.dev/docs/latest/) — current Skills, Extensions, Packages, Sessions, security, SDK, RPC, and runtime behavior.
- [Chunhao Zhang (hahhforest), *Build Your Own Pi / 动手学 Pi*](https://github.com/hahhforest/pi-textbook) — teaching reference for checkpoints, focused tests, failure experiments, the observable Agent Loop, session recovery, context rebuilding, trust gates, and evaluation. The textbook prose and original media are licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The user-provided [Chasen Liao-hosted mirror](https://chasen-liao.github.io/pi-textbook-page/learn/prologue/) is used as the reading URL. zero2Agent changes the organization, examples, explanations, and scope rather than reproducing the textbook text.
- [nicobailon/pi-mcp-adapter@6c08147f7a3c6eba670fa8fb73e1fe68a7ab471f](https://github.com/nicobailon/pi-mcp-adapter/tree/6c08147f7a3c6eba670fa8fb73e1fe68a7ab471f) — third-party MIT-licensed reference for proxy versus direct MCP tools, lazy lifecycle, configuration precedence, approvals, credentials, and output guards. It is not treated as a Pi built-in security boundary.
- [Pi Chinese documentation](https://pi-doc.com) — auxiliary Chinese-language navigation only; official latest documentation and source remain authoritative.
- [qualisero/awesome-pi-agent](https://github.com/qualisero/awesome-pi-agent) — historical community discovery only. The repository was archived on 2026-06-03 and states that its list is outdated, so it is not used as a current compatibility or security source.

## Nowcoder Interview Recollections

The interview-question updates dated 2026-08-16 were independently summarized from public interview recollections published from 2026-08-12 through 2026-08-15 in Nowcoder's [interview feed](https://www.nowcoder.com/?type=818_1). Public tutorial pages retain only generalized technical questions and company, role, or interview-round attribution.

At the user's explicit request, `.claude/skills/scrape-nowcoder/nowcoder-agent-excellent-full/` also keeps a non-site maintenance archive of selected interview recollections. New entries preserve the complete recorded interview sequence, including technical follow-ups, the author's recorded answers and interviewer feedback, coding tasks, and questions asked back to the interviewer. Each entry links to its Nowcoder source; account names, schools, author locations, specific personal outcomes, comments, recommendations, browser profiles, and login data are excluded. The complete browser scrape remains in a Git-ignored working directory and is not part of the repository archive.

## Agent Infra Interview Answers

The Agent Infra and AIOps interview answers added on 2026-08-28 were independently written and checked against these primary references:

- [Kubernetes Custom Resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/) and [Kubernetes API Concepts](https://kubernetes.io/docs/reference/using-api/api-concepts/) — declarative resource fit, List/Watch behavior, `resourceVersion`, and control-plane boundaries.
- [OpenTelemetry Context Propagation](https://opentelemetry.io/docs/concepts/context-propagation/) — correlation of traces, logs, and metrics across service boundaries.
- [Google SRE Incident Management Guide](https://sre.google/resources/practices-and-processes/incident-management-guide/) — symptom-based actionable alerting, incident automation, mitigation, and post-incident learning.

No upstream prose or diagrams are reproduced. Product- and version-specific behavior remains subject to the linked projects' current documentation.

## Weekly Interview Answer References (2026-08-28)

The answers derived from the 2026-08-22 through 2026-08-28 interview audit were independently written and checked against these primary references:

- [Playwright Locators](https://playwright.dev/docs/locators) and [Trace Viewer](https://playwright.dev/docs/trace-viewer) — resilient page interaction, failure evidence, and replay-oriented debugging.
- [Model Context Protocol Authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization), [Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools), and [Cancellation](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/cancellation) — authorization boundaries, Tool contracts, and optional cancellation semantics.
- [ECMA-376 Office Open XML](https://ecma-international.org/publications-and-standards/standards/ecma-376/), [CommonMark](https://spec.commonmark.org/), and [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/specs/semconv/) — document validation and trace/error evidence.
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/), [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/), and [Service Accounts](https://kubernetes.io/docs/concepts/security/service-accounts/) — secret handling and execution-boundary controls.
- [Qdrant Filtering](https://qdrant.tech/documentation/concepts/filtering/) and [PostgreSQL Row Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) — retrieval-time document and Chunk authorization.
- [ONNX Runtime Web](https://onnxruntime.ai/docs/tutorials/web/), [W3C WebGPU](https://www.w3.org/TR/webgpu/), [pypdf text extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html), and [W3C Markup Validation](https://validator.w3.org/docs/) — browser inference and PDF/HTML artifact verification.
- [NIST AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf) — generative-AI risk-management framing for content-safety workflows; the repository does not present it as jurisdiction-specific legal advice.
- [LeRobot Dataset v3](https://huggingface.co/docs/lerobot/lerobot-dataset-v3), [TRL SFT Trainer](https://huggingface.co/docs/trl/sft_trainer), [XGBoost model tutorial](https://xgboost.readthedocs.io/en/latest/tutorials/model.html), [ONNX IR](https://onnx.ai/onnx/repo-docs/IR.html), and [Ultralytics export documentation](https://docs.ultralytics.com/modes/export/) — data annotation, SFT sample contracts, model structure, interchange format, and runtime export boundaries.
- [KubeEdge EdgeHub](https://kubeedge.io/docs/architecture/edge/edgehub/) and [verl AgentLoop source at commit 8df88be](https://github.com/verl-project/verl/blob/8df88be746801b6d87c42e15f9a5a0ec1d5eeeae/verl/experimental/agent_loop/agent_loop.py) with its [AgentLoop documentation](https://verl.readthedocs.io/en/latest/advance/agent_loop.html) — edge/cloud coordination and the explicitly versioned alpha AgentLoop API.

No upstream prose, code, diagrams, or benchmark claims are reproduced. Framework-specific behavior remains tied to the linked version or current official documentation; architecture recommendations are identified as engineering judgment rather than product guarantees.
