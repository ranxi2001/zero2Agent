# Third-Party Attribution

The Agent Basic discussion of model API messages, context engineering, cache-aware context design, and controlled ablation experiments was conceptually informed by:

- Bojie Li, *AI Agents in Depth: Design Principles and Engineering Practice*, [`bojieli/ai-agent-book@e3883f8c`](https://github.com/bojieli/ai-agent-book/tree/e3883f8cec222c31e59c646be96641120863027e), Apache License 2.0, Copyright 2025 Bojie Li.

The corresponding zero2Agent prose, diagrams, examples, and `examples/agent-api-lab` implementation are independently written for this repository. No upstream source code, generated figures, or book text is included in this adaptation. Refer to the upstream repository for its full license and for separately licensed subprojects.

## DeepSeek Harness Module

The DeepSeek Harness module uses the following public projects as reference material. The article prose and diagrams are independently written; no upstream source code or book text is copied into this repository.

- [deepseek-ai/deepseek-harness@dsh-v0.1.0-rc.8](https://github.com/deepseek-ai/deepseek-harness/tree/dsh-v0.1.0-rc.8) — official architecture, service seams, and subsystem API documentation, MIT License.
- [shigma/Cordis](https://github.com/shigma/Cordis) — plugin kernel and lifecycle background, MIT License.
- [yanhua1010/dsh-harness-tutorial](https://github.com/yanhua1010/dsh-harness-tutorial) — Chinese demos and mini-harness teaching project, MIT License.
- [SheltonLiu-N/nano-cordis](https://github.com/SheltonLiu-N/nano-cordis) — runnable teaching implementation, MIT License.
- [Electricitysheep/dsh-handbook](https://github.com/Electricitysheep/dsh-handbook) and [alchaincyf/deepseek-harness-orange-book](https://github.com/alchaincyf/deepseek-harness-orange-book) — community handbooks and electronic books used for background comparison. These materials are licensed CC BY-NC-SA 4.0 where stated by their authors and describe earlier `0.1.0-rc.6`-era behavior; they are not the API source of truth for this module.
- [xueai.app interactive anatomy](https://xueai.app/slides/learn.html#dsh-1.html) and [Cordis architecture note](https://blog.antinomie.org) — online explanatory references; no local copy of their prose is published here.

The local research checkout and downloaded releases are kept under the Git-ignored `.codex-tmp/` directory and are not published as site content.

## Nowcoder Interview Recollections

The interview-question updates dated 2026-08-16 were independently summarized from public interview recollections published from 2026-08-12 through 2026-08-15 in Nowcoder's [interview feed](https://www.nowcoder.com/?type=818_1). Public tutorial pages retain only generalized technical questions and company, role, or interview-round attribution.

At the user's explicit request, `.claude/skills/scrape-nowcoder/nowcoder-agent-excellent-full/` also keeps a non-site maintenance archive of selected interview recollections. New entries preserve the complete recorded interview sequence, including technical follow-ups, the author's recorded answers and interviewer feedback, coding tasks, and questions asked back to the interviewer. Each entry links to its Nowcoder source; account names, schools, author locations, specific personal outcomes, comments, recommendations, browser profiles, and login data are excluded. The complete browser scrape remains in a Git-ignored working directory and is not part of the repository archive.
