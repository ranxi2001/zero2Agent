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

## Weekly Interview Answer References (2026-09-02)

The answers derived from the 2026-08-29 through 2026-09-02 interview audit were independently written and checked against these primary references:

- [Kubernetes CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) and [SWE-bench](https://github.com/swe-bench/SWE-bench/blob/main/README.md) - scheduled-run concurrency and missed-trigger semantics, plus reproducible repository-level repair evaluation.
- [MCP Transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) and [DSPy MIPROv2](https://dspy.ai/api/optimizers/MIPROv2/) - current stdio/Streamable HTTP boundaries and evaluation-driven prompt candidate optimization.
- [ECMA-376 Office Open XML](https://ecma-international.org/publications-and-standards/standards/ecma-376/), [Cube semantic-layer introduction](https://docs.cube.dev/docs/introduction), and [Cube joins](https://docs.cube.dev/docs/data-modeling/joins) - packaged Word relationships and governed metrics, entities, joins, and access rules for enterprise question answering.
- [Linux `/proc/<pid>/status`](https://man7.org/linux/man-pages/man5/proc_pid_status.5.html), [`/proc/<pid>/stat`](https://man7.org/linux/man-pages/man5/proc_pid_stat.5.html), [`pidfd_open`](https://man7.org/linux/man-pages/man2/pidfd_open.2.html), and [cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html) - process observation fields, start time, stable process handles, resource boundaries, and controlled process-group actions.

No upstream prose, code, diagrams, datasets, or benchmark results are reproduced. Version-specific behavior remains tied to the linked documentation; the surrounding architecture and safety recommendations are independent engineering analysis.

## Weekly Interview Answer References (2026-09-08)

The answers derived from the 2026-09-02 through 2026-09-08 interview audit were independently written and checked against these primary references:

- [LLaMA-Factory](https://github.com/hiyouga/LlamaFactory) and [Hugging Face TRL](https://huggingface.co/docs/trl/index) - current training-tool scope, trainer surfaces, and framework-selection boundaries.
- [DAPO](https://arxiv.org/abs/2503.14476) - the paper's no-KL training setting, asymmetric clipping, dynamic sampling, token-level policy-gradient, and overlong-reward design.
- [GitHub Spec Kit](https://github.com/github/spec-kit) - the constitution, specification, planning, and task workflow used as one concrete Spec-Driven Development implementation.
- [EnCodec](https://github.com/facebookresearch/encodec) and [SpeechTokenizer](https://arxiv.org/abs/2308.16692) - neural audio codec, residual vector quantization, and hierarchical semantic/acoustic Token design.

No upstream prose, code, diagrams, datasets, or benchmark claims are reproduced. Framework behavior remains tied to the linked versions and current documentation; the architecture, evaluation, and safety recommendations are independent engineering analysis.

## Weekly Interview Answer References (2026-09-13)

The answers added from the 2026-09-07 through 2026-09-13 interview audit were independently written and checked against these primary references:

- [Qwen2-VL official repository](https://github.com/QwenLM/Qwen2-VL) — visual tokenization and dynamic-resolution implementation boundaries.
- [DeepSpeed ZeRO documentation](https://www.deepspeed.ai/tutorials/zero/) — optimizer, gradient, and parameter sharding stages.
- [CUDA Runtime API stream synchronization](https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__STREAM.html) — stream and event synchronization semantics.
- [XGBoost model documentation](https://xgboost.readthedocs.io/en/latest/tutorials/model.html) — tree-model terminology used in the comparison answer.

No upstream prose, code, diagrams, datasets, or benchmark results are reproduced. Version-specific behavior remains tied to the linked documentation; the surrounding explanations and engineering recommendations are independent analysis.

## Weekly Interview Answer References (2026-09-21)

The answers added from the 2026-09-15 through 2026-09-21 interview audit were independently written and checked against these primary references:

- [OpenAI Computer Use Guide](https://developers.openai.com/api/docs/guides/tools-computer-use) — screenshot/action loops, environment boundaries, and human-confirmation safety points.
- [Spring AI Reference](https://docs.spring.io/spring-ai/reference/) and [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents) — current framework abstractions and agent/tool orchestration surfaces.
- [NVIDIA Nsight Compute Documentation](https://docs.nvidia.com/nsight-compute/NsightCompute/index.html) and [Nsight Systems User Guide](https://docs.nvidia.com/nsight-systems/UserGuide/index.html) — kernel-level versus system-wide GPU performance analysis.
- [OpenAI HumanEval](https://github.com/openai/human-eval), [Google Research MBPP](https://github.com/google-research/google-research/tree/master/mbpp), and [APPS](https://github.com/hendrycks/apps) — benchmark task formats and functional-evaluation boundaries.
- [Relaxed On-Policy Distillation](https://arxiv.org/abs/2603.11137) and [Trust Region On-Policy Distillation](https://arxiv.org/abs/2606.01249) — OPD instability, teacher/student distribution mismatch, and stabilization mechanisms.

No upstream prose, code, datasets, diagrams, or benchmark results are reproduced. Framework behavior remains tied to the linked documentation; architecture and evaluation recommendations are independent engineering analysis.

## Weekly Interview Answer References (2026-09-29)

The answers added from the 2026-09-22 through 2026-09-29 interview audit were independently written and checked against these primary references:

- [Model Context Protocol 2026-07-28 Transports](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports) — current stdio and Streamable HTTP bindings, framing, metadata, cancellation, and backward-compatibility boundaries.
- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) and [Deep Agents Overview](https://docs.langchain.com/oss/python/deepagents/overview) — conditional routing, graph state updates, harness capabilities, context management, delegation, permissions, and runtime boundaries.
- [Spring AI Reference](https://docs.spring.io/spring-ai/reference/) — Java model and vector-store integration abstractions used to contrast framework and direct-adapter approaches.
- [Muon official repository](https://github.com/KellerJordan/Muon) — Muon parameter scope, auxiliary Adam usage, orthogonalized updates, and tuning guidance.
- [Reinforcement Learning from Verifier Feedback](https://openreview.net/pdf?id=5WtovCb1ZE) — verifier-derived reward training and the RLVF terminology boundary.
- [OpenAI CLIP repository and model card](https://github.com/openai/CLIP) — contrastive image-text training, released encoders, zero-shot use, and documented limitations.
- [LLaMA](https://ai.meta.com/research/publications/llama-open-and-efficient-foundation-language-models/), [Llama 2](https://ai.meta.com/research/publications/llama-2-open-foundation-and-fine-tuned-chat-models/), and [Llama 3](https://ai.meta.com/research/publications/the-llama-3-herd-of-models) — architecture, training-data, post-training, tokenizer, context, tool-use, and release evolution across the three generations.

No upstream prose, code, datasets, diagrams, or benchmark results are reproduced. Version-specific behavior remains tied to the linked documentation; the surrounding explanations, comparisons, and engineering recommendations are independent analysis.

## Interview Answer References (2026-10-07)

The incremental answers from the September 23 through October 7 interview review were independently written using these primary references:

- [ToT 论文](https://arxiv.org/abs/2305.10601)
- [MCP 架构文档](https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture)
- [GQA 论文](https://arxiv.org/abs/2305.13245)
- [Transformer 原论文](https://arxiv.org/html/1706.03762v7)
- [LoRA 原论文](https://arxiv.org/html/2106.09685v2)
- [InstructGPT 论文](https://arxiv.org/abs/2203.02155)
- [LangChain](https://docs.langchain.com/oss/python/langchain/overview)
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [TrOCR](https://arxiv.org/abs/2109.10282)
- [DPO](https://arxiv.org/abs/2305.18290)
- [Dr. GRPO](https://arxiv.org/abs/2503.20783)


No upstream prose, code, figures, or datasets are reproduced. Protocol and implementation facts are attributed at the relevant answer; architecture, evaluation, and operational recommendations are independent engineering analysis. Public interview links document question provenance only.


## Weekly Interview Answer References (2026-10-13)

The answers updated from the October 7–13 interview review were independently written and checked against these primary references:

- [DAgger 论文](https://arxiv.org/abs/1011.0686)
- [BERT 论文](https://arxiv.org/abs/1810.04805)
- [Self-Consistency 论文](https://arxiv.org/abs/2203.11171)
- [Diffusion Policy 项目页](https://diffusion-policy.cs.columbia.edu/)
- [Megatron 并行策略文档](https://docs.nvidia.com/megatron-core/developer-guide/latest/user-guide/parallelism-guide.html)
- [SciPy softmax 文档](https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.softmax.html)
- [OpenVLA 官方实现](https://github.com/openvla/openvla)
- [RISC-V Vector 规范](https://github.com/riscvarchive/riscv-v-spec/blob/master/v-spec.adoc)
- [ACT 项目页](https://tonyzhaozh.github.io/aloha/)
- [JSON-RPC 2.0 规范](https://www.jsonrpc.org/specification)
- [XGBoost 模型文档](https://xgboost.readthedocs.io/en/latest/tutorials/model.html)

No upstream prose, code, diagrams, or datasets are reproduced. Interview links establish question provenance; the linked specifications, papers, and official implementations establish answer facts. Architecture, testing, deployment, and evaluation recommendations are independent engineering analysis.

## RSI and Cloud Bot Practice References (2026-10-18)

The two application-practice articles use the following primary sources:

- [LLM4MIP](https://github.com/LLM4MIP/llm4mip.github.io) (MIT): project scope, primal/dual Skills, historical case records, and comparison limitations. Selected objective values and mechanism facts are attributed in the article; no solver runs or independent result reproduction are claimed.
- [Recursive self-improvement of AI research agents](https://arxiv.org/abs/2609.26457): the distinction between optimizing a task artifact and iteratively modifying the research agent itself.
- [Grok Bot documentation](https://docs.x.ai/grok-bot/overview), [Meta Muse announcement](https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/), and [ChatGPT dot help](https://help.openai.com/en/articles/20001530-getting-started-with-your-dot): documented execution environments, continuity, controls, and product-specific boundaries.
- [Doubao Work introduction](https://www.feishu.cn/content/article/7677519271848610746), [Doubao work-partner help](https://aily.feishu.cn/hc/1u7kleqg_3d5z9ttt?_lang=zh), [Coze cloud-computer documentation](https://docs.coze.cn/cozespace_device), and [Manus Cloud Computer](https://www.manus.im/features/cloud-computer): documented task execution, collaboration, and environment lifecycle.

Explanations, diagrams, task templates, and proposed evaluation procedures are independently written. They are not upstream implementations or reports of product testing. Product availability remains tied to current official documentation and account configuration.

## Interview Answer References (2026-10-22)

The October 13–22 question-bank update independently explains mechanisms and engineering tradeoffs using these primary references:

- [Scaling Laws 原论文](https://arxiv.org/abs/2001.08361)
- [GECToR 论文](https://arxiv.org/abs/2005.12592)
- [Chinchilla 论文](https://arxiv.org/abs/2203.15556)
- [DPO 论文](https://arxiv.org/abs/2305.18290)
- [LangChain 概览](https://docs.langchain.com/oss/python/langchain/overview)
- [PyTorch Conv2d 文档](https://docs.pytorch.org/docs/2.14/generated/torch.nn.Conv2d.html)
- [PyTorch 梯度累积示例](https://docs.pytorch.org/docs/2.14/notes/amp_examples.html#gradient-accumulation)
- [Ragas API](https://docs.ragas.io/en/stable/references/evaluate/)
- [Faiss 索引说明](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes)
- [Transformers 文本生成文档](https://huggingface.co/docs/transformers/llm_tutorial)
- [LLVM 向量化指南](https://llvm.org/docs/Vectorizers.html)
- [2026-07-28 规范](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports)
- [Redis 向量检索文档](https://redis.io/docs/latest/develop/ai/search-and-query/query/vector-search/)
- [Spinning Up 强化学习基础](https://spinningup.openai.com/en/latest/spinningup/rl_intro.html)
- [Thinking Machines 的实现](https://thinkingmachines.ai/blog/on-policy-distillation/)
- [Elastic 文档](https://www.elastic.co/docs/solutions/search/hybrid-search)
- [TensorFlow 多任务推荐示例](https://www.tensorflow.org/recommenders/examples/multitask)

Interview links in the articles establish question provenance. These references establish specific answer facts; deployment, evaluation, and testing recommendations are independent engineering analysis. No upstream article, source code, figure, or dataset is reproduced.
