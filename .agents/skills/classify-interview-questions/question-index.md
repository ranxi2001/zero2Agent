# 面试题索引

> 自动维护，每次分发面试题后更新。用于快速判断新题是否已有、避免重复扫描 md 文件。
> 最后更新：2026-09-13（Luna API 扫描 2026-09-07 至 2026-09-13 牛客面经 202/202 篇；累计 693 题。传统八股 262 题）
> 排序规则：正文与本索引在现有最小主题组内按 `question-frequency.json` 的频次降序排列；同频按 `firstSeenOrder` 排列。

## 统计

| 维度 | 题数 |
|------|------|
| 01-architecture-design | 47 |
| 02-tool-management | 38 |
| 03-fault-tolerance | 38 |
| 04-memory-context | 64 |
| 05-eval-and-vision | 49 |
| 06-multi-agent-collab | 35 |
| 07-engineering-pitfalls | 69 |
| 08-prompt-engineering | 30 |
| 09-rag-retrieval | 73 |
| 10-training-and-data | 101 |
| 11-ai-code-testing | 19 |
| 12-business-ai-engineering | 27 |
| 13-project-deep-dive | 25 |
| 15-agent-concepts | 18 |
| 16-agent-infra | 28 |
| 17-ai-infra | 32 |
| **总计** | **693** |

## 01-architecture-design（47题）

1. 你用 ReAct 还是 Plan-and-Execute？为什么？ — 腾讯终面 【淘天二面追问：CoT vs ReAct 核心区别】【蚂蚁AI应用开发二面同题：ReAct 核心原理与复杂任务提升逻辑】【字节二面追问：Planner↔Executor 通信协议与重规划模式】【字节二面同题：ReAct vs Plan-and-Execute 理解与优劣对比】【数据智能查询平台面试同题：ReAct vs Plan-Execute 区别与场景】【小红书 Agent 岗一面追问：双模式与多轮状态机实现】【字节火山引擎 Managed Agent 一面追问：Reasoning + Action 循环】【[OPPO IT 开发一面](https://www.nowcoder.com/discuss/923561467092160512)】【[去哪儿旅行AI面试+笔试](https://www.nowcoder.com/discuss/926507047238078464)追问：ReAct和Plan-and-Execute两种AI agent运行框架的核心差异？】【[深圳tuitti视界之外实习一面](https://www.nowcoder.com/feed/main/detail/9b1329caf4b64389a0ab666585bda045)追问：你这里支持 ReAct 循环，但又由 Planner 将任务拆分成带依赖关系和验收条件的 DAG，这是不是就不是经典 ReAct 了？】【[阿里边缘bu 秋招一面 （已过）](https://www.nowcoder.com/feed/main/detail/bdebbb6088b6405e9eb2bd2c345acb6e)追问：在这个场景中，直接采用 ReAct + Tool 是否也能满足需求？】
2. Tree of Thoughts (ToT) 在线上系统里能用吗？成本不高？ — 腾讯终面
3. 了解过 Agent 的设计范式吗？ — 字节一面 【淘宝闪购一面同题：Agent 有哪些模式】【视频面经同题：Agent常见工作模式（ReAct/Plan-Execute等）】【[深圳tuitti视界之外实习一面](https://www.nowcoder.com/feed/main/detail/9b1329caf4b64389a0ab666585bda045)追问：你的方案更接近哪一种 Agent 范式？】
4. Agent 的架构设计？从系统角度来拆分 — 阿里一面【[月之暗面（Moonshot）- Agent 应用开发岗](https://www.nowcoder.com/discuss/926274239747952640)追问：Agent 项目的架构如何设计？解决了什么问题？】【[阿里边缘bu 秋招一面 （已过）](https://www.nowcoder.com/feed/main/detail/bdebbb6088b6405e9eb2bd2c345acb6e)追问：为什么把系统设计成三级 Agent 架构？】
5. Agent 在学术上由哪些部分组成？ — 字节一面【[OPPO IT 开发一面](https://www.nowcoder.com/discuss/923561467092160512)】
6. 如果让你设计一个 Agent 的规划器，怎么避免路径震荡？ — 腾讯二面【[字节跳动 - AI Agent 开发岗（工程方向）](https://www.nowcoder.com/discuss/926273296180547584)追问：路径震荡（反复失败）的原因是什么？如何引入失败记忆？】
7. 如果模型不擅长遵守流程，怎么放进强约束工作流？ — 腾讯二面【[阿里国际 Agent 开发三面](https://www.nowcoder.com/feed/main/detail/747f07e71f4448bebdce6ada5de800cd)】
8. 什么时候该做 Agent？和 Workflow 的边界在哪？ — 30题 【科大讯飞一面追问：workflow和ReAct的区别与使用时机】【数据智能查询平台面试同题：整体是Workflow还是Agent自由调用】【小红书 Rednote AI Native 一面追问：大模型与工作流如何权衡、固定流程为何仍用 Agent】【广报 Agent 开发追问：没有长期记忆或不完全自主是否仍算 Agent】【曹操出行实习追问：脚本硬编码与 LangGraph Agent 的选型边界】【阿里 Agent Infra 一面题库同题】【[虾皮Agent一面](https://www.nowcoder.com/feed/main/detail/409dc8793a7b450eb51ee32c2b923d49)追问：Agent 是人工触发任务吗？整体工作流程是否固定？】
9. 生产级 Agent 的执行循环包含哪些阶段？ — 30题 【快手AI应用开发一面追问：Agent Runtime 完整管线设计（Auth→Planner→Executor→Verifier→Trace）】【阿里 Agent Infra 一面题库追问：Agent Loop】【[字节中国交易与广告 AI 应用开发一面](https://www.nowcoder.com/feed/main/detail/b34f6902e8544fe2953696ed52e49dba)】【[蚂蚁 Agent 开发一面](https://www.nowcoder.com/feed/main/detail/39451cad5d2245b491d16778f2a9ca01)】
10. 设计一个 AI Agent 爬取短视频平台内容 — 字节实习一面
11. 现在的 Agent 架构和之前有什么本质不同？渐进式披露？ — 30题【[上海某量化开发 一面](https://www.nowcoder.com/feed/main/detail/87319d167f494d28a361ffd4a0215e06)追问：老架构有什么问题，新架构如何解决？】
12. 为什么很多团队做到最后是混合架构？ — 30题
13. Agent 系统里，模型和系统代码的职责边界怎么划？ — 30题
14. 如果面试官说“Agent 本质上就是套壳调用工具”，你怎么反驳？ — 30题
15. 什么样的任务适合先全局规划再执行，什么适合边走边决策？ — 30题
16. Skill、MCP、Rule 三者有什么区别？ — 蚂蚁一面 【快手AI应用开发一面追问：Tool/Skill/Agent 三层抽象的本质区别】
17. Agent 的任务规划是怎么做的？规划由模型还是规则？ — 快手一面【[阿里国际 Agent 开发三面](https://www.nowcoder.com/feed/main/detail/747f07e71f4448bebdce6ada5de800cd)】
18. 微服务怎么接入一个 Agent 系统？ — 蚂蚁一面
19. 如何保证规划 Agent plan 的结果正确？ — AI工程师面试
20. SSE 怎么实现 Human-in-the-Loop？ — AI工程师面试
21. LangChain 和 LangGraph 有什么区别？分别适合什么场景？ — 淘宝闪购一面 【遥望科技追问：新版LangChain底层为什么用LangGraph】【曹操出行/阿里 Agent 开发追问：复杂状态图中的选型依据】【[0827-字节大模型应用开发(一面)-秋招](https://www.nowcoder.com/discuss/926086211272196096)追问：对于 LangChain 和 LangGraph 这些框架了解吗，能说说两者的区别吗？】【[快手 - Agent 开发岗（应用落地 + AI 工具）](https://www.nowcoder.com/discuss/926274020192841728)追问：LangGraph 和 LangChain 有什么区别？图状态机适用于哪些场景？】【[第三次去哪儿旅行一面，AI面试问的是前端吗？](https://www.nowcoder.com/feed/main/detail/2ed12b3fa1d4491f8bb029f99cf9de73)追问：LangChain和LangGraph有什么区别？为什么现在项目优先使用LangGraph？】【[pdd agent二面](https://www.nowcoder.com/feed/main/detail/f5e7351df8364147ac8da085b99d9d18)追问：LangChain与LangGraph核心区别？】
22. 模型和 Agent 的区别到底是什么？ — 字节实习一面 【视频面经同题：你怎么理解Agent？它和普通LLM应用最大的区别】【[MiniMax - 大模型算法岗（后训练 / SFT / RL 方向，独角兽）](https://www.nowcoder.com/discuss/925527528259743744)追问：介绍一下大模型和 Agent 的区别和关系？】【[MiniMax - 大模型算法岗（后训练 / SFT / RL）](https://www.nowcoder.com/discuss/926272883872075776)追问：大模型与 Agent 的区别联系？】【[百度 - Agent 研发岗（架构方向）](https://www.nowcoder.com/discuss/926273622006665216)追问：在“AI 原生应用”中，Agent 的角色是什么？】
23. Agent 的 Self-Reflection 机制是什么？它怎么识别输出中的逻辑错误？ — 蚂蚁AI应用开发二面 【小红书 Agent 开发一面追问：Planner、Executor、Critic 的边界及独立 Critic】【[去哪儿 AI 全栈 AI 面](https://www.nowcoder.com/feed/main/detail/9cf516b3c2404100baeac52564e40709)】
24. 场景题：设计一个日志分析 Agent，怎么设计架构和工具？ — 腾讯AI应用开发实习一面【[百度 Agent 一面](https://www.nowcoder.com/feed/main/detail/53542e2dcfd44b1d84b0ae55b4fc1b35)】
25. 在“推理-行动”循环中，如何设计来纠正逻辑塌缩或无效工具调用？ — 淘天一面
26. 设计一个智能导购助手 Agent，描述其感知、规划、记忆和执行四大模块在分布式架构下的协同逻辑 — 淘天一面
27. 如果设计一个科研辅助 Agent，整体流程应该怎么设计？ — bilibili AI研发实习一面
28. 如何保障自然语言任务描述能精准转化为稳定、可靠的执行路径？ — 蚂蚁AI应用开发二面
29. 多角色智能客服场景（B/C/D 端），用 RAG 还是 Skill？怎么设计？ — 美团Keeta一面
30. Skill 和 Workflow 的区别是什么？什么场景该用 Skill 而不是 Workflow？ — 快手AI应用开发一面【[快手 AI 全栈一面](https://www.nowcoder.com/feed/main/detail/a30242712e8d456c839ff4223470f491)】
31. DAG 与含循环图在 Agent 编排中的区别和适用场景 — 猎豹移动Agent全栈开发
32. 基于强化学习的 Agent 与传统基于 Prompt 的 Agent 有何区别？各自的适用场景？ — Agent开发八股合集（南京大学）
33. AI 系统该做单域工具还是跨团队通用平台？怎么选？ — 数据智能查询平台面试（新增）【[英迈软件一面](https://www.nowcoder.com/feed/main/detail/355e6818b7e7418ba6f2c88c6bc50351)】【[阿里国际 Agent 开发三面](https://www.nowcoder.com/feed/main/detail/747f07e71f4448bebdce6ada5de800cd)】【[互联网金融 Agent 开发三面](https://www.nowcoder.com/feed/main/detail/88c55ee65af04ac98c218b9d17c47a71)】【[阿里千问平台开发复活赛一面](https://www.nowcoder.com/feed/main/detail/141447389dab4e8e9ca6db742a514f39)】
34. Agent 的 Middleware（中间件）是什么？在执行流中扮演什么角色？ — 字节跳动Agent开发实习生一面
35. Coding Agent 的完整链路是怎么运转的？从用户输入到代码产出的全流程 — 字节跳动Agent二面（Coding Agent）【百度大模型研发二面追问：Claude Code 用户交互全流程】【字节火山引擎 Managed Agent 一面追问：输入到页面展示的数据流】
36. 只有模型 API 和 VS Code，如何从零搭建一套可用的 Agent 应用？ — 百度大模型研发二面（新增）【[月之暗面（Moonshot）- Agent 应用开发岗](https://www.nowcoder.com/discuss/926274239747952640)追问：从零开始设计一个 Agent 应用时，整体规划如何制定？】
37. 用拓扑排序（规则式）管理任务依赖 vs 让大模型推理决策执行顺序，各有什么问题？ — 广州某小厂Agent后端开发二面（新增）
38. Agent 如何判断已经收集了足够的信息，最终给出输出结论？ — 字节跳动多模态算法一面【字节火山引擎 Managed Agent 一面追问：Loop 继续与结束条件】【阿里 Agent Infra 一面题库同题：停止条件】【[平安健康保险 AI 应用开发一面](https://www.nowcoder.com/feed/main/detail/6c11a75a8bd44628943deff3e42ae15c)追问：Agent 偷懒、过早结束或省略必要步骤】【[未知公司 Agent 二面](https://www.nowcoder.com/feed/main/detail/16675d793c0c42e8a6b46d42fb561561)追问：任务结束与会话终止策略】【[快手 AI 全栈一面](https://www.nowcoder.com/feed/main/detail/a30242712e8d456c839ff4223470f491)】
39. Agent 的 thinking 阶段怎么决定是调用工具还是直接回复？ — 腾讯AI应用开发实习生一面（新增）【字节火山引擎 Managed Agent 一面同题】
40. 设计一个内部的多源文档问答 AI，架构设计是什么？ — 百度AI智能体开发一面（新增）【[百度 Agent 一面](https://www.nowcoder.com/feed/main/detail/53542e2dcfd44b1d84b0ae55b4fc1b35)】【[OPPO IT 开发一面](https://www.nowcoder.com/discuss/923561467092160512)】
41. ReAct 在工程实现中，消息和状态协议应该怎么设计？ — 字节跳动AI Agent秋招一面（新增）【[OPPO IT 开发一面](https://www.nowcoder.com/discuss/923561467092160512)】
42. Agent 如何持续推进 Goal，并避免行为漂移和目标漂移？ — [腾讯 WXG 微信读书一面](https://www.nowcoder.com/feed/main/detail/3ffc762437274543b6a8f5e2ea6fb535)（2026-08-24）【[虾皮一面](https://www.nowcoder.com/feed/main/detail/e133c2610bde4adc812bba66c62e1641)】
43. Agent 组件拆解为什么适合责任链模式？与状态机、DAG 的边界是什么？ — 北京四维图新面经（新增）【阿里 Agent Infra 一面题库追问：为什么 Agent 本质上是状态机】
44. 设计一个预订机票的 Agent，如何处理澄清、支付确认和失败补偿？ — 百度 Agent算法岗二面（新增）
45. 在 AI/Agent 辅助编码时代，为什么 DDD 和清晰的领域边界反而更重要？ — [地图 Agent 二面](https://www.nowcoder.com/feed/main/detail/0208597586e744c884bdc571dc441fad)（2026-08-24）
46. AI Coding Agent 的 Solo 模式和 Plan 模式应该如何设计？ — [字节 Trae 二面](https://www.nowcoder.com/discuss/924821959647440896)（新增）

47. 什么时候需要自研或改造方案，而不是直接采用开源实现？ — [腾讯AI全栈一面](https://www.nowcoder.com/feed/main/detail/5f08a2b54559471aac95ea8009d38403)


## 02-tool-management（38题）

1. 工具描述写得再好，模型也瞎传参数怎么办？ — 腾讯终面 【蚂蚁AI应用开发二面追问：参数幻觉与语法错误的自动化修正】【科大讯飞一面追问：后端ORM接口作为tools如何防止工具调用偏移】【[去哪儿 AI 全栈 AI 面](https://www.nowcoder.com/feed/main/detail/9cf516b3c2404100baeac52564e40709)】
2. 工具库有上百个工具，怎么让模型快速选对？ — 腾讯终面 【淘天一面追问：100+工具召回偏差与分层路由】【百度大模型研发二面追问：Agent 如何选择合适工具】【[深信服Agent开发实习生一面二面，长时间被吊着，最终被横向掉了](https://www.nowcoder.com/feed/main/detail/14b2c379ae434062a009aefea9fc5df9)追问：现在有100多个工具，AI想调用的时候能找到自己想要的接口吗？怎么保障？；工具检索是如何做的？】
3. 多工具场景下的调度策略？ — 腾讯终面
4. 工具多导致 token 数过多，怎么解决？ — 蚂蚁一面 【阿里国际一面追问：Skill描述过长导致上下文爆炸】【小红书 Agent 岗一面追问：工具延迟加载触发时机与实现】【哔哩哔哩 AI 应用一面追问：大量工具描述导致 Prompt 膨胀】【[月之暗面（Moonshot）- Agent 应用开发岗](https://www.nowcoder.com/discuss/926274239747952640)追问：工具数量很多时，如何避免 Prompt 过长？】【[深信服Agent开发实习生一面二面，长时间被吊着，最终被横向掉了](https://www.nowcoder.com/feed/main/detail/14b2c379ae434062a009aefea9fc5df9)追问：Agent工具过多时你是怎么处理的？比如接口数量太多怎么解决？】
5. 工具调用成功但返回结果语义不完整，怎么设计中间层？ — 腾讯二面 【淘天二面追问：外部工具数据格式不匹配的自动映射】【淘天AI应用开发一面追问：MCP多工具返回格式不统一的标准化】【OPPO 一面追问：参数错误、失败和超时的统一处理】
6. Mock 是怎么实现的？在自动化生成测试的场景下 — 字节一面
7. 大模型的 Function Call 是什么？Tool Use 一般怎么用？ — 30题 【小红书AI应用开发追问：不做训练怎么让Agent调用工具+调用格式】【字节实习Agent开发一面追问：工具注册/解析/调用/回传全链路】【小红书 Agent 岗一面追问：tool_use 捕获、执行与非标准命令请求】【[BIGO 音频算法工程师一面](https://www.nowcoder.com/discuss/924359576990781440)】【[百度 Agent 一面](https://www.nowcoder.com/feed/main/detail/53542e2dcfd44b1d84b0ae55b4fc1b35)】【[启云方AI Agent一面凉经](https://www.nowcoder.com/feed/main/detail/fea2d18bd59a421da7d16fe16223d38c)追问：“语言调用工具”中的“语言”和真正的 tool call / function call 到底是什么关系？】
8. MCP 和 Skills 的本质区别是什么？ — 蚂蚁集团智能体与大模型应用二面 【蚂蚁AI应用开发二面同题：Skill 与 MCP 核心差异】【[钉钉二面](https://www.nowcoder.com/discuss/925181638412091392)追问：MCP 跟 Skill 有什么区别？】【[字节跳动 - AI Agent 开发岗（工程方向）](https://www.nowcoder.com/discuss/926273296180547584)追问：MCP 与 Skill 的核心区别是什么？迁移的原因是什么？】【[美团 - Agent 开发岗（场景设计方向）](https://www.nowcoder.com/discuss/926273749555376128)追问：MCP vs Skill 选型场景？】【[pdd agent 一面](https://www.nowcoder.com/feed/main/detail/ee971b755cbd475a91ef62cee38cdac8)追问：MCP是什么，为什么项目没有选用MCP而选择自己封装？Skill与MCP的核心区别是什么？】
9. MCP Server 是怎么构建的？ — 蚂蚁一面【[OPPO IT 开发一面](https://www.nowcoder.com/discuss/923561467092160512)】【[钉钉二面](https://www.nowcoder.com/discuss/925181638412091392)追问：自己有去搭建过 MCP Server 吗？】
10. Function Calling 的本质价值是什么？ — 30题 【蚂蚁Agent开发一面追问：有了FC是否可以没有MCP】【视频面经追问：FC/工具调用/普通Prompt调用三者区别】
11. 大厂开源 CLI 工具和 MCP 有什么区别？ — 蚂蚁一面
12. 手撕一个 ReAct 架构的 Agent — 蚂蚁二面
13. 你会如何设计工具 schema？ — 30题
14. 同一个能力是做成大而全工具还是多个小工具？ — 30题
15. MCP 协议的完整调用过程是怎样的？从 Host 到 Server 的每一步 — 高德实习一面 【蚂蚁Agent开发一面同题：MCP通信方式+配置方法】【腾讯AI应用开发一面追问：领域MCP工具（慢SQL诊断）与Agent系统串联】【唯品会大模型算法实习追问：Tool Schema 以 MCP JSON 注册后的内部链路】【[OPPO IT 开发一面](https://www.nowcoder.com/discuss/923561467092160512)】【[百度后端一面](https://www.nowcoder.com/discuss/924730985210458112)追问：一次 MCP 调用到底是谁发起、谁执行？；详细讲解一次 MCP 调用背后有哪些步骤。】【[去哪儿AI面试](https://www.nowcoder.com/discuss/924765100441903104)追问：MCP 的客户端和服务端交互的完整流程是怎么样的？中间的具体内容是什么？】【[拼多多 复活赛 一面](https://www.nowcoder.com/feed/main/detail/2109cf8eb0254507911fbf86bcbf51e4)追问：MCP 用过吗？Agent 和 MCP 的交互方式是怎样的？】
16. 如何在多智能体环境中实现动态发现并注册跨协议工具？ — 淘天一面 【遥望科技追问：工具自动注入的实现方式与意义】
17. LLM 是怎么从用户意图匹配到具体工具参数的？ — 高德实习一面【[启云方AI Agent一面凉经](https://www.nowcoder.com/feed/main/detail/fea2d18bd59a421da7d16fe16223d38c)追问：你提到“通过语言调用工具”，具体是怎么理解的？；以“查询天气工具”为例，用户说一句自然语言后，工具是怎么被触发的？】
18. 为什么将 Agent 工具注册到微服务注册中心（Nacos）而不是用 MCP？工具的自动注入怎么实现？ — 遥望科技Agent开发一面【[深信服Agent开发实习生一面二面，长时间被吊着，最终被横向掉了](https://www.nowcoder.com/feed/main/detail/14b2c379ae434062a009aefea9fc5df9)追问：动态工具注册中心是怎么做的？动态注入是怎么去注入的？；工具注册中心的构建过程中有什么难点吗？】
19. Agent 做多轮工具调用和单轮调用相比，会面临哪些额外挑战？ — 阿里国际一面
20. 推理模型为什么可能不支持工具调用？技术原因是什么？ — 已有正文（补录索引）
21. 多工具场景下怎么确定工具调用优先级？ — 已有正文（补录索引）
22. 开源模型的 Function Calling 能力较弱，如何通过微调或 Prompt Engineering 提升？ — Agent开发八股合集（南京大学）
23. 边界不好定义的场景，Skill形式不能很好区分场景披露工具，怎么办？ — 阿里暑期Agent算法二面
24. 工具返回了非常大的数据超出大模型上下文窗口，怎么办？ — 唯品会一面（新增）【[字节跳动 - AI Agent 开发岗（工程方向）](https://www.nowcoder.com/discuss/926273296180547584)追问：工具返回数据量过大时，如何进行分块或流式处理？】【[月之暗面（Moonshot）- Agent 应用开发岗](https://www.nowcoder.com/discuss/926274239747952640)追问：工具返回数据量过大时，如何处理？】【[8.26百度二面](https://www.nowcoder.com/feed/main/detail/190c6c68414b491d856091e42aef2386)追问：查询日志接口是现有的，怎么保证不会一次拉取过多日志导致上下文爆掉？】
25. 多Skill串行/嵌套时依赖冲突、参数不兼容的容错设计？ — 百度AI Agent前端研发实习生一面
26. MCP + OAuth2.1：为什么要把 OAuth2.1 接到 MCP 里？ — 视频面经汇总（新增）
27. Tool Result 回写模型时，消息契约应该包含哪些字段？ — [Newegg 一面](https://www.nowcoder.com/discuss/920719616005898240)（2026-08-22）【字节火山引擎 Managed Agent 一面追问：Function Call 与 Tool Result 回到上下文】【[字节中国交易与广告 AI 应用开发一面](https://www.nowcoder.com/feed/main/detail/b34f6902e8544fe2953696ed52e49dba)】
28. 没有 MCP 之前大模型调用工具走的是什么流程？MCP 本身有什么缺点或者挑战？ — 淘天AI Agent一面（新增）【小得盈满一面追问：上下文膨胀、Secret 隔离与工具投毒】
29. Agent 调用启动较慢的外部工具时，如何设计异步任务和结果回调？ — 途游 Agent二面（新增）【[月之暗面（Moonshot）- Agent 应用开发岗](https://www.nowcoder.com/discuss/926274239747952640)追问：异步任务如何处理？】
30. 如何评测 MCP Server / Tool 自身的契约、可用性和效果，并用轨迹 Badcase 持续迭代？ — 阿里控股 Agent Infra 暑期一面【[未知公司 Agent 二面](https://www.nowcoder.com/feed/main/detail/16675d793c0c42e8a6b46d42fb561561)追问：如何判断 CLI/MCP 是否 AI-Friendly】
31. MCP 返回结果支不支持流式？ — 淘天AI Agent一面（新增）
32. Tool-use SFT 的训练目标是什么？基座模型已经具备工具调用能力时，SFT 还需要学习什么？ — 唯品会NLP算法实习一面（新增）
33. 如何不用多智能体方案让 1000 个 Tools 正常工作？ — AI应用开发进阶面（新增）
34. 一个 Agent 如何同时连接多个 MCP Server，并保证用户与会话隔离？ — 百度秋招后端一面（新增）
35. CLI、Skill 与 sub-agent 的职责边界是什么？CLI 直接调用 LLM 和 Skill 拉起 sub-agent 应如何取舍？ — 小得盈满 AI 相关岗位一面（新增）
36. 跨平台工具授权即将过期时，Agent 如何调整调用顺序并安全续权？ — TikTok Agent工程师面试（新增）
37. MCP 工具治理为什么需要审计？应该审计哪些证据？ — 拓竹 AI Agent算法一面（新增）

38. 当治理规则需要修改服务代码时，如何安全落地？ — [9.10 虾皮二面](https://www.nowcoder.com/feed/main/detail/595a0cb450cf45e9a47a0d32084b9099)


## 03-fault-tolerance（38题）

1. Agent 如何减少幻觉？在工业场景下怎么做？ — 字节一面 【字节实习Agent开发一面追问：任务幻觉（Agent编造未请求的执行步骤）】【字节大模型测开一面追问：Temperature→0时还会有幻觉吗】【影石创新一面追问：如何定位幻觉来自模型、上下文还是工具】【[淘宝闪购 AI 应用研发二面](https://www.nowcoder.com/feed/main/detail/09ec7c36a2774223a93044a02b2c3ec0)】
2. 你怎么设计 Agent 的失败恢复机制？ — 腾讯二面 【淘天AI应用开发一面追问：工具报错时prompt引导自主重试】【[中兴软开一面](https://www.nowcoder.com/feed/main/detail/0b39815babfb47108464ffabdf929eba)】
3. 调支付接口超时了，Agent 怎么处理？ — 腾讯终面【[拼多多 - Agent 开发岗（工程化 + 数据库）](https://www.nowcoder.com/discuss/926273867092430848)追问：外部 API 超时的重试策略及防重试风暴？】
4. Agent 错误删除了数据，系统设计上怎么防范？ — 腾讯终面
5. 如何限制 Agent 的思考深度、工具调用次数，避免无限循环？ — 30题 【淘天一面追问：思维死循环专项检测与打断】【快手AI应用开发一面追问：调用指纹去重+相同参数只允许一次+终止条件设计】【百度大模型研发二面追问：工具失败后重复调用保护】【阿里 Agent Infra 一面题库同题：重复 Tool Call 与停止条件】【[月之暗面（Moonshot）- Agent 应用开发岗](https://www.nowcoder.com/discuss/926274239747952640)追问：如何设计任务完成的停止条件？】
6. 幻觉的各种治理手段，优缺点？行为限制在什么阶段做？ — 蚂蚁一面 【视频面经追问：从RAG/Prompt/输出约束三个角度拆解幻觉控制】【[去哪儿 AI 全栈 AI 面](https://www.nowcoder.com/feed/main/detail/9cf516b3c2404100baeac52564e40709)】
7. Agent 在中间步骤已经偏了，怎么尽早发现？ — 30题
8. Agent 执行 shell 命令怎么保证安全？还有哪些安全问题？ — 蚂蚁一面 【蚂蚁AI应用开发二面追问：文件操作与代码执行权限管理】【小红书 Agent 岗一面追问：拦截时机与规则引擎】【[百度 - Agent 研发岗（架构方向）](https://www.nowcoder.com/discuss/926273622006665216)追问：Agent 生成代码、执行命令的安全沙箱如何设计？】
9. Prompt 注入攻击如何防御？ — 快手一面【[月之暗面（Moonshot）- Agent 应用开发岗](https://www.nowcoder.com/discuss/926274239747952640)追问：如何防范 Prompt Injection 绕过系统指令？】
10. 资源紧张怎么处理？用户排队机制怎么实现？ — 蚂蚁一面
11. 工具调用的安全控制是怎么实现的？如何限制敏感接口？ — 快手一面
12. Skill 间需要传递敏感信息时，如何做到内部可用、对用户不可见？ — [百度 Coding Agent 二面](https://www.nowcoder.com/feed/main/detail/b9521e2b51e04afeac0a3a32e13f4da9)（新增）【[pdd agent 一面](https://www.nowcoder.com/feed/main/detail/ee971b755cbd475a91ef62cee38cdac8)追问：使用Skill实现时，如何防止向用户泄漏业务数据和核心脚本？】
13. 为什么在复杂的 Agent 闭环场景中，仅靠 RAG 无法彻底解决幻觉问题？ — 淘天一面 【淘天一面追问：数据/检索/生成三方面系统性降幻觉】【腾讯金融科技一面追问：知识库无内容但模型输出正确时的信任边界】
14. 高风险在线环境中，Agent 的异常管控方案怎么设计？ — 淘宝闪购一面【[中国电信风控 Agent 二面](https://www.nowcoder.com/feed/main/detail/22e18a3d20734429aec41b37744beadc)追问：央国企高安全水位、端侧配置与私钥保护】【[快手 AI 全栈一面](https://www.nowcoder.com/feed/main/detail/a30242712e8d456c839ff4223470f491)】
15. 支付等高敏感操作场景下，Human-in-the-Loop 流程怎么设计？ — 蚂蚁AI应用开发二面 【淘宝闪购一面同题：人工强制中断 Agent 执行与 HiL 处理】
16. Agent 的 Self-Reflection 机制怎么识别输出中的逻辑错误？（容错角度） — 蚂蚁AI应用开发二面 【字节AI一面追问：Reflection 连续失败 3 次后的降级策略】
17. Agent 系统的安全护栏怎么设计？敏感词拦截的工程方案有哪些？ — 快手AI应用开发算法一面【[腾讯/csig/元宝/内容安全/日常实习/三轮技术面试](https://www.nowcoder.com/feed/main/detail/60f381f558a848ceac18c666268dc7da)追问：我现在需要对云端 Agent 的输出做安全校验，你会怎么设计校验方案？】
18. 金融系统不能让 Agent 真实操作，怎么设计？（影子模式 + 渐进放权） — 京东一面
19. Agent 系统中网络抖动 vs 真实故障，如何区分判断？ — 滴滴AI agent开发日常实习
20. NL2SQL 场景下的 SQL 安全防护怎么做？ — 已有正文（补录索引）
21. 如果上下文爆炸或工具循环调用，怎么解决？ — 慧疗互联网医院Agent开发一面 【字节Agent开发实习生一面同题：三级压缩】【[格物致信（一面过，二面线下拒）](https://www.nowcoder.com/feed/main/detail/f68f0d54184944c391e0d7b6d1bb82c8)追问：Agent上下文窗口膨胀你是怎么解决的？难点是什么？】
22. Agent 系统的 fallback 是怎么做的？ — 字节Agent开发一面【[百度 Agent 一面](https://www.nowcoder.com/feed/main/detail/53542e2dcfd44b1d84b0ae55b4fc1b35)】
23. 整体的失败重试机制（node、RAG链、tools）分别怎么做？ — 字节Agent开发一面【阿里 Agent Infra 一面题库追问：分层 Timeout 与 Retry】
24. 状态机卡死悬停/死循环的排查与熔断机制？ — 百度AI Agent前端研发实习生一面【阿里 Agent Infra 一面题库追问：Circuit Breaker】【[百度 - Agent 研发岗（架构方向）](https://www.nowcoder.com/discuss/926273622006665216)追问：Agent 死循环的熔断机制如何设计？】【[月之暗面（Moonshot）- Agent 应用开发岗](https://www.nowcoder.com/discuss/926274239747952640)追问：如何设计 Agent 死循环的熔断机制？】
25. 工具调用返回结果为空或调用失败，Agent 应该怎么处理？是直接重试还是换策略？ — 最有料AI实习生面经（新增）【[快手 - Agent 开发岗（应用落地 + AI 工具）](https://www.nowcoder.com/discuss/926274020192841728)追问：工具调用失败率较高时，应从描述、重试、降级等哪些维度进行优化？】
26. 页面结构变化导致 Skill 失效时，如何检测、降级与修复？ — [百度 Coding Agent 二面](https://www.nowcoder.com/feed/main/detail/b9521e2b51e04afeac0a3a32e13f4da9)（新增）
27. 在跨境汇款等金融业务场景下，Agent 超时/失败如何应对并保证资金安全？ — 腾讯AI应用开发（新增）
28. Agent 失败通常有哪些原因？如何快速定位责任层？ — 点点互动Agent开发秋招一面（新增）【阿里 Agent Infra 一面题库同题：模型与 Infra 故障归因】【[8.26百度二面](https://www.nowcoder.com/feed/main/detail/190c6c68414b491d856091e42aef2386)追问：根因定位的 Agent 能详细讲一下吗？】
29. 所有模型超时或故障时怎么兜底？什么时候用规则引擎，什么时候转人工，服务恢复后怎么回切？ — 商汤大模型算法应用实习二面 【拼多多 AI Agent 提前批二面追问：API Provider 故障切换、负载均衡、自动恢复与回切】
30. Agent Workflow 如何保证节点原子性，并在部分成功后安全回滚？ — 字节剪映Agent一面（新增）【[美团 - Agent 开发岗（场景设计方向）](https://www.nowcoder.com/discuss/926273749555376128)追问：Agent 回滚机制（修改异常时恢复）？】
31. LLM 没有走标准 Tool Call，而是在文本里直接输出命令请求，系统如何识别、执行并拦截风险？ — 小红书 Agent 岗一面（新增）【[启云方AI Agent一面凉经](https://www.nowcoder.com/feed/main/detail/fea2d18bd59a421da7d16fe16223d38c)追问：模型是不是返回一段普通文本，然后从文本里通过正则等方式解析出工具调用？】
32. 如何对自己的 Agent 做系统化红队测试，而不是只测 Prompt Injection？ — 中兴 AI大模型算法岗一面（新增）【阿里 Agent Infra 一面题库追问：Prompt Injection 的 Infra 防线】
33. Coding Agent 看到 .env 文件会怎样？如何设计安全边界？ — Coding Agent面经（新增）
34. 长时间运行的 Coding Agent 等待用户决策时，如何避免任务永久卡住？ — 小红书 Agent 岗一面（新增）
35. 工具失败后，哪些异常处理应由大模型参与，哪些必须由确定性程序控制？ — 影石创新 AI Agent一面（新增）
36. 为什么安全攻击检测不能只依赖大模型？规则、专用模型和 LLM 应该如何分工？ — [字节中国交易与广告 Agent 一面](https://www.nowcoder.com/feed/main/detail/6dede073825e4ab493fcbce7f598a6c8)（2026-08-24）
37. Agent 无法处理任务时，“求助 / 升级”状态机应该如何设计？ — [百度 Agent 研发岗一面](https://www.nowcoder.com/discuss/926273622006665216)（新增）

38. 如何设计可靠的 Webhook 投递保障？ — [要务科技-面筋](https://www.nowcoder.com/discuss/926539013991796736)


## 04-memory-context（64题）

1. 上下文窗口不够用，对话太长了怎么办？ — 字节实习二面 【币安AI大模型实习一面追问：智能客服场景下agent压缩机制优劣对比】【阿里国际AI应用开发二面追问：压缩后如何保留否定约束和硬性条件】【快手AI应用开发一面追问：Agent Runtime 中 token budget 分层分配（system/user/memory/evidence/RAG）】【小红书 Agent 岗一面追问：两层压缩与 LLM 保留判定】【高德/字节一面追问：摘要不能简单合并全部历史、如何选择保留信息】【阿里 Agent Infra 一面题库同题：长 Context 不能全部塞给模型】【[蚂蚁 Agent 开发一面](https://www.nowcoder.com/feed/main/detail/39451cad5d2245b491d16778f2a9ca01)】【[虾皮一面](https://www.nowcoder.com/feed/main/detail/e133c2610bde4adc812bba66c62e1641)】【[拼多多 - Agent 开发岗（工程化 + 数据库）](https://www.nowcoder.com/discuss/926273867092430848)追问：1M 也不够怎么办？】
2. 长上下文里，怎么让 Agent 不忘记关键信息？ — 腾讯终面 【淘天一面追问：模型层面遗忘缓解机制】
3. 用户说“按老样子帮我订一下”，模糊需求怎么处理？ — 腾讯终面
4. 多 Agent / 多异步任务下，如何防止上下文污染？ — 字节一面
5. 讲一下 Agent 中的“长短期记忆” — 字节一面 【含追问：记忆更新策略】【淘天一面追问：短期/长期区分存储、更新策略】【蚂蚁AI应用开发二面同题：Agent 长期记忆设计思路】【淘天Agent开发同题：短期对话记忆和长期记忆分别怎么提取和存储】【快手AI应用开发一面追问：用户偏好记忆设计+压缩后 token 预算控制】【阿里国际/哔哩哔哩一面同题：分级存储与自动沉淀】【[字节中国交易与广告 AI 应用开发一面](https://www.nowcoder.com/feed/main/detail/b34f6902e8544fe2953696ed52e49dba)】【[百度 Agent 一面](https://www.nowcoder.com/feed/main/detail/53542e2dcfd44b1d84b0ae55b4fc1b35)】【[MiniMax - 大模型算法岗（后训练 / SFT / RL）](https://www.nowcoder.com/discuss/926272883872075776)追问：记忆模块如何实现，长期存储和短期存储分别采用什么方案？】【[字节跳动 - AI Agent 开发岗（工程方向）](https://www.nowcoder.com/discuss/926273296180547584)追问：如何进行记忆分层（工作记忆/长期记忆），存储方案如何设计？】【[万仞二面CEO](https://www.nowcoder.com/feed/main/detail/641608e014b147c7b8aaa3c2e4387f2c)追问：短期记忆和长期记忆怎么做的？】
6. 什么时候应该追问用户，什么时候自己继续推理？ — 腾讯二面 【淘天一面追问：主动澄清 vs 历史画像推断决策框架】【淘天一面追问：极度模糊表达的工程处理】【[美团 - Agent 开发岗（场景设计方向）](https://www.nowcoder.com/discuss/926273749555376128)追问：模糊需求（如“找个好吃的”）的多轮澄清机制？】
7. 你怎么理解 Agent 里的“状态”而不是“上下文”？ — 腾讯二面【阿里 Agent Infra 一面题库追问：State、Context、Memory 的区别】【[百度 Agent 一面](https://www.nowcoder.com/feed/main/detail/53542e2dcfd44b1d84b0ae55b4fc1b35)】
8. 三类上下文的优先级怎么处理？ — 腾讯二面【[字节二面（Trae）](https://www.nowcoder.com/discuss/924821959647440896)追问：上下文管理是怎么做的？】
9. 对于上下文工程有什么经验？有没有做过 to-do list？ — 抖音一面
10. Agent 记忆系统里的「做梦机制」（Dreaming）是什么？和 Reflection 有什么区别？ — 阿里云暑期实习Agent面经
11. 设计亿级用户、千亿级记忆条目的记忆系统 — 后端AI八股
12. 如何处理记忆的“新鲜度”与“重要性”之间的冲突？ — 后端AI八股
13. Agent 记忆存在偏见或事实性错误，如何发现并纠正？ — 后端AI八股
14. 如何沉淀部门级 Agent 记忆，既避免经验随人流失，又控制错误、过期和权限风险？ — [电商 Agent 三面](https://www.nowcoder.com/feed/main/detail/b6b453976c2d4e43a872054d695c2fe2)（新增）【[阿里千问 Agent 开发一面](https://www.nowcoder.com/feed/main/detail/463438ee0d9e403b98e8578a05ba4e3f)】
15. 什么是记忆的 Reflection 机制？ — 后端AI八股
16. 长期记忆选向量数据库还是 KV/关系数据库？ — 后端AI八股
17. 什么是记忆的幻觉问题？和 LLM 幻觉有何区别？ — 后端AI八股
18. 什么是“工具态记忆”（Tool-state Memory）？ — 后端AI八股
19. 记忆的容量规划需要考虑哪些因素？ — 后端AI八股
20. 如何判断当前对话与历史对话是否相关？ — 字节实习二面
21. 一条历史信息该进长期记忆还是只留当前会话？ — 30题【[去哪儿 AI 全栈 AI 面](https://www.nowcoder.com/feed/main/detail/9cf516b3c2404100baeac52564e40709)】
22. 记忆摘要、压缩、去重、合并的触发时机？ — 30题 【淘天AI应用开发一面追问：向量记忆库去重方案与语义合并】
23. 长期记忆检索时，怎么避免“语义相关但当前无用”的污染？ — 30题
24. 用户偏好、事实记忆、系统状态三者冲突了，信谁？ — 30题
25. 如何减少无关上下文对模型的干扰？当前上下文有哪些优化思路？ — 快手一面【[百度后端一面](https://www.nowcoder.com/discuss/924730985210458112)追问：处理上下文过长有哪些常见策略？】【[字节跳动9.3 Agent开发一面面经](https://www.nowcoder.com/discuss/925342611194286080)追问：随着提问轮次增加，上下文窗口会越来越大，该如何解决？】【[月之暗面（Moonshot）- Agent 应用开发岗](https://www.nowcoder.com/discuss/926274239747952640)追问：如何进行上下文管理，避免上下文过长导致效果下降？】【[第三次去哪儿旅行一面，AI面试问的是前端吗？](https://www.nowcoder.com/feed/main/detail/2ed12b3fa1d4491f8bb029f99cf9de73)追问：Agent记忆模块如何设计？上下文无限膨胀有哪些处理方案？】
26. Code Agent 的上下文工程，和普通对话 Agent 有哪些独特挑战？ — 蚂蚁一面【[OPPO IT 开发一面](https://www.nowcoder.com/discuss/923561467092160512)】【[拼多多 - Agent 开发岗（工程化 + 数据库）](https://www.nowcoder.com/discuss/926273867092430848)追问：大规模代码场景的上下文维护？】
27. Checkpoint 用什么数据库存？如何优化加载速度？ — AI工程师面试 【CVTE AI应用工程师一面追问：短期记忆为什么用 sqlite checkpointer】【钉学科技 FDE 实习一面追问：字段、一致性与换模型恢复】
28. 摘要总结往往会丢失关键细节，在长文本 Agent 中一般怎么来处理这一块？ — 淘天一面【[字节跳动9.3 Agent开发一面面经](https://www.nowcoder.com/discuss/925342611194286080)追问：压缩或者摘要肯定会丢失信息，如何使信息丢失最小化？】
29. 做上下文工程最关键的工作是什么？ — 蚂蚁二面
30. 在电商或导购场景下，用户的请求往往高度模糊，Agent 怎么来精准理解这种需求？ — 淘天一面
31. 会话记忆具体是怎么实现的？滑动窗口设几轮？摘要压缩怎么触发？ — 高德实习一面【[字节二面（Trae）](https://www.nowcoder.com/discuss/924821959647440896)追问：上下文压缩怎么做？】【[抖音电商Agent全栈开发工程师一面](https://www.nowcoder.com/discuss/925066865183858688)追问：记忆压缩怎么做？进行到第十一轮时，应该给模型哪些信息？】【[美团 - Agent 开发岗（场景设计方向）](https://www.nowcoder.com/discuss/926273749555376128)追问：记忆压缩（减少上下文同时保留关键信息）的实现？】【[深圳tuitti视界之外实习一面](https://www.nowcoder.com/feed/main/detail/9b1329caf4b64389a0ab666585bda045)追问：这个摘要是怎样使用的？】
32. 有没有了解过最前沿的记忆设计？ — 字节实习一面 【淘宝闪购一面追问：OpenClaw vs Hermes 分层压缩记忆对比】【美团Keeta一面追问：Mem0 原理与自实现记忆的区别】【CVTE AI应用工程师一面追问：OpenClaw 记忆机制借鉴】
33. Claude Code 的记忆架构是什么？上下文真的等于记忆吗？ — 字节实习一面 【小红书数据库智能化一面追问：主流 Agent 与 Claude Code 的上下文管理策略】【[阿里边缘bu 秋招一面 （已过）](https://www.nowcoder.com/feed/main/detail/bdebbb6088b6405e9eb2bd2c345acb6e)追问：你读过哪些 Claude Code 源码，了解它的上下文管理机制吗？】
34. 什么是上下文缓存（Prompt Caching）？它在 Agent 系统中有什么价值？ — 蚂蚁AI应用开发二面【阿里 Agent Infra 一面题库同题：上下文预计算与 Prefix Cache】【[全栈实习一面，20分钟居然问这么细😂](https://www.nowcoder.com/feed/main/detail/4af1e257116e4e36970c6e0d8bf2f70e)追问：你的项目有没有做前上下文缓存、前缀缓存？】
35. 长周期对话（间隔数周后继续）如何管理历史？冷启动怎么做？ — 淘宝闪购一面【[阿里千问 Agent 开发一面](https://www.nowcoder.com/feed/main/detail/463438ee0d9e403b98e8578a05ba4e3f)】
36. 设计会话记忆系统时需要考虑哪些维度？ — 高德实习一面
37. 用户对话中频繁切换话题，会话记忆该怎么设计？ — 高德实习一面
38. Lost in the Middle 问题是什么？有哪些解决方案？ — 淘宝闪购一面
39. 怎么判断当前用户的提问需不需要去检索长期记忆？ — 淘天Agent开发
40. 怎么实现多轮对话过程中，根据用户反馈自我调整的功能？ — 腾讯AI应用开发实习一面
41. 基于滑动窗口摘要时，合并还是分别保留？各自适合什么场景？ — 快手AI应用开发一面
42. 如果让你设计一个三层记忆机制，整体架构和压缩方法怎么设计？ — 快手AI应用开发一面
43. 你的向量记忆库是如何更新用户画像的？ — 快手AI应用开发算法一面
44. 记忆冲突怎么解决？比如用户前后说了不同的过敏信息 — 美团Agent开发（智能客服方向）二面【[百度 Agent 一面](https://www.nowcoder.com/feed/main/detail/53542e2dcfd44b1d84b0ae55b4fc1b35)】【[去哪儿 AI 全栈 AI 面](https://www.nowcoder.com/feed/main/detail/9cf516b3c2404100baeac52564e40709)】
45. 短期记忆压缩后，过了很长时间又需要当时完整信息怎么办？ — AI初创Agent开发实习【[深圳tuitti视界之外实习一面](https://www.nowcoder.com/feed/main/detail/9b1329caf4b64389a0ab666585bda045)追问：当需要替换执行结果时，怎样还原之前的上下文，以便基于更完整的信息作出判断？】【[作业帮秋招一面](https://www.nowcoder.com/feed/main/detail/c86c7591ba9d47b696774ddb48cdc9cb)追问：会话记忆管理使用了滑动窗口 + 压缩，压缩过程会不会丢失记忆，该如何解决该问题？】
46. 压缩过程中会丢失工具调用历史，导致模型重复调用工具，怎么解决？ — 美团Agent开发（智能客服方向）二面
47. 如何判断是 Prompt 内容影响决策，还是 Prompt 太长导致注意力涣散？ — 淘天AI Agent暑期实习一面
48. 为什么要区分静态长期记忆和动态长期记忆？各自存什么？ — 字节跳动Agent二面（Coding Agent）（新增）
49. 每轮对话都触发长期记忆存储，用户记忆快速积累、存得过多怎么办？ — 字节跳动Agent二面（Coding Agent）（新增）
50. 云端 Coding Agent 的容器迁移或重启时，如何恢复会话上下文、工作区和进行中的任务？ — [腾讯 WXG 微信读书一面](https://www.nowcoder.com/feed/main/detail/3ffc762437274543b6a8f5e2ea6fb535)（2026-08-24）【[小米 - AI Agent 开发（三面综合）](https://www.nowcoder.com/discuss/925163737139429376)追问：如何设计 Agent 的状态持久化？容器重启后如何恢复会话？】【[拼多多 - AI Agent 开发（工程化 + 数据库方向）](https://www.nowcoder.com/discuss/925527160763187200)追问：长流程任务的“断点恢复”能力你是怎么做的？服务重启后如何加载未完成状态？】【[字节跳动 - AI Agent 开发岗（工程方向）](https://www.nowcoder.com/discuss/926273296180547584)追问：如何设计断点续传，使服务重启后能够恢复任务？】【[阿里巴巴（阿里云）- Agent Infra](https://www.nowcoder.com/discuss/926273487512113152)追问：如何实现状态持久化，使容器重启后会话恢复？】
51. Agent 做上下文压缩后，如何验证没有破坏当前任务？ — Coding Agent面经（新增）【[字节跳动 - AI Agent 开发岗（工程方向）](https://www.nowcoder.com/discuss/926273296180547584)追问：如何设计上下文压缩策略，以及如何评估信息丢失？】【[拼多多 复活赛 一面](https://www.nowcoder.com/feed/main/detail/2109cf8eb0254507911fbf86bcbf51e4)追问：上下文压缩时怎么降低信息丢失的概率？】
52. 跨会话记忆如何从对话中提取？哪些信息值得写入长期记忆？ — 小红书 Agent 岗一面（新增）【[〔社招〕〔面经〕9月初XX科技(中厂) AI全栈工程师（Agent应用）一面 挂](https://www.nowcoder.com/discuss/926232883432296448)追问：从对话 session 里沉淀“真正有价值的知识”，而不是“改字号/美化”这类操作噪声？】【[万仞二面CEO](https://www.nowcoder.com/feed/main/detail/641608e014b147c7b8aaa3c2e4387f2c)追问：怎么让短期记忆变成长期记忆？】
53. 上下文预算不足时，如何按任务依赖压缩，而不是按时间删除旧消息？ — 腾讯互娱全栈开发（AI）二面（新增）【[字节 AI 应用开发二面](https://www.nowcoder.com/feed/main/detail/7e8a821479a649fd914e449d312eeb95)】【[百度后端一面](https://www.nowcoder.com/discuss/924730985210458112)追问：上下文压缩时会对所有内容一视同仁，还是会侧重不同内容？；具体应该如何压缩上下文？】
54. 前 10 轮都变成了总结，之前的原始上下文就不需要了吗？ — 月之暗面Agent开发岗（新增）【[深圳tuitti视界之外实习一面](https://www.nowcoder.com/feed/main/detail/9b1329caf4b64389a0ab666585bda045)追问：恢复时模型看到的只有摘要，还是也会看到之前的完整消息或上下文？】
55. 已进行 10 轮并做了总结，第 11 轮开始时，总结怎么处理？是重算前 11 轮还是叠加？ — 月之暗面Agent开发岗（新增）
56. 当用户对话零碎、跨轮次且意图发生跳跃时，如何结合上下文准确判断当前意图？ — 某小厂FOSHO AI应用开发二面（新增）
57. session 里的临时文件存主服务还是 skill 进程服务，要不要删，什么时候删？ — 阿里淘天Agent开发一面（新增）
58. 大体积工具结果落盘后，为什么还要返回预览？预览内容应该如何选择？ — 小红书 Agent 岗一面（新增）
59. 如何用 Prompt 提取用户风格偏好？风格偏好应包含哪些内容？ — 小红书 Agent 岗一面（新增）
60. 大模型生成会话摘要时，如何避免摘要内容污染用户偏好？新结论推翻旧结论时怎么保留？ — 百度内容营销与广告日常实习一面（新增）
61. 金融 Agent 执行股价提醒等定时任务时，应该携带哪些历史上下文？ — 顺极 Agent开发二面（新增）
62. 按大纲分章节生成长文时，如何维持跨章节连续性与事实一致性？ — 成都 Agent 实习面经（新增）
63. Codebase Memory 应该如何初始化、增量更新和失效？ — [拼多多 Agent 开发岗一面](https://www.nowcoder.com/discuss/926273867092430848)（新增）

64. 为什么长视频通常需要切片和分阶段处理，而不是一次性输入大模型？ — [阿里 Token Foundry AI应用研发二面面经](https://www.nowcoder.com/feed/main/detail/ed25d2f60ddc4436b0139a7c52e62a61)


## 05-eval-and-vision（49题）

1. 如何量化评估一个上线的 Agent 好坏？除了准确率 — 腾讯终面【[百度 - Agent 研发岗（架构方向）](https://www.nowcoder.com/discuss/926273622006665216)追问：如何量化 Agent 的“智能程度”（除准确率外）？】【[美团 - Agent 开发岗（场景设计方向）](https://www.nowcoder.com/discuss/926273749555376128)追问：任务完成率统计及避免主观评估？】【[深信服Agent开发实习生一面二面，长时间被吊着，最终被横向掉了](https://www.nowcoder.com/feed/main/detail/14b2c379ae434062a009aefea9fc5df9)追问：最终的效果怎么样？准确率达到了多少？怎么测评？】【[8.26百度二面](https://www.nowcoder.com/feed/main/detail/190c6c68414b491d856091e42aef2386)追问：你们怎么评估这个 Agent 的效果，以及后续怎么优化？】【[拼多多 复活赛 一面](https://www.nowcoder.com/feed/main/detail/2109cf8eb0254507911fbf86bcbf51e4)追问：你们用的 Agent 在实际过程中有没有评价指标？比如准确率、误报率，处理现网配置时有没有这类指标？】【[PDD Agent三面](https://www.nowcoder.com/feed/main/detail/9908477cdd4041fabacbfbf02febb13c)追问：Agent输出效果如何量化评估？】
2. 当前阻碍 Agent 大规模落地的最大挑战？ — 腾讯终面【[百度 - Agent 研发岗（架构方向）](https://www.nowcoder.com/discuss/926273622006665216)追问：当前 Agent 系统面临的最大工程挑战是什么（上下文、工具、规划）？】
3. Agent 在线上最难监控的指标是什么？ — 腾讯二面
4. 如何对 Agent 记忆系统的效果进行量化评估？ — 后端AI八股
5. AI 工具最大的帮助场景是什么？ — 腾讯一面 【视频面经追问：平时用哪些AI工具+差异对比】【[去哪儿 AI 全栈 AI 面](https://www.nowcoder.com/feed/main/detail/9cf516b3c2404100baeac52564e40709)】
6. 从开发者角度，做 Agent 最难的部分？ — 腾讯一面【[百度 Agent 一面](https://www.nowcoder.com/feed/main/detail/53542e2dcfd44b1d84b0ae55b4fc1b35)】【[9.4 某小厂 AI Agent hr+技术面](https://www.nowcoder.com/feed/main/detail/10b2fcaf73d2401f8636bd0459e1cd08)追问：在该 Agent 项目开发中，你认为最难的技术点或挑战是什么？是如何迭代解决的？】
7. 有没有遇到过 AI 工具无法解决的场景？ — 腾讯一面【[深信服Agent开发实习生一面二面，长时间被吊着，最终被横向掉了](https://www.nowcoder.com/feed/main/detail/14b2c379ae434062a009aefea9fc5df9)追问：如果出现当前已有工具无法解决的问题时，怎么去解决的？】
8. Agent 框架还有哪些地方可以改进？ — 腾讯一面
9. 怎么给 Agent 建立评测体系？只看成功率为什么不够？ — 30题 【阿里国际二面追问：调优 case + 评测集构建】【顺极/曹操出行一面追问：验证环节、长链路稳定性和 Agent 评测】【[阿里淘天一面](https://www.nowcoder.com/feed/main/detail/a32b3c75644e4994933a38e1dfb16bc1)】【[蚂蚁 Agent 开发一面](https://www.nowcoder.com/feed/main/detail/39451cad5d2245b491d16778f2a9ca01)】【[字节 AI Agent 研发一面](https://www.nowcoder.com/feed/main/detail/2ba7e96d48634777990b28c2cb322f40)】【[中兴软开一面](https://www.nowcoder.com/feed/main/detail/0b39815babfb47108464ffabdf929eba)】【[钉钉一面](https://www.nowcoder.com/discuss/923765750446202880)】【[MiniMax - 大模型算法岗（后训练 / SFT / RL）](https://www.nowcoder.com/discuss/926272883872075776)追问：如何评测 Agent 的工具调用能力并构建评测集？】【[作业帮秋招一面](https://www.nowcoder.com/feed/main/detail/c86c7591ba9d47b696774ddb48cdc9cb)追问：有没有做过 Agent 评测相关工作？】【[pdd agent二面](https://www.nowcoder.com/feed/main/detail/f5e7351df8364147ac8da085b99d9d18)追问：Agent评测体系，测试用例覆盖范围？】
10. RAG 系统的回答准确率怎么计算？ — 蚂蚁二面【[字节二面（Trae）](https://www.nowcoder.com/discuss/924821959647440896)追问：准确率怎么计算？】
11. 如何从真实 Issue 构建可复现的缺陷修复 Agent Benchmark，并防止污染和假修复？ — [字节 AI Agent 研发一面](https://www.nowcoder.com/feed/main/detail/2ba7e96d48634777990b28c2cb322f40)（新增）
12. 线上反馈“有时好有时差”，第一步看什么？ — 30题
13. Agent 上线到生产环境，最容易被低估的三个风险点？ — 30题
14. 2026 年做 Agent 应用开发，跟去年相比最大的变化？ — 30题
15. 了解最近 AI 的新方向吗？ — 30题
16. 通过什么方式去验证 Skill 的提升效果，指标是什么？ — 美团食杂后端一面 【电商库存一面追问：Skill 变更影响面回归】【字节火山引擎 Managed Agent 一面追问：脚本与模型评审对比两个 Skill】【[快手 AI 全栈一面](https://www.nowcoder.com/feed/main/detail/a30242712e8d456c839ff4223470f491)】【[快手 - Agent 开发岗（应用落地 + AI 工具）](https://www.nowcoder.com/discuss/926274020192841728)追问：Skill 的质量评估指标有哪些？】【[作业帮一面 9.5](https://www.nowcoder.com/feed/main/detail/21ca46108ebf479fb8056c6e9f61d42f)追问：怎么验证 skill 的效果？怎么判断 skill 行不行、要不要改？】【[阿里边缘bu 秋招一面 （已过）](https://www.nowcoder.com/feed/main/detail/bdebbb6088b6405e9eb2bd2c345acb6e)追问：任务执行完成率从不足 50% 提升到 100%，这个指标是怎么评测出来的？】
17. RAG 系统如何评测？评测维度和指标？评测数据集怎么构建？ — 快手一面 【字节AI一面追问：评测集规模/分布/baseline 三件套】【[钉钉一面](https://www.nowcoder.com/discuss/923765750446202880)】【[字节二面（Trae）](https://www.nowcoder.com/discuss/924821959647440896)追问：评测机制怎么做？】【[腾讯/csig/元宝/内容安全/日常实习/三轮技术面试](https://www.nowcoder.com/feed/main/detail/60f381f558a848ceac18c666268dc7da)追问：对于什么场景进行评测？评测目标是什么？评测集怎么构建的？】【[百度Agent一面](https://www.nowcoder.com/feed/main/detail/72858aade19d443facc870fea8bb134f)追问：评测集是怎么做的？】
18. Agent 端到端成功率和工具误调用率怎么量化？怎么改进？ — 腾讯AI应用开发二面 【快手AI应用开发一面追问：Tool 调用准确率拆分（工具选择/参数填充/无效调用/重复调用/任务成功率）】【科大讯飞一面追问：自动建单结果的评估维度设计】【[百度 - Agent 研发岗（架构方向）](https://www.nowcoder.com/discuss/926273622006665216)追问：工具调用成功率如何进行离线、在线评测？】
19. Ragas 评测框架是什么？Answer Relevance 偏低时，怎么区分是检索问题还是模型问题？ — 蚂蚁AI应用开发二面 【淘天AI应用开发一面追问：Context Precision 过低优化方案】
20. 如何为 Word、PDF、Markdown 等文档生成与编辑能力设计通用自动评测框架？ — [百度 AI 测开一面](https://www.nowcoder.com/feed/main/detail/cd8e446a6ec14edfa53cf4c7b6864c4d)（新增）
21. 怎么理解 Vibe Coding？你有哪些实践经验？ — 蚂蚁AI应用开发二面 【科大讯飞一面追问：各Vibe Coding工具特点与CC/Codex使用感受对比】【[快手 - Agent 开发岗（应用落地 + AI 工具）](https://www.nowcoder.com/discuss/926274020192841728)追问：Vibe Coding 在实际工程中的优缺点是什么？】
22. 如何衡量 Agent 的 Planning 能力 vs Hallucination Rate？ — 淘天一面
23. 设计一个电商客服 Agent 的评测方案——商品咨询、售后处理、投诉安抚三类任务分别评估 — 淘天一面
24. 用户在线反馈怎么收集？不同模型和 Prompt 的 AB 测试怎么设计？ — 快手AI应用开发一面【[美团 - Agent 开发岗（场景设计方向）](https://www.nowcoder.com/discuss/926273749555376128)追问：AB 测试评估两种 Prompt 策略？】
25. AI 写代码越来越强，算法工程师的角色会怎么变？ — 字节TikTok AI应用开发一面【[虾皮一面](https://www.nowcoder.com/feed/main/detail/e133c2610bde4adc812bba66c62e1641)】
26. 哪些类型的 Agent 产品在未来 2 年内最可能被淘汰？ — 字节TikTok AI应用开发一面
27. 线上 log 是海量的，怎么转化成有限的线下评测集？随机抽样为什么不行？ — 字节跳动AI Agent评测二面（新增）【[钉钉一面](https://www.nowcoder.com/discuss/923765750446202880)】【[腾讯/csig/元宝/内容安全/日常实习/三轮技术面试](https://www.nowcoder.com/feed/main/detail/60f381f558a848ceac18c666268dc7da)追问：怎么保证构建的评测集覆盖所有场景且可用？】【[阿里边缘bu 秋招一面 （已过）](https://www.nowcoder.com/feed/main/detail/bdebbb6088b6405e9eb2bd2c345acb6e)追问：评测集和 Ground Truth 是如何构造的？】
28. Agent 后续的发展方向？哪些场景更容易落地？ — 视频面经汇总（新增）
29. 面试反问环节：怎么提出有深度的问题？ — 视频面经汇总（新增）
30. Text2SQL 系统的准确性评测与用户反馈回流机制 — 数据智能查询平台面试（新增）
31. RAG 召回链路监控与召回漂移检测 — 数据智能查询平台面试（新增）
32. 能不能不走“线上转线下评测集”，直接对线上 case 做无 GT 的打分和效果观测？ — 字节跳动AI Agent评测二面（新增）
33. Agent 自进化闭环如何设计？怎样判断沉淀出的经验值得进入系统？ — 字节Agent开发实习生一面（新增）【电商库存一面追问：人工审批、C 端灰度与回滚】【字节火山引擎 Managed Agent 一面追问：自动更新 AGENTS.md / Skills 后验证提升】【[阿里控股 Agent Infra 二面](https://www.nowcoder.com/feed/main/detail/627844d5923149b6ac46a631b2b41d5a)】
34. 如何证明 Agent 的最终答案真正使用了工具或检索证据，而不是凭模型常识猜中？ — Momenta Agent开发一面、阿里 Agent开发一面（新增）
35. 独立 Verifier 和 LLM-as-Judge 应该如何分工？ — 阿里千问 C端算法实习一面（新增）【[字节中国交易与广告 AI 全栈二面](https://www.nowcoder.com/feed/main/detail/0f77410f8b1b4daca879d5ff99c7ae07)】
36. 树形意图识别和逐层路由应该如何设计，并构造评测集避免误差级联？ — 快手 AI应用开发一面【[大方云图研发实习一面](https://www.nowcoder.com/feed/main/detail/a9a40feb4e1e4d0ca7c3f8c3ba67d487)追问：双阶段路由的专精与错误阻断】
37. 如何通过两套 Harness 的同任务对照与组件消融定位效果差异？ — [Teamily AI QA/测开面经](https://www.nowcoder.com/feed/main/detail/6a01e27dc1b142d29921eb3cc7bcd20f)（新增）【[深信服 ai agent 一面](https://www.nowcoder.com/feed/main/detail/83326f3bcc5546b2b556373ad29a6d71)追问：如何评估 Harness 效果？】
38. Skill 路由应该如何构造测试集并评估？ — 字节Agent测评一面（新增）
39. Multi-Agent 出现 Badcase 时，如何定位责任 Agent，并判断是否需要 SFT？ — 字节Agent开发二面（新增）
40. Skill 的调用量、Token 成本和效果埋点应该放在哪一层？ — 电商库存二面（新增）
41. 供应商不返回 usage 时，如何核算 Agent 的 Token 和成本？ — 成都晓多科技 Agent开发岗二面（新增）
42. 什么是 AI-native 团队？如何判断团队离 AI-first 还有多远？ — HR系统一面（新增）
43. 如何判断用户反馈真的让 Agent 变好，而不是噪声或选择偏差？ — MiniMax平台研发一面（新增）
44. 评审 Agent 为什么要左移？应该左移到需求、设计还是编码阶段？ — 字节社招一面（新增）
45. 如何为跨任务重复出现的安全或质量问题生成稳定 Fingerprint，并安全接入自动修复 Agent？ — [元石科技后端/Agent 一面](https://www.nowcoder.com/discuss/921742843704549376)（新增）
46. 如何实现基于 VLM 的 Benchmark 系统，并避免评测模型自说自话？ — [深信服 Agent 开发一面](https://www.nowcoder.com/feed/main/detail/83326f3bcc5546b2b556373ad29a6d71)（新增）

47. 哪些业务场景不适合引入 Agent？ — [虾皮测开日常实习一面](https://www.nowcoder.com/discuss/927594784770764800)
48. 如何设计消融实验并判断模块贡献？ — [美团面经-美团算法岗面经-01](https://www.nowcoder.com/discuss/927381090602348544)
49. 串行链路修改一个节点后，如何做精确归因？ — [知识科技 数据平台 二面](https://www.nowcoder.com/feed/main/detail/c478feeef29340caac7b8c44d5a6c5e4)


## 06-multi-agent-collab（35题）

1. 多智能体怎么协作？ — 腾讯终面【[百度正式批：一面结束第二天就约二面了](https://www.nowcoder.com/discuss/925108144831725568)追问：你项目做多智能体协同和xx，这有什么优点和难点吗？】
2. 多 Agent 系统里，怎么防止踢皮球或死循环？ — 腾讯终面【[中兴软开一面](https://www.nowcoder.com/feed/main/detail/0b39815babfb47108464ffabdf929eba)】
3. 多 Agent 之间需要共享状态吗？ — 腾讯终面
4. 怎么判断该做单 Agent 还是多 Agent？ — 30题 【阿里国际一面追问：Claude Code 是 multi 还是 single agent】【PDD/国际业务 Agent 一面追问：代码生成保障与单体/多 Agent 边界】【[钉钉一面](https://www.nowcoder.com/discuss/923765750446202880)】【[阿里千问平台开发复活赛一面](https://www.nowcoder.com/feed/main/detail/141447389dab4e8e9ca6db742a514f39)】
5. 多 Agent 协作中，记忆如何共享？ — 30题 【淘天一面追问：记忆隔离与上下文污染防治】【小红书AI应用开发同题：多Agent上下文管理与共享】
6. 单 Agent 还是多 Agent？子 Agent 的任务？ — 字节一面
7. 按“职能拆分”和“阶段拆分”各有什么优缺点？ — Agent 开发面试 30 题
8. Handoff 的核心难点是什么？ — 30题
9. MCP 和 A2A 分别解决什么层面的问题？ — 30题
10. 什么时候该用 subagent？ — 30题 【bilibili AI研发实习一面追问：主Agent和子Agent共用同一个上下文吗？】【遥望科技追问：主Agent和子Agent的协调机制怎么做】【小红书 Agent 岗一面追问：多 Agent 优势与上下文压力】
11. 任务简单但工具调用多，用 subagent 是否浪费 token？ — 30题
12. 图片信息怎么在 subagent 之间流转？ — 30题
13. Multi Agent 系统中 Router 节点依据什么规则把任务分给子 Agent？ — 淘天二面 【淘天AI应用开发一面追问：LLM路由 vs 规则路由优劣对比】【[虾皮Agent一面](https://www.nowcoder.com/feed/main/detail/409dc8793a7b450eb51ee32c2b923d49)追问：复杂任务场景下，中心调度 Agent 如何路由调用不同的 subAgent？】
14. 三层 Agent（Root/Main+Fallback/Sub-Agent）协同策略 + 跨层上下文传递 — 淘天Agent开发【[虾皮Agent一面](https://www.nowcoder.com/feed/main/detail/409dc8793a7b450eb51ee32c2b923d49)追问：多层子 Agent 调用会不会造成中心调度 Agent 上下文爆炸？怎么解决？】
15. Multi-Agent 如何通信？不同项目分别用了哪些通信方法？（含 MCP vs A2A 协议层次对比） — 币安AI大模型实习一面【[中兴软开一面](https://www.nowcoder.com/feed/main/detail/0b39815babfb47108464ffabdf929eba)】
16. 多 Agent 怎么编排的？用的什么编排模式？ — 百度实习一面
17. Multi-Agent 中心化编排模式 vs 点对点架构，核心区别和优势是什么？ — 蚂蚁AI应用开发二面
18. 为什么大家都在用 Multi-Agent？从一开始到现在原因是否有变化？ — 币安AI大模型实习一面
19. 如果让两个不同的 Agent 产品进行对话（比如 Claude Code 和 Cursor），在协议层面应该怎么做？ — 字节TikTok AI应用开发一面
20. 智能体可信通信怎么实现？ — 已有正文（补录索引）
21. 多个 Agent 并发操作数据库或文件，这种并发怎么处理？ — 蚂蚁Agent开发一面（新增）【[拼多多 - AI Agent 开发（工程化 + 数据库方向）](https://www.nowcoder.com/discuss/925527160763187200)追问：多 Agent 运行机制是怎样的？如何防止并发修改同一文件？】【[拼多多 - Agent 开发岗（工程化 + 数据库）](https://www.nowcoder.com/discuss/926273867092430848)追问：多 Agent 并发修改同一文件的冲突防止？】
22. 子 Agent 之间的上下文怎么传递？传什么、不传什么？ — 阿里Agent面经（新增）【[阿里边缘bu 秋招一面 （已过）](https://www.nowcoder.com/feed/main/detail/bdebbb6088b6405e9eb2bd2c345acb6e)追问：各层 Agent 之间的上下文如何传递？；如何保证传给子 Agent 的上下文足够完整，不会遗漏关键信息？】
23. 多 Agent 协作常见模式有哪些？各自适合什么任务类型？ — 阿里Agent面经（新增）【[蚂蚁 Agent 开发一面](https://www.nowcoder.com/feed/main/detail/39451cad5d2245b491d16778f2a9ca01)】
24. 主 Agent 与子 Agent 的通信和进度同步怎么做？是推还是拉？ — 广州某小厂Agent后端开发二面（新增）【[阿里边缘bu 秋招一面 （已过）](https://www.nowcoder.com/feed/main/detail/bdebbb6088b6405e9eb2bd2c345acb6e)追问：主 Agent 与二级 Agent、子 Agent 之间如何通信？】
25. 校验 Agent 和推理 Agent 结论冲突时怎么处理？ — 商汤大模型算法应用实习二面（新增）【[字节跳动 - AI Agent 开发岗（工程方向）](https://www.nowcoder.com/discuss/926273296180547584)追问：语音转录复核 Agent 场景中，规则与模型冲突时如何处理？】
26. 大规模 Multi-Agent 如何做调度、背压和资源隔离？调度器崩溃或 Leader 派错任务时怎么恢复？ — 深信服 Agent 开发一面、钉学科技 FDE 实习一面（新增）
27. 如何按租户、任务和 Agent 层级设置分层并发预算？ — 小红书 AI Agent开发一面【[顺极 Agent 开发二面](https://www.nowcoder.com/feed/main/detail/93a26b84a6634558b7228bf350c709b5)追问：模型配额、CPU/内存、工具与依赖图如何共同决定上限】
28. 多个 Agent 并行跑的时候状态竞争怎么避免？ — 淘天AI Agent一面（新增）
29. 如果拆成感知/推理/校验 Agent，哪些能并行哪些要顺序，什么时候需要反向通信？ — 商汤大模型算法应用实习二面（新增）
30. 在 A2A 场景下，如何防止两个 Agent 陷入递归对话？ — AI应用开发进阶面（新增）
31. 业务模块增删时，如何治理 Multi-Agent 能力拓扑，避免 Agent 增殖和路由配置失控？ — 懂车帝 Agent 开发一面（新增）
32. 如何保证多 Agent 通信结果明确、可验证，而不是自然语言互相猜？ — [国际业务 Agent 一面](https://www.nowcoder.com/feed/main/detail/3c305b0c1565458ba05c9906322f5327)（2026-08-22）
33. 复杂 Agent 为什么拆成 LangGraph 子图而不是单条 Pipeline？子图的状态与 IO 契约如何设计？ — [小红书/百度 Agent 实习一面](https://www.nowcoder.com/feed/main/detail/e319aadc79a9479397a6661a7f5ca088)（2026-08-24）
34. 多 Agent 执行策略如何根据任务动态选择，并在运行中安全切换？ — 字节 AI Agent 二面实习面经（新增）
35. 多人、多 Agent、跨设备协同与“群聊式多 Agent”有什么不同？ — [跨设备多 Agent 项目一面](https://www.nowcoder.com/feed/main/detail/9b1329caf4b64389a0ab666585bda045)（新增）

## 07-engineering-pitfalls（69题）


1. Agent 的成本怎么控制？ — Agent 岗面试高频题【字节实习二面追问：LobeChat 为什么烧 token】【[顺极 Agent 开发二面](https://www.nowcoder.com/feed/main/detail/93a26b84a6634558b7228bf350c709b5)追问：Agent 全量开放后的成本与容量治理】【[字节 AI 应用开发二面](https://www.nowcoder.com/feed/main/detail/7e8a821479a649fd914e449d312eeb95)】【[百度 - Agent 研发岗（架构方向）](https://www.nowcoder.com/discuss/926273622006665216)追问：大规模部署下如何控制 Token 成本（缓存、模型选型、结果复用）？】
2. 开发 Agent 时踩过什么坑？ — 高频题【[阿里国际 Agent 开发三面](https://www.nowcoder.com/feed/main/detail/747f07e71f4448bebdce6ada5de800cd)】【[快手 AI 全栈一面](https://www.nowcoder.com/feed/main/detail/a30242712e8d456c839ff4223470f491)】
3. 为什么很多 Agent Demo 很惊艳，一上线就不稳定？ — 腾讯二面
4. 用过哪些 Code Agent？优缺点？ — 腾讯AI应用开发 【高德实习一面追问：日常 AI Coding 实战工作流】【蚂蚁Agent开发一面追问：企业多系统改需求AI Coding怎么处理】【淘天Agent开发追问：AI辅助编程工作流拆解+提示词策略与人工审核介入点】【视频面经追问：做代码重构时怎么用AI辅助】【字节火山引擎 Managed Agent 一面追问：如何完成项目开发】【[杭州和为机电 AI 应用工程师面试](https://www.nowcoder.com/discuss/923620045412933632)】【[OPPO IT 开发一面](https://www.nowcoder.com/discuss/923561467092160512)】
5. 平时写的代码有多少是 AI 生成的？ — 腾讯一面 【百度实习一面追问：AI coding 占比的回答策略】【[杭州和为机电 AI 应用工程师面试](https://www.nowcoder.com/discuss/923620045412933632)】【[抖音电商Agent全栈开发工程师一面](https://www.nowcoder.com/discuss/925066865183858688)追问：AI Coding 的占比大概是多少？】【[9.2百度AI测开2面](https://www.nowcoder.com/feed/main/detail/a4c9480945fa481c98949ffb66cd2e3a)追问：在你们日常的 Coding 工作中，大约有多少比例的代码是通过 AI Coding 或 Vibe Coding 生成的？】
6. 平时用过哪些 AI Agent 工具？ — 腾讯一面【[杭州和为机电 AI 应用工程师面试](https://www.nowcoder.com/discuss/923620045412933632)】
7. 你熟悉的 Agent 框架，架构设计上有什么优势？ — 腾讯一面
8. 自己做 Agent 时，踩过最大的坑？ — 腾讯一面
9. 如何保证 AI 代码生成的质量与掌控性？ — 蚂蚁一面【[字节 AI 应用开发二面](https://www.nowcoder.com/feed/main/detail/7e8a821479a649fd914e449d312eeb95)】【[去哪儿 AI 全栈 AI 面](https://www.nowcoder.com/feed/main/detail/9cf516b3c2404100baeac52564e40709)】【[阶跃星辰（Stepfun）- 大模型算法岗（Post-train）](https://www.nowcoder.com/discuss/926273007276814336)追问：AI Coding 习惯及代码质量保证？】【[快手 - Agent 开发岗（应用落地 + AI 工具）](https://www.nowcoder.com/discuss/926274020192841728)追问：如何确保 AI 生成代码逻辑可靠？；AI 编码工具（Cursor/Codex）如何协作及保证代码质量？】【[要务科技-面筋](https://www.nowcoder.com/discuss/926539013991796736)追问：如何让AI写业务代码？】【[作业帮一面 9.5](https://www.nowcoder.com/feed/main/detail/21ca46108ebf479fb8056c6e9f61d42f)追问：之后怎么保证代码质量？怎么验证？还有别的机制吗？】
10. 如何解决大模型 API 服务的响应延迟？ — 字节实习一面 【视频面经同题：提升模型响应速度的优化方向】【小红书数据库智能化二面追问：产品层面的等待体验优化】【小舒一面追问：异步调用与线程阻塞】【[互联网金融 Agent 开发三面](https://www.nowcoder.com/feed/main/detail/88c55ee65af04ac98c218b9d17c47a71)】【[9/4泰隆一面](https://www.nowcoder.com/feed/main/detail/738ff92bcd9049c5afc32d8f63226b79)追问：如何提高大模型响应速度？】
11. 什么是 SDD？它和 Skills 有什么区别？ — 蚂蚁一面【[字节 AI Agent 开发岗一面](https://www.nowcoder.com/discuss/926273296180547584)追问：如何将 Spec-Driven Development 与 Agent 结合？】【[DeepSeek Harness 方向面试](https://www.nowcoder.com/discuss/925527442863714304)追问：Spec-driven development 在 AI 时代如何与 Agent 结合？】
12. AI Coding 产品怎么测试？ — 蚂蚁二面
13. LangGraph 定义的搜索节点做不到并发执行吗？ — AI工程师面试
14. PostgreSQL 的索引结构？Checkpoint 场景如何用索引加速？ — AI工程师面试
15. 用 Claude Code 做长任务，session 跑不完怎么办？ — AI工程师面试
16. 分布式限流算法——令牌桶、漏桶、滑动窗口 — 快手一面
17. 布隆过滤器的原理？误判率如何控制？ — 快手一面
18. 数据库索引失效的常见场景？LIKE 查询？ — 快手一面
19. 大规模数据处理场景设计——千条到百万级 — 快手一面
20. AI 应用中 SSE 流式数据怎么处理？数据格式是什么？ — 百度实习一面【[字节agent一面](https://www.nowcoder.com/feed/main/detail/612a1c20eea744a288b142f5b43f57e1)追问：SSE 在项目里用来做什么？推送的数据格式是什么样？】【[百度Agent一面](https://www.nowcoder.com/feed/main/detail/72858aade19d443facc870fea8bb134f)追问：有流式输出吗？具体的流式响应是怎么处理的？】
21. 针对包含 3 个以上工具调用且高频请求的任务，如何压低端到端延迟？ — 淘天一面【[字节跳动9.3 Agent开发一面面经](https://www.nowcoder.com/discuss/925342611194286080)追问：如何解决上述长程任务运行延迟问题？】
22. 开发 Agent 的时候，你用的是什么开发流程？ — 字节实习一面【[阿里云 SOC Agent Infra 一面](https://www.nowcoder.com/feed/main/detail/1bde9ba913d74ca6847962f679865f7e)】
23. 任务执行远大于单次 Token 限制时，如何设计断点继续生成？ — 淘天一面
24. AI 应用的前端资源缓存怎么配的？ — 百度实习一面
25. AI Coding 检查错误的时间比自己写还长，怎么提效？ — 字节实习二面【[拼多多 复活赛 一面](https://www.nowcoder.com/feed/main/detail/2109cf8eb0254507911fbf86bcbf51e4)追问：日常 coding 或改策略往往是不确定的事情，怎么让 Agent 提效？】
26. 数据量和 QPS 增大后，Agent 架构怎么改进？硬件和 GPU 怎么选？ — 阿里国际二面
27. 使用 LangGraph 开发 Agent，遇到最大的困难是什么？ — bilibili AI研发实习一面
28. Agent 系统的缓存选型——本地缓存 vs Redis — 字节实习二面
29. 模型离线 AUC 很高但上线后效果暴跌，怎么排查？ — 淘宝闪购一面
30. 高并发场景同时调 10 个 Embedding 接口，asyncio.gather vs 多线程的资源优势？ — 淘天AI应用开发一面
31. Agent 异步任务管线中引入消息中间件（Kafka），会不会反而变慢或成为瓶颈？扫表 vs 消息驱动选型 — 淘天Agent开发
32. 用 AI Coding 工具写代码达不到预期怎么办？ — CVTE AI应用工程师一面
33. LangGraph 的 State Snapshot（状态快照）机制是怎么实现的？ — 快手AI应用开发算法一面
34. Agent 系统可观测性设计——怎样的结构才能更好地追踪整个 Trace？ — 美团Agent开发（智能客服方向）二面 【懂车帝 Agent 开发一面追问：Trace、日志、指标和配置版本联合归因】【阿里 Agent Infra 一面题库同题：Agent Trace 字段与成功率突降排查】【[阿里千问 Agent 开发一面](https://www.nowcoder.com/feed/main/detail/463438ee0d9e403b98e8578a05ba4e3f)】【[百度 Agent 二面](https://www.nowcoder.com/feed/main/detail/bca7dc14bd654e91b89792608111b211)】【[阿里巴巴（阿里云）- Agent Infra](https://www.nowcoder.com/discuss/926273487512113152)追问：如何设计 Agent 全链路追踪（Trace）和可观测性（Metrics）？】【[百度Agent一面](https://www.nowcoder.com/feed/main/detail/72858aade19d443facc870fea8bb134f)追问：用户的一次请求在最终的 Trace 展示上是什么形式？Trace 具体怎么用，会做分析吗？】【[格物致信（一面过，二面线下拒）](https://www.nowcoder.com/feed/main/detail/f68f0d54184944c391e0d7b6d1bb82c8)追问：Agent很容易变成黑盒，任务失败你如何做可观测性？】
35. SSE 流式输出中断后如何保证之前的输出不丢失？ — 某教育agent开发 【视频面经追问：用户中途关浏览器后内容保留与恢复】【[字节跳动 - AI Agent 开发岗（工程方向）](https://www.nowcoder.com/discuss/926273296180547584)追问：如何设计 SSE 流式输出网关，处理断线重连和消息重放？】【[百度 - Agent 研发岗（架构方向）](https://www.nowcoder.com/discuss/926273622006665216)追问：如何设计 SSE 流式网关，处理断线重连和消息重放？】
36. Agent 如何做版本管理与灰度？ — Agent面经八股系列【[蚂蚁 Agent 开发一面](https://www.nowcoder.com/feed/main/detail/39451cad5d2245b491d16778f2a9ca01)】
37. 怎么设计一个大模型网关系统？ — 猎豹移动Agent全栈开发【[阿里淘天一面](https://www.nowcoder.com/feed/main/detail/a32b3c75644e4994933a38e1dfb16bc1)】
38. 产品的用户量、每日 token 消耗和底层模型选型怎么估算？ — 快手AI应用开发一面
39. Claude Code 用久了感觉响应越来越慢，这是什么原因？怎么解决？ — 字节TikTok AI应用开发一面
40. 如何设计 Agent 的流式输出以提升用户体验，特别是包含工具调用和多次大模型交互时？ — Agent开发八股合集（南京大学）【[阿里千问 Agent 开发一面](https://www.nowcoder.com/feed/main/detail/463438ee0d9e403b98e8578a05ba4e3f)】
41. 高并发场景下，如何设计 Agent 服务的弹性伸缩策略？ — 已有正文（补录索引）
42. 流式返回时，如何插入非文本事件（工具调用标记、思考过程、错误提示），且不影响前端渲染？ — 牛客Agent面经汇总
43. SSE 和 WebSocket、单次调用的区别是什么？Agent 场景该怎么选？ — 成都agent面试（社招）【阿里 Agent Infra 一面题库同题】【[阿里淘天一面](https://www.nowcoder.com/feed/main/detail/a32b3c75644e4994933a38e1dfb16bc1)】
44. AgentState 的作用是什么？为什么不使用全局变量？ — 字节Agent开发一面
45. 系统里多租户隔离是怎么实现的？ — 视频面经汇总（新增）【阿里 Agent Infra 一面题库同题：数据、资源与权限隔离】【[字节跳动 - AI Agent 开发岗（工程方向）](https://www.nowcoder.com/discuss/926273296180547584)追问：如何设计多租户隔离，包括状态和知识库隔离？】【[百度 - Agent 研发岗（架构方向）](https://www.nowcoder.com/discuss/926273622006665216)追问：如何实现多租户状态与知识库隔离？】【[百度Agent一面](https://www.nowcoder.com/feed/main/detail/72858aade19d443facc870fea8bb134f)追问：不同用户之间是怎么隔离的？】
46. 从原始诉求到可执行 PRD/Spec，如何清洗需求、判断完备性并设置质量门禁？ — 电商库存一面、小得盈满一面（新增）【[字节中国交易与广告 AI 全栈二面](https://www.nowcoder.com/feed/main/detail/0f77410f8b1b4daca879d5ff99c7ae07)】【[蚂蚁 Agent 开发一面](https://www.nowcoder.com/feed/main/detail/39451cad5d2245b491d16778f2a9ca01)】
47. 多模型如何动态路由？根据视频特征、任务特征、成本、延迟和效果选模型？ — 商汤大模型算法应用实习二面（新增）【[百度Agent一面](https://www.nowcoder.com/feed/main/detail/72858aade19d443facc870fea8bb134f)追问：模型路由的依据是什么？】【[作业帮秋招一面](https://www.nowcoder.com/feed/main/detail/c86c7591ba9d47b696774ddb48cdc9cb)追问：从大模型切到小模型主要是为了响应时长吗，实际效果对比大模型怎么样？】
48. 了解 Kubernetes 吗？在 Agent 项目里有没有实际用到？ — 视频面经汇总（新增）【[百度 Agent 二面](https://www.nowcoder.com/feed/main/detail/bca7dc14bd654e91b89792608111b211)】
49. LangGraph 图状态机里，怎么捕获每个节点的执行结果并实时推前端？ — 淘天AI Agent一面（新增）【[深圳tuitti视界之外实习一面](https://www.nowcoder.com/feed/main/detail/9b1329caf4b64389a0ab666585bda045)追问：能否完整描述这个图、图上的状态，以及每个节点的执行过程？】
50. 如何记录 Agent 的非确定性边界，实现可重复的故障回放？ — 腾讯互娱全栈开发（AI）二面（新增）【字节火山引擎 Managed Agent 一面追问：耗时、Token、结果和失败路线】
51. 进程、线程、协程有什么区别？什么场景下协程更有优势？ — 视频面经汇总（新增）
52. 子 Agent 和工具调用的 Token 用量统计缺失，怎么做容错补偿？ — 深信服AI全栈开发二面（新增）
53. 多个子 Agent 延迟退出，同时更新同一对话的 Token 统计数据，线程竞争怎么解决？ — 深信服AI全栈开发二面（新增）
54. Agent 框架如何实现流式并行？了解 Claude Code 的流式并行是怎么做的吗？ — 广州某小厂Agent后端开发二面（新增）
55. Redis 在 Agent 系统中适合承担哪些职责，哪些数据不应只放 Redis？ — 点点互动Agent开发秋招一面（新增）
56. 什么是死锁？死锁产生的条件、检测和解决方法是什么？ — 小红书 Agent 岗一面（新增）
57. 编译器从源代码到可执行程序经历哪些阶段？ — 小红书 Agent 岗一面（新增）
58. 在浏览器输入一个 URL 到页面显示，完整经历了哪些过程？ — 小红书 Agent 岗一面（新增）
59. 云端 Agent 的沙盒应该常驻还是按任务创建？如何优化启动和通信开销？ — 顺极 Agent开发二面（新增）
60. 如何设计同时兼顾吞吐、首 Token 延迟和租户公平性的推理调度器？ — 智象未来 AI Infra一面（新增）
61. Agent 的中间与最终交付物应该如何版本化、校验和交接？ — 福田 FDE线下面试（新增）
62. 多模型供应商如何抽象统一 Provider，而不丢失差异能力？ — 成都晓多科技 Agent开发岗二面（新增）
63. 如何可靠采集 Coding Agent 轨迹，避免崩溃或异步退出时丢数据？ — MiniMax平台研发一面（新增）
64. 自动回滚阈值如何设置，避免固定阈值误杀或放过回归？ — [深信服 Agent 三面](https://www.nowcoder.com/feed/main/detail/b64e8fddbfc642ec9aa33bcdb9aab9aa)（2026-08-23）
65. 如何设计类似 LangFlow 的 Agent 工作流可视化编排画布？ — 商汤 AI Agent 开发面经（新增）
66. 接入多个外部 Agent 时，如何用 Adapter 统一异构事件、工具调用和生命周期协议？ — 北京 B 端 AI 小厂面经（新增）

67. 如何统计 Agent 各模块耗时并定位瓶颈？ — [寒武纪AI应用开发一面&二面](https://www.nowcoder.com/feed/main/detail/64868531af8d424b8aa55f46e313b478)
68. 如何估算 Agent 使用模型的月度成本？ — [汇川技术一面](https://www.nowcoder.com/feed/main/detail/6a241d73effc4540a857a752d987a6f8)
69. 大型项目重构如何规划，如何处理模块正交与冗余？ — [阿里控股 AI全栈开发 二面](https://www.nowcoder.com/feed/main/detail/a11a3a9e0d824969b44db5bb2149ef9f)


## 08-prompt-engineering（30题）

1. 提示词模板是怎么构建的？ — 抖音一面
2. Skills 的原理有没有了解过？ — 蚂蚁一面 【高德实习一面追问：Skill 的本质理解】【蚂蚁Agent开发一面追问：创建 Skill 的方式（除自然语言描述外）】【小红书AI应用开发同题：Skills了解+如何管理】【CVTE AI应用工程师一面追问：怎么理解 Skill？能解决什么问题？怎么写 MCP？】【科大讯飞一面追问：写Skills和写提示词的区别与共同点】
3. Claude Code 的架构有什么比较创新的设计？ — 蚂蚁一面 【高德实习一面追问：从源码角度看设计哲学】
4. 如果让你从零设计一个 Skill 系统，需要实现哪些核心能力？ — 字节实习一面 【蚂蚁AI应用开发二面追问：单一 Skill 模块设计思路】【字节抖音一面追问：手撕 Skill 注册/发现/调用实现】【阿里国际AI应用开发二面追问：多Skill可见时执行顺序保证+Plan模式协调】【阿里国际大模型应用开发一面追问：Skill自我迭代机制+质量评测】【字节火山引擎 Managed Agent 一面追问：开发、测试、运维 Skills 组织】【[快手 AI 全栈一面](https://www.nowcoder.com/feed/main/detail/a30242712e8d456c839ff4223470f491)】【[阿里巴巴- Agent 开发岗（一面）](https://www.nowcoder.com/discuss/925162488314765312)追问：如何设计一个 Skill 注册中心，支持动态加载、版本管理和权限控制？】
5. 为什么已经有了 MCP，Anthropic 还要做 Skill？Skill 里面有没有工具？ — 字节实习一面【[pdd agent 一面](https://www.nowcoder.com/feed/main/detail/ee971b755cbd475a91ef62cee38cdac8)追问：早期流行MCP，现在大量转向Skill，背后的原因是什么？】
6. 一个好的 Prompt 和一个差的 Prompt 的区别？ — 蚂蚁一面
7. LobeChat 的插件和 Claude Code 的 Skills 有什么本质区别？ — 字节实习二面
8. Skill 的渐进式披露怎么实现？Skill 之间的沙箱隔离和通信机制是什么？ — 快手AI应用开发一面【[OPPO IT 开发一面](https://www.nowcoder.com/discuss/923561467092160512)】【[要务科技-面筋](https://www.nowcoder.com/discuss/926539013991796736)追问：Skill的渐进式披露概念了解吗？】【[pdd agent二面](https://www.nowcoder.com/feed/main/detail/f5e7351df8364147ac8da085b99d9d18)追问：Agent怎么实现不同任务的隔离？】
9. Harness Engineering 是什么？它如何演进的？ — CVTE AI应用工程师一面【[抖音电商Agent全栈开发工程师一面](https://www.nowcoder.com/discuss/925066865183858688)追问：你怎么看 Harness 工程？】【[字节跳动9.3 Agent开发一面面经](https://www.nowcoder.com/discuss/925342611194286080)追问：你如何理解Agent中Harness的概念？】
10. 通常 Prompt 包含哪些结构？ — 淘宝闪购一面 【视频面经同题：一个完整Prompt通常包含哪些部分】
11. 什么是一个好的提示词？如何做好提示词的评估？ — 科大讯飞AI一面【[要务科技-面筋](https://www.nowcoder.com/discuss/926539013991796736)追问：如何设计提示词让AI讲产品卖点？】
12. 在调优 Prompt 时，你有哪些实战经验？如何利用 AI 辅助自己优化 Prompt？ — 字节二面
13. 用户的某个需求，你会沉淀为 Skill 还是长期记忆？判断标准是什么？ — 字节TikTok AI应用开发一面
14. DSPy 是什么？它在 Agent 提示词优化和流程构建上有什么优势？ — Agent开发八股合集（南京大学）【[钉钉一面](https://www.nowcoder.com/discuss/923765750446202880)】
15. 一个 Skill 写得好不好，应该看哪些评价标准？ — 视频面经汇总（新增）【[快手 AI 全栈一面](https://www.nowcoder.com/feed/main/detail/a30242712e8d456c839ff4223470f491)】
16. Prompt 层面让模型回答更快、更稳定的方法？ — 视频面经汇总（新增）
17. OpenSpec/Spec 驱动开发与普通开发流程有什么区别？如何治理 Spec 过期？ — 浦金科一面、电商库存一面（新增）【[蚂蚁 Agent 开发一面](https://www.nowcoder.com/feed/main/detail/39451cad5d2245b491d16778f2a9ca01)】【[OPPO IT 开发一面](https://www.nowcoder.com/discuss/923561467092160512)】【[字节 AI 应用开发二面](https://www.nowcoder.com/feed/main/detail/7e8a821479a649fd914e449d312eeb95)】
18. 如何给 Agent 工具系统设计动态 Skill，而不让版本升级破坏历史任务？ — 关于skill的面试问题（新增）【[〔社招〕〔面经〕9月初XX科技(中厂) AI全栈工程师（Agent应用）一面 挂](https://www.nowcoder.com/discuss/926232883432296448)追问：Skill 里哪些是固定、哪些随观察动态调整？】【[美团 - Agent 开发岗（场景设计方向）](https://www.nowcoder.com/discuss/926273749555376128)追问：Agent 插件系统热插拔 Skill？】
19. Skill 的 Prompt 配置上线后出错，如何快速止损和修复？ — 百度秋招后端一面 【[拼多多 AI 全栈两轮技术面](https://www.nowcoder.com/discuss/921104232256675840)追问：Prompt 模板的版本、测试和灰度】
20. 团队里的 Skill 数量持续膨胀，如何治理重复能力、路由冲突和上下文占用？ — [电商 Agent 三面](https://www.nowcoder.com/feed/main/detail/b6b453976c2d4e43a872054d695c2fe2)【电商库存二面（2026-08-17）】
21. Skill 分层体系怎么设计？为什么这么分层？ — 字节跳动Agent二面（Coding Agent）（新增）
22. 动态 Prompt 和静态 Prompt 有什么区别？各自在什么场景下用？ — 字节跳动Agent二面（Coding Agent）（新增）
23. 如果让你设计一个代码审查的 Skill，你会如何设计？ — 最有料AI实习生面经（新增）
24. 如果 Agent 挂 100 个 Skill，如何提升召回率、准确度、F1 综合值？ — 关于skill的面试问题（新增）
25. Skill 和 Agent 的关系，为什么不用 Skill 而用子 Agent？ — AI应用开发进阶面（新增）
26. 为什么 Coding Agent 的 Skills 通常放在 System 上下文，而不是用户 Query 中？ — 文心一言实习一面（新增）
27. 如何让 Agent 自动沉淀 Skill，同时保证生成的 Skill 准确、无害且不会无限膨胀？ — 电商库存二面（新增）
28. 为什么一个很短的 Skill 也可能有效？如何验证效果来自哪里？ — [OPPO AI 全栈一面](https://www.nowcoder.com/discuss/920830730643443712)（2026-08-23）
29. 可演进能力为什么应封装为 Skill，而不是不断塞进 Prompt？Skill 的知识进化流水线如何治理？ — 小红书 Agent开发实习一面（新增）
30. Skill 的多后端可插拔加载应该如何设计？ — [阿里边缘 BU 一面](https://www.nowcoder.com/feed/main/detail/bdebbb6088b6405e9eb2bd2c345acb6e)（新增）

## 09-rag-retrieval（73题）

1. 多维度的查询改写是什么？ — 抖音基础架构 Agent 一面【淘天一面追问：改写为何提升精准度的底层原理】【[美团 Agent 开发一面](https://www.nowcoder.com/feed/main/detail/58159306df52463ab75d72daa80d66df)追问：短 Query 与长 Chunk 的非对称召回】【[阿里巴巴（淘天）- 大模型算法岗（搜推方向）](https://www.nowcoder.com/discuss/926272464059891712)追问：淘宝搜索中如何用大模型做 Query 理解和改写？】【[美团 - Agent 开发岗（场景设计方向）](https://www.nowcoder.com/discuss/926273749555376128)追问：RAG 召回不相关时 Query Rewrite 优化举例？】
2. RAG 的检索如何实现？ — 阿里一面【[钉钉一面](https://www.nowcoder.com/discuss/923765750446202880)】
3. 并行化意图识别是什么？ — 抖音一面
4. 讲一下项目里召回的流程 — 抖音一面
5. RAG 召回了矛盾文档，Agent 怎么处理？ — 腾讯二面
6. Embedding 和 ReRank 模型具体怎么微调？ — 腾讯AI应用开发 【腾讯AI应用开发一面追问：重排序完整实现流程】【爱奇艺大模型算法追问：Embedding模型与Reranker训练Loss区别】
7. RAG 检索到文档很多但回答质量差，怎么排查？ — 携程实习一面 【Shopee/Momenta Agent 一面同题：高召回但最终答案准确率低】
8. RAG 为什么需要向量检索？和关键词检索的本质区别？ — 蚂蚁一面【[拼多多 复活赛 一面](https://www.nowcoder.com/feed/main/detail/2109cf8eb0254507911fbf86bcbf51e4)追问：关键词 / 倒排这种方式有明显局限，比如“苹果”和“apple”可能匹配不上，你们怎么看？】【[百度Agent一面](https://www.nowcoder.com/feed/main/detail/72858aade19d443facc870fea8bb134f)追问：BM25 和向量检索分别解决什么类型的问题？】
9. 什么是余弦相似度？在 RAG 中做什么？ — 携程实习一面【[9.4 某小厂 AI Agent hr+技术面](https://www.nowcoder.com/feed/main/detail/10b2fcaf73d2401f8636bd0459e1cd08)追问：在向量检索召回阶段，度量 Query 与文档向量相似度的常用算法是什么？】
10. 什么是嵌入（Embedding）？为什么需要向量化？ — 携程实习一面 【小红书AI应用开发追问：Embedding本质+每个维度含义+Sparse Embedding】
11. 双路召回的 TopK，K 是如何确定的？ — 腾讯AI应用开发
12. 如何向非技术人员解释 RAG？ — 携程实习一面
13. 如何快速上手一个没接触过的技术？ — 携程实习一面
14. RAG 中如何提高文档召回率？ — 蚂蚁一面
15. 全量生产文档做关联性检索，有没有更高效的方案？ — 蚂蚁二面
16. 渐进式披露架构下还需要 RAG 吗？ — 蚂蚁二面
17. RAG 在 Agent 体系里是工具、记忆还是推理前置步骤？ — 30题
18. 检索结果质量参差不齐，控制点放在哪？ — 30题
19. 什么时候一次检索多次使用，什么时候边执行边检索？ — 30题
20. RAG 返回过时信息，怎么降低 Agent 被误导的概率？ — 30题
21. 为什么引入BM25？和向量检索怎样组合？ — 快手一面 【高德实习一面追问：更广义的多路检索策略】【淘天一面追问：RRF K参数调优 + 长尾查询优化】【淘天AI应用开发一面追问：基于Milvus的BM25与向量分数归一化】【字节二面同题：多路检索 + 向量/关键词各解决什么】【淘天Agent开发同题：为什么加BM25+具体解决了什么bad case】【视频面经同题：讲一下你的召回和重排策略】【钉学科技 FDE 实习一面追问：双路短板、融合与分类 bad case 验证】【[9.4 某小厂 AI Agent hr+技术面](https://www.nowcoder.com/feed/main/detail/10b2fcaf73d2401f8636bd0459e1cd08)追问：在混合检索中，除了向量语义检索，常结合的基于关键词词频与文档相关性的检索算法是什么？】【[虾皮Agent一面](https://www.nowcoder.com/feed/main/detail/409dc8793a7b450eb51ee32c2b923d49)追问：BM25 检索结果和向量检索结果，两套数据如何做结果融合？】
22. 如何系统性提升 RAG 的检索相关度与生成效果？ — 快手一面 【淘天一面追问：实际召回不准的排查改进方法论】【视频面经同题：做知识检索时怎么提高模型最终回答准确率】【[抖音电商Agent全栈开发工程师一面](https://www.nowcoder.com/discuss/925066865183858688)追问：底层检索做了哪些提升？】
23. Rerank 后返回几个块？TopK 截断策略？ — 快手一面 【字节二面追问：Re-rank 的作用 + 为什么有了向量相似度还需要它】【淘天Agent开发追问：低分阈值提前过滤策略】
24. RAG 中为什么引入父子索引？ — 快手一面
25. RAG 系统的端到端性能如何优化？ — 快手一面
26. 分块策略怎么设计？不同策略的优缺点？ — 高德 AI 应用开发实习一面【腾讯AI应用开发二面追问：chunk 边界修正 + 表格跨块修复】【字节AI一面追问：领域文档语义感知切片】【Shopee 一面追问：为什么不能只按固定 Token 数切分】【[字节数据平台 Agent 一面](https://www.nowcoder.com/feed/main/detail/f5f840632a19417b91b8987762427a6a)追问：跨物理页 Chunk 与页码引用】【[钉钉一面](https://www.nowcoder.com/discuss/923765750446202880)】【[虾皮Agent一面](https://www.nowcoder.com/feed/main/detail/409dc8793a7b450eb51ee32c2b923d49)追问：文档分块具体采用什么分块策略？；除递归字符切分外，还有哪些文档分块方案？】【[百度Agent一面](https://www.nowcoder.com/feed/main/detail/72858aade19d443facc870fea8bb134f)追问：Chunk 太大或太小有什么影响？Chunk 大小怎么确定？】
27. GraphRAG 在处理 Agent 复杂关联查询时的优势在哪里？ — 淘天一面 【蚂蚁AI应用开发二面同题：GraphRAG 理解与应用】【蚂蚁AI应用开发二面追问：Self-Reflection/CoT 噪声过滤】【腾讯AI应用开发二面追问：三元组抽取幻觉控制 + Community Summary 设计】【字节二面追问：多跳推理/复杂逻辑查询场景下RAG架构优化】【币安AI大模型实习一面追问：叶子节点在智能客服中如何触发】
28. 知识库整体怎么设计？从文档接入到检索的完整架构 — 高德 AI 应用开发实习一面【字节二面同题：RAG 完整流程从文档切块到生成】【阿里 Agent Infra 一面题库同题】【[百度 Agent 二面](https://www.nowcoder.com/feed/main/detail/bca7dc14bd654e91b89792608111b211)】【[拼多多 复活赛 一面](https://www.nowcoder.com/feed/main/detail/2109cf8eb0254507911fbf86bcbf51e4)追问：聊聊你们知识库是怎么设计的？怎么检索的？】【[虾皮Agent一面](https://www.nowcoder.com/feed/main/detail/409dc8793a7b450eb51ee32c2b923d49)追问：讲下项目里 RAG 的整体实现流程。】
29. RAG 召回数据层应如何设计文档、Chunk、Embedding、版本和权限 Schema？ — [Newegg AI 软件工程实习一面](https://www.nowcoder.com/discuss/920719616005898240)（新增）【[拼多多 复活赛 一面](https://www.nowcoder.com/feed/main/detail/2109cf8eb0254507911fbf86bcbf51e4)追问：如果文档都做倒排或索引，怎么同时解决切分和权限问题？】
30. 向量数据库怎么选型？不同规模下该用什么方案？ — 阿里国际二面 【淘天Agent开发追问：为什么选pgvector】【[中兴软开一面](https://www.nowcoder.com/feed/main/detail/0b39815babfb47108464ffabdf929eba)】【[钉钉一面](https://www.nowcoder.com/discuss/923765750446202880)】
31. Embedding 模型怎么选？选型时考虑哪些因素？ — 高德实习一面
32. 为什么 Claude Code 不用 RAG 检索代码，而是直接用 grep？ — 字节实习一面
33. Coding Agent 应从代码反向理解领域知识，还是维护独立知识库/规则库？ — [国际业务 Agent 二面](https://www.nowcoder.com/feed/main/detail/b163baeb304e432d9b4c9c218ed467fa)（新增）
34. 升级 Embedding 模型后，怎么保证索引和检索向量的逻辑一致性？ — 阿里国际二面
35. 图检索、向量检索、混合检索有什么区别？怎么选？ — 腾讯AI应用开发二面【[字节 AI 应用开发二面](https://www.nowcoder.com/feed/main/detail/7e8a821479a649fd914e449d312eeb95)】【[百度Agent一面](https://www.nowcoder.com/feed/main/detail/72858aade19d443facc870fea8bb134f)追问：为什么选择混合召回？】【[作业帮秋招一面](https://www.nowcoder.com/feed/main/detail/c86c7591ba9d47b696774ddb48cdc9cb)追问：RAG 是多路检索吗，单路检索能不能做、能不能解决业务问题？】
36. RAG 架构与模型微调（Fine-tuning）相比，各自的适用场景和优缺点是什么？ — 字节二面 【淘天转正实习一面追问：预训练语料已包含相关知识为什么还要RAG】【[字节二面（Trae）](https://www.nowcoder.com/discuss/924821959647440896)追问：RAG 主要用来做什么？】
37. 如何处理 RAG 过程中的权限隔离和时效性问题？ — 字节二面【[阿里千问 AI 应用研发一面](https://www.nowcoder.com/feed/main/detail/da6d74a34ceb4e52b9b4fbcac25cfb3b)追问：文档/Chunk ACL、缓存与引用泄露】【[拼多多 复活赛 一面](https://www.nowcoder.com/feed/main/detail/2109cf8eb0254507911fbf86bcbf51e4)追问：你们把内部文档给 Agent 用，有没有考虑过泄露问题？】
38. 向量数据库索引中 IVF_FLAT 和 HNSW 的区别？各自适合什么场景？ — 快手AI应用开发算法一面【[阿里巴巴（淘天）- 大模型算法岗（搜推方向）](https://www.nowcoder.com/discuss/926272464059891712)追问：向量检索中 IVF 与 HNSW 的选型依据是什么？】【[全栈实习一面，20分钟居然问这么细😂](https://www.nowcoder.com/feed/main/detail/4af1e257116e4e36970c6e0d8bf2f70e)追问：你的 RAG 向量数据库用的索引是什么？】
39. Deep Research 在代码层面是怎么实现的？和普通 RAG 有什么区别？ — bilibili AI研发实习一面【字节火山引擎 Managed Agent 一面追问：Auto Research】
40. RAG 知识库的噪声剔除和文档去重怎么做？ — 腾讯AI应用开发二面 【淘天Agent开发追问：防止AI批量生成虚假数据投毒】
41. PDF 解析用什么工具？Layout-aware Parsing 是怎么做的？ — 腾讯AI应用开发二面
42. 多模态 Embedding 检索中，文本与图片权重怎么平衡？图纸参数召回不准的根因？ — 淘天AI应用开发一面
43. 向量数据库的标量条件过滤怎么做？Pre-filter vs Post-filter 的区别？ — 淘天AI应用开发一面
44. Agentic RAG 是什么？和传统 RAG 的核心区别？ — 美团Keeta一面
45. 补充检索是如何评估数据质量并触发的？怎么保证二次检索能搜到之前没搜到的内容？ — 淘天Agent开发
46. RAG 检索到的 Chunk 不足以回答问题，后续怎么处理？ — 字节大模型测开一面
47. 向量数据库里两个同义词是什么关系？完全同义的词会在同一个点上吗？ — 字节大模型测开一面
48. RAG 过程中如何处理文件里的图片？ — 字节暑期agent实习二面【[PDD Agent三面](https://www.nowcoder.com/feed/main/detail/9908477cdd4041fabacbfbf02febb13c)追问：RAG如果存在图片类非文本内容，如何处理？】
49. 如何避免模型回复过度依赖检索到的外部知识，导致回答生硬、缺乏共情能力和自然度？ — 阿里淘天AI Agent应用开发二面
50. 随着大模型上下文窗口持续扩容（100K→1M+），传统 RAG 技术是否会被完全替代？ — 阿里淘天AI Agent应用开发二面
51. 从 ES 切换到向量检索，哪些能力会下降，哪些会提升？ — 字节跳动Agent开发实习生一面
52. 父文档是怎么得到的？语义切分具体是怎么做的？聚类后怎么区分不同文档？ — 同程Agent开发实习一面【[百度Agent一面](https://www.nowcoder.com/feed/main/detail/72858aade19d443facc870fea8bb134f)追问：为了保证连续语义，文本具体怎么切分？有什么算法？】
53. RAG 项目里 MySQL 和 Elasticsearch 的数据一致性怎么保证？ — 视频面经汇总（新增）
54. 手动干预切片是怎么做的？为什么需要这一步？ — 视频面经汇总（新增）
55. Text2SQL 的 RAG 架构里，DDL 层和规则层分别解决什么问题？业务表频繁变更时怎么保持可用？ — 已有正文（补录索引）【[OPPO IT 开发一面](https://www.nowcoder.com/discuss/923561467092160512)】
56. 笔试题：多路召回结果合并去重 + 加权排序 + TopK — 已有正文（补录索引）【[作业帮秋招一面](https://www.nowcoder.com/feed/main/detail/c86c7591ba9d47b696774ddb48cdc9cb)追问：两路检索得到的召回结果如何做结果融合？】
57. RAG 文档切分中遇到代码块、表格、标题等特殊内容怎么处理？ — 最有料AI实习生面经（新增）【[虾皮Agent一面](https://www.nowcoder.com/feed/main/detail/409dc8793a7b450eb51ee32c2b923d49)追问：PDF 电子表格如果很长、超出 chunk 长度，切分时会从表格中间截断吗？截断后如何避免表格行数据残缺带来的问题？】【[阿里边缘bu 秋招一面 （已过）](https://www.nowcoder.com/feed/main/detail/bdebbb6088b6405e9eb2bd2c345acb6e)追问：同一文档中的两个表格存在逻辑关联时，应该如何切分和维护这种关联？】
58. 处理一万个长文档构建 RAG 知识库，工程上怎么做？ — 阿里Agent面经·场景题（新增）
59. RAG 知识库更新怎么不停服？热更新方案怎么设计？ — 腾讯AI应用开发（新增）【[抖音电商Agent全栈开发工程师一面](https://www.nowcoder.com/discuss/925066865183858688)追问：更新是每天全量跑一遍吗？】
60. 混合检索到底在哪个环节比单独用效果好？ — 淘天AI Agent一面（新增）【[百度Agent一面](https://www.nowcoder.com/feed/main/detail/72858aade19d443facc870fea8bb134f)追问：有没有通过实验分析向量检索及混合检索带来的提升？】
61. 知识图谱如何从文档构建、增量维护，并处理实体与关系冲突？ — 阿里云暑期 Agent 面经（新增）【[抖音电商Agent全栈开发工程师一面](https://www.nowcoder.com/discuss/925066865183858688)追问：知识构建与图谱抽取怎么做？；更新时实体抽取和关系关联怎么处理？】
62. MMR 为什么还能提高效果？重排后为什么还要设置 MMR 截断？ — 深势科技一面（新增）
63. 基于关键词的命令行代码搜索与基于 Embedding/RAG 的代码搜索，各有什么优缺点？ — 某小厂FOSHO AI应用开发二面（新增）
64. 知识库持续更新时，如何保证一次 RAG 回答读取同一逻辑快照？ — 腾讯互娱全栈开发（AI）二面（新增）
65. 如何设计支持版本过滤和时间旅行查询的向量索引？ — 腾讯互娱全栈开发（AI）二面（新增）
66. RAG 如何防止引用漂移和跨版本证据拼接？ — 腾讯互娱全栈开发（AI）二面（新增）
67. RAG 前端如何展示长文档，并让引用稳定跳转到原文证据？ — 商汤 AI Agent 开发面经（新增）

68. 图召回如何缓解热门内容被过度推荐的问题？ — [28届双非本末9硕 腾讯wxg推荐算法面经](https://www.nowcoder.com/feed/main/detail/19d5ea0eda0e40de8a060ac516703c58)
69. RAG 检索结果如何安全地组装到提示词中？ — [腾讯AI全栈一面](https://www.nowcoder.com/feed/main/detail/5f08a2b54559471aac95ea8009d38403)
70. RAG 组装上下文后，如何选择最终生成模型？ — [腾讯AI全栈一面](https://www.nowcoder.com/feed/main/detail/5f08a2b54559471aac95ea8009d38403)
71. 生成教学蓝图时，如何识别语义歧义和超纲内容？ — [9.7传音控股AI测试开发实习生](https://www.nowcoder.com/feed/main/detail/1c1b97aa3ccb4b2a915eeed85d01107a)
72. 视频没有语音时，如何保持检索效果？ — [阿里 Token Foundry AI应用研发三面面经（三面挂）](https://www.nowcoder.com/feed/main/detail/bfd43b5c66784add8fbf5893c164697a)
73. BGE 类文本 Embedding 模型的基本结构是什么？ — [腾讯音乐面经-腾讯音乐算法岗面经-01](https://www.nowcoder.com/discuss/926677767104532480)


## 10-training-and-data（101题）

1. 构造数据集遇到过什么难点？ — 腾讯AI应用开发【CVTE AI应用工程师一面追问：合成数据集质量达不到预期怎么办】【[字节 Seed 具身数据一面](https://www.nowcoder.com/feed/main/detail/657dfac8ca5c49f28492a1110b95f7cd)追问：标注一致性与自动质检】【[Momenta 大模型算法工程师一面](https://www.nowcoder.com/feed/main/detail/f7518c865e07491cb1518d288698813c)追问：长尾样本对齐】
2. 预训练数据清洗方法？ — 字节一面【[MiniMax - 大模型算法岗（后训练 / SFT / RL 方向，独角兽）](https://www.nowcoder.com/discuss/925527528259743744)追问：数据清洗时，你如何筛选低质量样本？用过哪些启发式规则或模型过滤？】【[MiniMax - 大模型算法岗（后训练 / SFT / RL）](https://www.nowcoder.com/discuss/926272883872075776)追问：低质数据筛选的启发式规则或模型过滤方法？】
3. 自动标注系统的主要难点是什么？如何设计模型预标注、置信度分流和人工复核闭环？ — [字节 Seed 具身数据一面](https://www.nowcoder.com/feed/main/detail/657dfac8ca5c49f28492a1110b95f7cd)（新增）【[百度具身研发一面](https://www.nowcoder.com/feed/main/detail/258695ecdfbb464790fc8ae55c9f1661)追问：标注相关，有做过自动化标注吗？】
4. SFT 数据字段如何映射？instruction 与 input 重叠时如何定义清洗和拼接契约？ — [大方云图研发实习一面](https://www.nowcoder.com/feed/main/detail/a9a40feb4e1e4d0ca7c3f8c3ba67d487)（新增）【[阶跃星辰（Stepfun）- 大模型算法岗（Post-train）](https://www.nowcoder.com/discuss/926273007276814336)追问：SFT 数据中指令与输入字段重叠的处理？】
5. Agent 工具调用怎么训练？训练集包含什么？ — 腾讯二面
6. 训练数据标注粒度应该越细越好还是按任务适配？如何权衡成本、信息量和泛化？ — [字节 Seed 具身数据一面](https://www.nowcoder.com/feed/main/detail/657dfac8ca5c49f28492a1110b95f7cd)（新增）
7. DPO、PPO、GRPO 的区别和优缺点？ — 高频题 【阿里国际一面追问：PPO vs GRPO 深度对比】【淘天AI应用开发一面追问：DPO不需要在线采样的原因+数据格式】【美团Keeta一面追问：chosen/rejected数据生成实操与常见坑】【阿里国际一面追问：重要性采样在策略差异大时失效+GRPO vs PPO KL散度区别】【[快手广告大模型一面](https://www.nowcoder.com/discuss/923996140154953728)】【[MiniMax - 大模型算法岗（后训练 / SFT / RL 方向，独角兽）](https://www.nowcoder.com/discuss/925527528259743744)追问：GRPO 和 DPO 在代码实现上的区别是什么？】【[阶跃星辰（Stepfun）- 大模型算法岗（Post-train）](https://www.nowcoder.com/discuss/926273007276814336)追问：PPO vs GRPO 优劣势？】【[8.13 百度一面挂 百度多模态算法工程师-北京](https://www.nowcoder.com/discuss/926467109717118976)追问：PPO 和 GRPO 的区别是什么？】
8. 微调方法有哪些？LoRA 和全参数微调？ — 高频题 【阿里国际二面追问：微调经验与全流程认知】【淘天AI应用开发一面追问：LoRA A/B矩阵初始化+秩选择+权重Merge】【[百度正式批：一面结束第二天就约二面了](https://www.nowcoder.com/discuss/925108144831725568)追问：你微调具体微调哪一部分，不太可能是全量微调吧？】
9. 给定时间序列，如何用 ML 筛选特征再基于规则建模？ — 字节一面【[OPPO 大模型算法面经](https://www.nowcoder.com/feed/main/detail/685479ec75b542bebf1156c47f1d4e88)追问：组合特征盲点】
10. kernel 级别的优化，CUTE DSL 或手写 CUDA？ — 字节一面
11. XGBoost 相比单棵决策树，在目标函数、正则和集成机制上做了什么改进？ — [OPPO 大模型算法面经](https://www.nowcoder.com/feed/main/detail/685479ec75b542bebf1156c47f1d4e88)（新增）
12. 手撕 Multi-Head Attention — 手撕题【[0907 百度一面 （AI Infra）](https://www.nowcoder.com/feed/main/detail/91f5187146864de5878349a2ecf497ce)追问：你对 AI 算法或模型架构有一定了解吗？Transformer、Attention 如何计算？】
13. 位置编码的作用？ — 高频题 【字节二面同题：QKV机制+为什么引入位置编码和多头注意力】
14. 绝对位置编码和相对位置编码的区别？ — 高频题 【爱奇艺大模型算法追问：RoPE/MRoPE长文本位置编码原理】
15. 常用解决过拟合的方法？ — 高频题
16. LayerNorm 和 BatchNorm 的区别？ — 高频题
17. RLHF 中奖励模型训练数据如何构建？ — 后端AI八股 【快手一面+荣耀一面追问：奖励函数设计逻辑和打分规则】【阿里国际AI应用算法追问：reward hacking 识别与防范】【阿里国际AI算法一面追问：RL训练质量达标判断方法】
18. 大模型推理加速技术有哪些？ — 后端AI八股 【阿里国际二面追问：推理服务部署/算子融合/IO 优化】【阿里国际AI算法一面追问：Flash Attention与稀疏注意力原理】
19. 多模态是怎么实现的？图片怎么编码？ — 后端AI八股 【爱奇艺大模型算法追问：CLIP图文对齐+图像Token冗余解决方案】【[美团 - Agent 开发岗（场景设计方向）](https://www.nowcoder.com/discuss/926273749555376128)追问：多模态（图片）输入与文本的融合方案？】
20. 你了解哪些多模态大模型？ — 蚂蚁一面
21. 有没有了解过端侧部署的模型？ — 蚂蚁一面
22. OCR、多模态模型、YOLO 与 ONNX 分别处于任务、模型和运行时哪个层次？如何组合？ — [北京金蝶二面](https://www.nowcoder.com/feed/main/detail/6edec13bc5f34f0ca137b4a4911dcb10)（新增）
23. 如何优化长文本生成中的显存占用？ — 后端AI八股
24. Transformer 中梯度消失/爆炸怎么解决？ — 后端AI八股
25. Token 过长导致的 Attention 稀释现象为什么会导致 Agent 的指令遵循能力下降？ — 淘天一面
26. 在 Agent 多轮对话任务中，标准 Attention 机制的平方复杂度在工程落地上主要引发了哪些问题？ — 淘天一面
27. SFT、蒸馏、GRPO 的技术选型——什么时候用什么？ — 阿里国际一面 【快手二面追问：SFT为什么不够，什么时候必须上RL】【腾讯金融科技一面追问：蒸馏时防止小模型学到错误推理链】
28. GRPO 的 Loss 函数、Advantages 计算与信用分配机制 — 阿里国际一面 【快手一面+美团一面追问：全0全1 reward处理 + 单步问题是否需要GRPO】【阿里国际一面追问：GRPO训练中观测什么指标】
29. vLLM 的 PagedAttention 原理是什么？解决了什么问题？ — 快手AI应用开发算法一面【[华为 - 大模型算法岗（AI Infra / 训练优化）](https://www.nowcoder.com/discuss/926272625410674688)追问：vLLM PagedAttention 如何解决碎片？】【[阿里巴巴（阿里云）- Agent Infra](https://www.nowcoder.com/discuss/926273487512113152)追问：vLLM 的 PagedAttention 如何解决显存碎片问题？】
30. DP、DDP、TP、PP——分布式训练并行策略的区别与选型 — 荣耀一面【[0907 百度一面 （AI Infra）](https://www.nowcoder.com/feed/main/detail/91f5187146864de5878349a2ecf497ce)追问：大模型中的大矩阵乘法，例如流水线并行或张量并行，你了解吗？】
31. 深度学习网络中的「残差连接」解决了什么问题？其物理含义是什么？ — 字节二面 【淘天Agent开发同题：传统CNN痛点+ResNet核心思想】
32. 什么是灾难性遗忘？微调时如何缓解？ — 字节大模型测开一面【[阶跃星辰（Stepfun）- 大模型算法岗（Post-train）](https://www.nowcoder.com/discuss/926273007276814336)追问：后训练中避免灾难性遗忘的方法？】
33. Text-to-SQL 训练集构建——500 样本覆盖 200+ 查询模式的数据生产流设计 — 淘天一面
34. Token 和字符有什么区别？ — 淘宝闪购一面
35. QLoRA 的核心设计是什么？NF4、双重量化、分页优化器分别解决什么问题？ — 淘天AI应用开发一面
36. 垂直领域微调后，模型通用能力严重退化怎么办？ — 淘天AI应用开发一面
37. 现有的大模型性能为什么这么好？ — 字节二面
38. GQA 和 MLA 的原理是什么？各自解决什么问题？ — 阿里国际AI算法一面
39. MoE 架构下为什么参数量大但单 Token 推理成本不一定高？ — 字节大模型测开一面
40. BF16 与 FP32 精度差异及训练推理选型？ — 爱奇艺大模型算法岗二面
41. 模型推理慢，排查思路是什么？ — 阿里国际AI算法一面
42. 超长上下文是怎么实现的？（如 Kimi 这类模型） — 百度大模型实习
43. Agent 在细分场景（比如法律、医疗）落地时，微调策略和通用场景有什么不同？ — 字节TikTok AI应用开发一面
44. 为什么要通过微调模型来做代码生成？为什么不用纯 Prompt 或 Spec Coding？ — 小米AI Agent一面 【字节Agent开发实习生一面追问：spec coding/SDD为什么达不到Agent效果】
45. 外部模型参数更大，14B 在 Agent 层面会不会不够？ — 小米AI Agent一面
46. Rerank 模型蒸馏的数据是什么样的？训练数据大概有多少条？ — 同程Agent开发实习一面
47. BERT 和 GPT 架构的区别是什么？ — 同程Agent开发实习一面
48. 为什么现在的大模型都是 Decoder-only 架构？ — 淘天AI Agent暑期实习一面
49. 训练 AI Coding Agent，端到端还是分阶段训练？ — 淘天AI Agent暑期实习一面
50. 客服 Agent 奖励函数的 Reward Hacking/稀疏/区分度问题，如何设计新 reward？ — 阿里暑期Agent算法二面【[百度正式批：一面结束第二天就约二面了](https://www.nowcoder.com/discuss/925108144831725568)追问：reward是如何设计的呢？；奖励函数怎么写的？；你的奖励函数具体设计是比较稀疏还是稠密的？】【[MiniMax - 大模型算法岗（后训练 / SFT / RL）](https://www.nowcoder.com/discuss/926272883872075776)追问：RL reward 曲线上升但效果变差的原因是什么？】【[阶跃星辰（Stepfun）- 大模型算法岗（Post-train）](https://www.nowcoder.com/discuss/926273007276814336)追问：Reward Hacking 的检测与纠正？】【[百度 正式批 二面 端到端决策规划控制算法工程师](https://www.nowcoder.com/feed/main/detail/af692c37e31d437292d4881b58b24e56)追问：对于DDPG项目的reward，你是如何设计的？】
51. 多轮对话 Agent 没有现成对话数据，如何从 UI 操作流合成 SFT 训练语料？ — 海底捞大模型面经（新增）
52. 多轮 Agent 的 RL reward 怎么设计？Turn 级信用分配怎么做？ — 海底捞大模型面经（新增）
53. Agentic RL 与普通 LLM RL 的核心差异是什么？ — 腾讯大模型算法岗一二面（新增）【[腾讯（WXG）- 大模型算法岗（一面）](https://www.nowcoder.com/discuss/925163074921709568)追问：智能体强化学习（Agentic RL）与传统 RL 在训练范式和信用分配上的核心差异是什么？】【[字节跳动 - 大模型算法岗（强化学习方向）](https://www.nowcoder.com/discuss/925523582761857024)追问：智能体强化学习（Agentic RL）与传统 RL 在训练范式和信用分配上的核心差异是什么？】【[腾讯（CSIG）- 大模型算法岗（RLHF 与多模态）](https://www.nowcoder.com/discuss/925526785003909120)追问：智能体强化学习（Agentic RL）与传统 RL 在训练范式和信用分配上的核心差异是什么？】【[字节跳动 - 大模型算法岗（RL/后训练方向）](https://www.nowcoder.com/discuss/926272098744438784)追问：智能体强化学习（Agentic RL）与传统 RL 在训练范式和信用分配上的核心差异？】
54. 为什么 Step-level SFT 之后再进行 GRPO，通常比直接从基座模型开始做 GRPO 稳定？ — 唯品会NLP算法实习一面（新增）【[百度正式批：一面结束第二天就约二面了](https://www.nowcoder.com/discuss/925108144831725568)追问：SFT和GRPO是分两阶段的吗？】【[MiniMax - 大模型算法岗（后训练 / SFT / RL 方向，独角兽）](https://www.nowcoder.com/discuss/925527528259743744)追问：SFT 的作用是什么？为什么通常先做 SFT 再做强化学习？】【[MiniMax - 大模型算法岗（后训练 / SFT / RL）](https://www.nowcoder.com/discuss/926272883872075776)追问：SFT 的作用及为何先 SFT 后 RL？】
55. 训练后量化的完整流程是什么？粒度、校准方法和离群值如何共同影响精度？ — 摩尔线程/智谱/百度 AI Infra 面经（新增）
56. GPTQ、AWQ、SmoothQuant 与 AdaQuant 的核心思路有什么不同？ — 智谱/后摩智能/AI Infra 小厂面经（新增）
57. 长时序任务中的 Agent RL 为什么容易训练失稳？如何缓解？ — [字节大模型算法岗](https://www.nowcoder.com/discuss/926272098744438784)、[腾讯 CSIG 大模型算法岗](https://www.nowcoder.com/discuss/925526785003909120)、[腾讯 WXG 大模型算法岗](https://www.nowcoder.com/discuss/925163074921709568)（新增）
58. Agentic CPT、SFT、RL 三阶段分别训练什么能力？ — 字节跳动AI Agent秋招一面（新增）【[阶跃星辰（Stepfun）- 大模型算法岗（Post-train）](https://www.nowcoder.com/discuss/926273007276814336)追问：后训练全链路（数据→SFT→RL）详细介绍？】
59. LoRA 应该挂在哪些层？rank、alpha 和 dropout 如何共同影响效果？ — Shopee 大模型一面（新增）【[阶跃星辰（Stepfun）- 大模型算法岗（Post-train）](https://www.nowcoder.com/discuss/926273007276814336)追问：LoRA 的 rank 值越大越好吗？为什么？】
60. Agentic CFT 与 SFT、RL 的目标有何不同？为什么训练时要 Mask Observation Token？ — [Shopee Agent 开发一面](https://www.nowcoder.com/feed/main/detail/79fe3fc8f8cb4c4d9beca478f4279e3a)（2026-08-24）【[腾讯一面微调 Mask 追问](https://www.nowcoder.com/discuss/924026569318727680)】
61. DAPO 为什么可以不使用额外 KL 惩罚？它如何维持策略更新稳定？ — [字节大模型算法岗](https://www.nowcoder.com/discuss/926272098744438784)、[字节强化学习岗](https://www.nowcoder.com/discuss/925523582761857024)（新增）
62. Tool-use SFT 训练时，长轨迹采用截断、切分还是掩码？如何避免破坏工具依赖关系？ — 唯品会NLP算法实习一面（新增）
63. GRPO 中相对奖励是如何计算的？同一组奖励方差接近零时如何处理？ — 唯品会NLP算法实习一面（新增）
64. Tool-use 轨迹长度与任务复杂度有什么关系？训练数据应如何分布？ — 唯品会大模型算法实习一面（新增）
65. Tool-use 强化学习中的内容奖励应如何设计？ — 唯品会大模型算法实习一面（新增）
66. 多工具调用存在依赖关系时，Reward 应如何做信用分配？ — 唯品会大模型算法实习一面（新增）
67. Agent 交互轨迹与普通语言模型语料有什么区别？如何仿真高质量轨迹？ — 字节Agent算法实习一面（新增）
68. 多轮对话 RL 如何设计过程奖励与终局奖励，并避免用户模拟器过拟合？ — [阿里云 AI Infer 一面](https://www.nowcoder.com/discuss/921086976030150656)（2026-08-23）
69. 为什么 SFT 后继续做 DPO/PPO 等偏好优化可能导致基础能力退化？ — 哔哩哔哩 AI 后端开发凉经（新增）
70. KV Cache Block 的哈希和逻辑到物理映射应该怎么设计？ — 智象未来 AI Infra一面（新增）
71. Agent 动作空间过大导致探索低效时，如何裁剪和分层？ — 阿里千问 C端算法实习一面（新增）
72. 训练实验如何对 YAML 配置做规范化哈希，并保证单变量变化可复现？ — [大方云图研发实习一面](https://www.nowcoder.com/feed/main/detail/a9a40feb4e1e4d0ca7c3f8c3ba67d487)（2026-08-24）
73. 如何训练模型做高精度抽取式摘要？数据、目标、Loss 和评测如何设计？ — 百度大模型实习 Agent 面经（新增）
74. 预训练与 SFT 在数据、目标函数、计算形态和基础设施上有什么区别？ — AI Infra 小厂实习面经（新增）
75. Agentic RL 数据筛选为什么会排除部分学生错误轨迹？哪些可恢复错误反而值得保留？ — [阿里云 AI Infer 一面](https://www.nowcoder.com/discuss/921086976030150656)（新增）
76. TTS 音频如何被离散化为 Token，语义与音色信息如何取舍？ — [MiniMax 大模型算法岗一面](https://www.nowcoder.com/discuss/926272883872075776)（新增）
77. LLaMA-Factory 和 TRL 等 SFT / RL 工具如何对比和选型？ — [MiniMax 大模型算法岗一面](https://www.nowcoder.com/discuss/926272883872075776)（新增）

78. 如何处理训练数据中的类别不平衡？ — [本轮面经（文章 27）](https://www.nowcoder.com/feed/main/detail/46556042061840eca6af69727e72909c)
79. 自研自动驾驶方法与 UniAD 的主要区别应如何比较？ — [本轮面经（文章 30）](https://www.nowcoder.com/feed/main/detail/2981f94b70954a38bd30804a7a3071af)
80. 决策任务的 label 如何定义？预测任务如何设计监督信号？ — [本轮面经（文章 30）](https://www.nowcoder.com/feed/main/detail/2981f94b70954a38bd30804a7a3071af)
81. 如何把“减速多少”映射为是否碰撞的风险？ — [本轮面经（文章 30）](https://www.nowcoder.com/feed/main/detail/2981f94b70954a38bd30804a7a3071af)
82. LightGBM 和 XGBoost 有什么区别，如何选型？ — [本轮面经（文章 39）](https://www.nowcoder.com/discuss/927969546672046080)
83. 树模型需要哪些特征工程？缺失值、初始化、默认值和分桶怎么处理？ — [本轮面经（文章 39）](https://www.nowcoder.com/discuss/927969546672046080)
84. 连续特征离散化有什么作用和代价？ — [本轮面经（文章 39）](https://www.nowcoder.com/discuss/927969546672046080)
85. 机器学习、LSTM 和大语言模型之间是什么关系？ — [本轮面经（文章 40）](https://www.nowcoder.com/feed/main/detail/ac25d49b0692473c8f65654adda82b9b)
86. LSTM 的核心设计原理是什么？ — [本轮面经（文章 40）](https://www.nowcoder.com/feed/main/detail/ac25d49b0692473c8f65654adda82b9b)
87. 为什么选择 AC 自动机、TextCNN、FastText 和 TinyBERT，而不是更深的模型？ — [本轮面经（文章 77）](https://www.nowcoder.com/feed/main/detail/19d5ea0eda0e40de8a060ac516703c58)
88. 使用大模型生成标签时，会遇到哪些问题？ — [本轮面经（文章 77）](https://www.nowcoder.com/feed/main/detail/19d5ea0eda0e40de8a060ac516703c58)
89. 交叉熵损失的数学形式和含义是什么？ — [本轮面经（文章 77）](https://www.nowcoder.com/feed/main/detail/19d5ea0eda0e40de8a060ac516703c58)
90. 若真实标签分布为 P、预测分布为 Q，KL 散度如何表示？ — [本轮面经（文章 77）](https://www.nowcoder.com/feed/main/detail/19d5ea0eda0e40de8a060ac516703c58)
91. 图召回主要解决什么问题？如何划分负责环节？ — [本轮面经（文章 77）](https://www.nowcoder.com/feed/main/detail/19d5ea0eda0e40de8a060ac516703c58)
92. 为什么用图召回，而不是用户—物品行为模型、矩阵分解或双塔模型？ — [本轮面经（文章 77）](https://www.nowcoder.com/feed/main/detail/19d5ea0eda0e40de8a060ac516703c58)
93. 为什么在排序链路中同时使用 LightGBM 和 LambdaRank？ — [本轮面经（文章 77）](https://www.nowcoder.com/feed/main/detail/19d5ea0eda0e40de8a060ac516703c58)
94. 静态分和动态分在推荐链路中分别起什么作用？ — [本轮面经（文章 77）](https://www.nowcoder.com/feed/main/detail/19d5ea0eda0e40de8a060ac516703c58)
95. 模型剪枝有哪些方法，如何评估是否值得？ — [本轮面经（文章 93）](https://www.nowcoder.com/feed/main/detail/9b4cee70522d4e7aa771e222aeb28169)
96. 序列较稀疏时，建模如何处理稀疏性？ — [本轮面经（文章 101）](https://www.nowcoder.com/discuss/927381090602348544)
97. 业界通常如何处理长视频理解？ — [本轮面经（文章 159）](https://www.nowcoder.com/feed/main/detail/bfd43b5c66784add8fbf5893c164697a)
98. 视频没有语音时，视觉与多模态分析如何降级？ — [本轮面经（文章 159）](https://www.nowcoder.com/feed/main/detail/bfd43b5c66784add8fbf5893c164697a)
99. 一条 VideoSegment 数据结构应保存哪些内容？ — [本轮面经（文章 160）](https://www.nowcoder.com/feed/main/detail/ed25d2f60ddc4436b0139a7c52e62a61)
100. 持续学习有哪些方法，如何避免旧能力退化？ — [本轮面经（文章 185）](https://www.nowcoder.com/discuss/926467109717118976)
101. Qwen-VL 的动态分辨率如何实现？ — [本轮面经（文章 186）](https://www.nowcoder.com/discuss/926463586325495808)


## 11-ai-code-testing（19题）

1. 代码解析有没有前置分析？有效性判断？ — 蚂蚁一面【[美团 - Agent 开发岗（场景设计方向）](https://www.nowcoder.com/discuss/926273749555376128)追问：代码生成场景的安全漏洞防范（静态分析）？】
2. 分支覆盖率是怎么统计的？代码插桩怎么实现？ — 蚂蚁一面
3. 哪些代码会让模型生成准确度降低？如何过滤？ — 蚂蚁一面
4. 如何测试 AI 生成代码的正确性？ — 蚂蚁一面 【字节实习二面追问：AI 写的代码如何验证】【字节实习Agent开发一面追问：代码Agent生成结果有效性/准确率量化】【小红书 Agent 岗一面追问：Agent 自主生成测试程序】【OPPO/深信服一面追问：修改验证与测试门禁】【[字节中国交易与广告 AI 全栈二面](https://www.nowcoder.com/feed/main/detail/0f77410f8b1b4daca879d5ff99c7ae07)】【[蚂蚁 Agent 开发一面](https://www.nowcoder.com/feed/main/detail/39451cad5d2245b491d16778f2a9ca01)】
5. AI 生成的代码线下测试没问题，上线后出了问题怎么办？ — 字节实习二面
6. 工程级 Code Agent 处理项目上下文、生成代码时有哪些核心挑战？ — 蚂蚁Agent一二面（Code Agent方向）【[字节 AI 应用开发二面](https://www.nowcoder.com/feed/main/detail/7e8a821479a649fd914e449d312eeb95)】【[拼多多 - Agent 开发岗（工程化 + 数据库）](https://www.nowcoder.com/discuss/926273867092430848)追问：代码生成全链路及超长上下文处理？】
7. 如何用 Agent 自动化测试一个现有软件项目，并划分规划、执行、Oracle 与人工门禁？ — 蚂蚁集团效能研发面经【[0824 百度二面](https://www.nowcoder.com/feed/main/detail/2c301fd7793e43d18b8f8481d25a72e8)追问：长期演进框架的上下文与产物治理】【[viture agent平台开发 一面](https://www.nowcoder.com/feed/main/detail/c4c614b12d564af3b37c30c241072973)追问：如果完全自动化地交给Agent不太放心，如何解决？】
8. Coding Agent 如何执行人工交互测试，例如操作浏览器并验证页面行为？ — 小红书 Agent 岗一面（新增）【[蚂蚁 Agent 开发一面](https://www.nowcoder.com/feed/main/detail/39451cad5d2245b491d16778f2a9ca01)】
9. Coding Agent 如何做增量代码审查，避免大仓库全量逐行扫描？ — PDD秋招提前批一面（新增）【[拼多多 - Agent 开发岗（工程化 + 数据库）](https://www.nowcoder.com/discuss/926273867092430848)追问：代码审查 Agent 的全量扫描优化？】
10. AI 生成代码在哪些场景更具落地价值？应用边界在哪？ — 蚂蚁Agent一二面（Code Agent方向）
11. AI 测试平台中，人和 AI 的职责边界如何划分？ — 快手测试开发实习一面（新增）
12. TDD 如何接入 Coding Agent？测试门禁应该放在生成流程的哪个阶段？ — [深信服 Agent 三面](https://www.nowcoder.com/feed/main/detail/b64e8fddbfc642ec9aa33bcdb9aab9aa)（2026-08-23）
13. AI Coding 如何完成多来源账单分析应用，并证明交付结果可信？ — CVTE视源股份 AI Coding（新增）
14. Coding Agent 能否自举开发自身？如何避免生成器与验证器同源导致循环确认？ — [平安健康保险 AI 应用开发一面](https://www.nowcoder.com/feed/main/detail/6c11a75a8bd44628943deff3e42ae15c)（新增）

15. 什么是 AST，代码测试中如何使用？ — [Walmart-Onesec-Intern一面（已offer）](https://www.nowcoder.com/feed/main/detail/c639e7ea920b49b1834839f2a090809e)
16. 污点分析通常包含哪三类核心节点？ — [Walmart-Onesec-Intern一面（已offer）](https://www.nowcoder.com/feed/main/detail/c639e7ea920b49b1834839f2a090809e)
17. 请举例说明业务中的污点源和污点汇。 — [Walmart-Onesec-Intern一面（已offer）](https://www.nowcoder.com/feed/main/detail/c639e7ea920b49b1834839f2a090809e)
18. 代码 Agent 评测中，worktree 对照实验解决什么问题？ — [Walmart-Onesec-Intern一面（已offer）](https://www.nowcoder.com/feed/main/detail/c639e7ea920b49b1834839f2a090809e)
19. 如何用工程手段治理代码规范，而不是只依赖模型提醒？ — [百度Agent Harness 研发工程师 - 9月8日 - 一面 - 秋招](https://www.nowcoder.com/discuss/926928449204129792)


## 12-business-ai-engineering（27题）

1. 时间紧张，“快速上线规则方案”和“训练一个更智能的 AI 方案”之间怎么选？ — 网易 AI Agent 开发实习【[阿里国际 Agent 开发三面](https://www.nowcoder.com/feed/main/detail/747f07e71f4448bebdce6ada5de800cd)】【[字节中国交易与广告 AI 全栈二面](https://www.nowcoder.com/feed/main/detail/0f77410f8b1b4daca879d5ff99c7ae07)】
2. 设计一个能根据用户行为自适应调整策略的 AI 系统，从技术架构上怎么做？ — 网易 AI Agent 开发实习
3. 如何验证 AI 方案确实提升了业务指标，而不是带来了副作用？ — 网易 AI Agent 开发实习【[阶跃星辰（Stepfun）- 大模型算法岗（Post-train）](https://www.nowcoder.com/discuss/926273007276814336)追问：如何衡量后训练带来的实际业务增益？】
4. 业务方反馈“AI 效果差”，你怎么系统性定位问题？ — 网易 AI Agent 开发实习【[viture agent平台开发 一面](https://www.nowcoder.com/feed/main/detail/c4c614b12d564af3b37c30c241072973)追问：如果AI Agent效果没有达到预期、在某些指标上落后，你们怎么优化？】
5. 面向客户的 Multi-Agent 客服系统，怎么保证用户体验良好？ — 币安AI大模型实习一面
6. 知识库 RAG 和智能客服 Agent 系统的成熟方案有哪些？标准方案的优点和局限性？ — 币安AI大模型实习一面
7. Agent 项目如何从 Demo 进行企业级落地？从原型到生产需要补全哪些工程能力？ — 哆咔互娱 Agent开发实习一面 【[国际业务 Agent 一面](https://www.nowcoder.com/feed/main/detail/3c305b0c1565458ba05c9906322f5327)追问：无人化业务链路的自治边界】
8. 设计订单客服 Agent 时，如何处理转人工和意图识别调优？ — 某 Java/Agent 岗面经（新增）
9. 如何设计会议转写 Agent 的端到端链路并评估质量？ — 字节 TikTok AI Agent开发一面（新增）【[字节中国交易与广告 AI 全栈二面](https://www.nowcoder.com/feed/main/detail/0f77410f8b1b4daca879d5ff99c7ae07)】
10. 医疗 Skill 如何与 HIS 系统协同，同时满足权限和审计要求？ — [百川智能医疗大模型后训练一面](https://www.nowcoder.com/feed/main/detail/d209892dc2cf43c6859a776c5e526eca)（2026-08-22）【[阶跃星辰（Stepfun）- 大模型算法岗（Post-train）](https://www.nowcoder.com/discuss/926273007276814336)追问：医疗 Skill 的设计动机及与 HIS 协同方案？】
11. 面向 C 端的 Agent 应用应该包含哪些架构和模块？ — 百度大模型研发二面（新增）【[百度 - Agent 研发岗（架构方向）](https://www.nowcoder.com/discuss/926273622006665216)追问：何为 Agent 应用？C 端 Agent 的架构模块？】
12. 什么时候接入 MCP 是合理设计，什么时候属于过度设计？ — 拼多多 AI Agent 提前批二面（新增）
13. 设计一个群聊 Agent，如何同时处理权限、上下文和并行请求？ — 小红书数据库智能化日常实习一面（新增）
14. 长文本内容安全审核如何区分“引用有害内容”与“表达有害立场”？ — [中国电信风控 Agent 二面](https://www.nowcoder.com/feed/main/detail/22e18a3d20734429aec41b37744beadc)（2026-08-22）
15. 音视频 Agent 如何保护隐私并提供可验证删除？ — 字节 TikTok AI Agent开发一面（新增）
16. 20K 流式长文本安全审核如何兼顾增量响应与全文语义？ — [中国电信风控 Agent 二面](https://www.nowcoder.com/feed/main/detail/22e18a3d20734429aec41b37744beadc)（2026-08-22）
17. 设计一个“输入网站、输出宣发内容”的 Agent，完整链路是什么？ — 百度大模型研发二面（新增）
18. 有害内容安全改写如何兼顾风险控制与用户真实诉求，并验证语义保持？ — [中国电信风控 Agent 二面](https://www.nowcoder.com/feed/main/detail/22e18a3d20734429aec41b37744beadc)（新增）
19. 内容安全误杀后，如何通过申诉、分层策略和回归集持续治理？ — [中国电信风控 Agent 二面](https://www.nowcoder.com/feed/main/detail/22e18a3d20734429aec41b37744beadc)（新增）
20. 浏览器端运行小模型有什么价值？隐私、算力和能力边界是什么？ — [拼多多 AI 全栈两轮技术面](https://www.nowcoder.com/discuss/921104232256675840)（新增）
21. 如何设计批量 PDF 转 HTML 并与知识库核对的 LLM Workflow？ — [平安健康保险 AI 应用开发一面](https://www.nowcoder.com/feed/main/detail/6c11a75a8bd44628943deff3e42ae15c)（新增）

22. 如何设计一个自动驾驶行为评估 Agent？ — [卓驭 正式批 一面 数据算法与测评工程师 已挂](https://www.nowcoder.com/feed/main/detail/46556042061840eca6af69727e72909c)
23. 如何预测车辆未来一段时间的网络强弱？ — [小鹏汽车端侧agent一面](https://www.nowcoder.com/feed/main/detail/ac25d49b0692473c8f65654adda82b9b)
24. 网站访问量激增时，如何设计系统承载？ — [9.11 Boss直聘--一面](https://www.nowcoder.com/feed/main/detail/51ff89e97d4949bd9db8e12a605b7aa9)
25. 智能评审系统如何落地，大模型承担什么职责？ — [汇川技术-应用软件工程师-一面](https://www.nowcoder.com/feed/main/detail/31bdec3009dd4557936291038fae6bc0)
26. 如何说明一个 AI 系统在信审链路中的位置和职责？ — [阿里 Token Foundry AI应用研发一面面经](https://www.nowcoder.com/feed/main/detail/6a7fbdcf484a4b2bbe4b900b2dbd5750)
27. 如何过滤广告、系统消息等垃圾信息？ — [要务科技-面筋](https://www.nowcoder.com/discuss/926539013991796736)


## 13-project-deep-dive（25题）

1. 你的 Agent 项目用了什么框架？为什么选它？ — 淘宝闪购一面 【淘宝闪购一面追问：安全合规下开源 vs 闭源框架选型】【CVTE AI应用工程师一面追问：为什么基于 LangGraph 做】【[互联网金融 Agent 开发三面](https://www.nowcoder.com/feed/main/detail/88c55ee65af04ac98c218b9d17c47a71)】【[百度 Agent 二面](https://www.nowcoder.com/feed/main/detail/bca7dc14bd654e91b89792608111b211)】
2. Agent 项目有没有真正上线部署？线上效果怎么样？ — 淘宝闪购一面 【视频面经追问：上线后整体部署方式是怎样的】【[汇川技术-AI全栈开发工程师 技术一面 8/27 应届实习（含转正）](https://www.nowcoder.com/discuss/925156092424749056)追问：日常有没有将项目上线到云服务器？】
3. 意图识别模块具体怎么做的？ — 淘宝闪购一面【[快手 - Agent 开发岗（应用落地 + AI 工具）](https://www.nowcoder.com/discuss/926274020192841728)追问：意图识别模块应采用分类模型还是规则引擎？如何提升准确率？】【[作业帮秋招一面](https://www.nowcoder.com/feed/main/detail/c86c7591ba9d47b696774ddb48cdc9cb)追问：意图识别是怎么做的，使用的什么模型，介绍意图识别树结构。】
4. 你的 Agent 有哪些工具？工具是怎么设计的？ — 淘宝闪购一面 【视频面经追问：工具怎么注册/管理/调用】【[字节 AI 应用开发二面](https://www.nowcoder.com/feed/main/detail/7e8a821479a649fd914e449d312eeb95)】
5. 怎么提升工具调用的正确率？ — 淘宝闪购一面【[字节跳动9.3 Agent开发一面面经](https://www.nowcoder.com/discuss/925342611194286080)追问：Agent在执行过程中需要调用工具，这些工具都有固定的入参，需要模型结合上下文提供，如何保障工具调用的可靠性？】【[第三次去哪儿旅行一面，AI面试问的是前端吗？](https://www.nowcoder.com/feed/main/detail/2ed12b3fa1d4491f8bb029f99cf9de73)追问：Agent工具调用失败的常见原因有哪些？如何优化工具调用成功率？】
6. 工具调用时怎么保证参数提取准确？ — 淘宝闪购一面
7. 知识库是怎么构建的？ — 淘宝闪购一面【[8.26百度二面](https://www.nowcoder.com/feed/main/detail/190c6c68414b491d856091e42aef2386)追问：IM 项目中的 AI 助手和知识检索是怎么做的？】【[拼多多 复活赛 一面](https://www.nowcoder.com/feed/main/detail/2109cf8eb0254507911fbf86bcbf51e4)追问：你们现在知识库具体是怎么做的？】
8. 分块策略是怎么设计的？ — 淘宝闪购一面 【蚂蚁AI应用开发二面追问：overlap 与分片尺寸权衡】【腾讯AI应用开发一面追问：分块方案选型理由与指标量化】
9. 如何解析上传的表格或图片文件来构建知识库？ — 淘宝闪购一面 【蚂蚁AI应用开发二面追问：跨页表格语义完整性】【[虾皮Agent一面](https://www.nowcoder.com/feed/main/detail/409dc8793a7b450eb51ee32c2b923d49)追问：文档里面存在表格、图片，如何处理？】
10. 知识检索时如何提升模型回答正确率？ — 淘宝闪购一面
11. 你的系统有没有用到 ReAct 模式？怎么用的？ — 淘宝闪购一面 【美团食杂后端一面同题：如何基于 ReAct 架构开发的】【[互联网金融 Agent 开发三面](https://www.nowcoder.com/feed/main/detail/88c55ee65af04ac98c218b9d17c47a71)】
12. LangGraph 中的 State 怎么定义和流转？节点多了怎么防止状态膨胀？ — 蚂蚁AI应用开发二面 【钉学科技 FDE 实习一面追问：State、Node、Edge 的设计优先级】
13. 你的 Agent 系统还有哪些未充分优化的地方？你的改进路线图是什么？ — 淘宝闪购一面【[viture agent平台开发 一面](https://www.nowcoder.com/feed/main/detail/c4c614b12d564af3b37c30c241072973)追问：AI Agent系统的优化过程如何？】
14. 开发 Agent 过程中遇到的最大问题是什么？如果重新设计某一模块会怎么做？ — CVTE AI应用工程师一面【[阿里云 SOC Agent Infra 一面](https://www.nowcoder.com/feed/main/detail/1bde9ba913d74ca6847962f679865f7e)】
15. 自我介绍 + 简单讲一下自己做过的 Agent 项目 — 视频面经汇总（新增）【[钉钉二面](https://www.nowcoder.com/discuss/925181638412091392)追问：介绍一下你之前做的 Agent。】
16. 怎么提升模型回答的性能？ — 淘宝闪购一面
17. 你的 Agent 和别人开发的相比，核心差异是什么？ — 淘宝闪购一面
18. 新闻交易 Agent 项目管线如何搭建？Agent 响应延迟是多久？ — 币安AI大模型实习一面
19. 项目为什么选择 E2B 沙箱？选型理由和优势是什么？ — CVTE AI应用工程师一面
20. 你做过的不同 AI 项目之间，核心技术差异是什么？ — 已有正文（补录索引）
21. 视频 AI Agent 项目主要解决什么业务问题？ — [阿里 Token Foundry AI应用研发三面面经（三面挂）](https://www.nowcoder.com/feed/main/detail/bfd43b5c66784add8fbf5893c164697a)；[阿里 Token Foundry AI应用研发二面面经](https://www.nowcoder.com/feed/main/detail/ed25d2f60ddc4436b0139a7c52e62a61)

22. 视频 Agent 的 VideoContext 数据结构应如何设计？ — [阿里 Token Foundry AI应用研发二面面经](https://www.nowcoder.com/feed/main/detail/ed25d2f60ddc4436b0139a7c52e62a61)；[阿里 Token Foundry AI应用研发三面面经（三面挂）](https://www.nowcoder.com/feed/main/detail/bfd43b5c66784add8fbf5893c164697a)
23. 跨机票、地铁与导航的地图 Agent，如何划定 Agent、数据和工具边界？ — 地图 Agent二面（新增）
24. 表格解析后如何保证结构和数值正确？ — [上海沐润天海文化科技 agent开发一面](https://www.nowcoder.com/discuss/928253581973553152)
25. 如何介绍 PPT 自动生成管线的技术栈并说明选型？ — [9.7传音控股AI测试开发实习生](https://www.nowcoder.com/feed/main/detail/1c1b97aa3ccb4b2a915eeed85d01107a)


## 15-agent-concepts（18题）

1. Harness Engineering 是什么？如果让你构建一个 Harness 体系，你会做哪些工作？ — 快手AI业务应用设计开发 【字节后端开发日常实习二面/腾讯AI后端开发一面/美团Agent方向/社招五年Go/腾讯音乐/小红书一面同题】【[阿里国际 Agent 开发三面](https://www.nowcoder.com/feed/main/detail/747f07e71f4448bebdce6ada5de800cd)】【[阿里千问平台开发复活赛一面](https://www.nowcoder.com/feed/main/detail/141447389dab4e8e9ca6db742a514f39)】
2. Prompt Engineering、Context Engineering、Harness Engineering 三者有什么区别？ — 阿里淘天Agent开发日常实习一面 【阿里云暑期实习同题】【成都某中厂追问变体：加入 Loop Engineering 作为第四层】【字节火山引擎 Managed Agent 一面追问：Context Engineering 与 Skills 组织】
3. 讲一讲 Agent 的发展路线——从以前的架构到现在的 Harness Engineering — 阿里淘天 AI应用开发 暑期二面 【[淘天 AI 应用开发秋招二面](https://www.nowcoder.com/feed/main/detail/1b201d12219c45818b447bc7633fd62c)追问：模型升级与 Harness 的边界】
4. 你的项目中体现了哪些 Harness Engineering 的思想？ — 阿里国际一面
5. Vibe Coding 和 Harness，你更偏向哪种路线？为什么？ — 字节TikTok实习后端AI开发一面
6. 你会关注 Harness、Context Engineering 这类行业热点吗？优势劣势？ — 腾讯CDG产品经理一面 【字节大模型算法暑期二面追问：harness/Hermes新Agent设计】【网易互娱二面同题】【[DeepSeek（深度求索）- Agent 开发 / Harness 方向（独角兽）](https://www.nowcoder.com/discuss/925527442863714304)追问：你最近在关注 Agent 领域的什么新技术？】
7. Harness、Hermes 这种比较新的 Agent 设计了解吗？ — 已有正文（补录索引）
8. MCP 是什么？它解决了 Function Calling 的什么根本问题？ — 蚂蚁智能体与大模型应用二面 【蚂蚁Agent开发一面/高德实习一面/字节实习Agent开发一面同题】【阿里 Agent Infra 一面题库同题】【[钉钉一面](https://www.nowcoder.com/discuss/923765750446202880)】
9. MCP 和 A2A 分别解决什么层面的问题？为什么需要两个协议？ — Agent 30题 【蚂蚁一面/币安AI大模型实习一面追问】
10. Skills 是什么？为什么有了 MCP 和 Function Calling 还需要 Skills？ — 字节实习一面 【蚂蚁一面/小红书/CVTE/科大讯飞同题】
11. Skill、MCP、Rule 三者在 Agent 系统中各自扮演什么角色？ — 蚂蚁一面 【快手AI应用开发一面追问：Tool/Skill/Agent三层抽象】【[淘宝闪购 AI 应用研发二面](https://www.nowcoder.com/feed/main/detail/09ec7c36a2774223a93044a02b2c3ec0)】【[虾皮一面](https://www.nowcoder.com/feed/main/detail/e133c2610bde4adc812bba66c62e1641)】
12. Hermes、OpenCode、Claude Code、OpenClaw 等热门 Coding Agent 工具的核心差异和适用场景？ — 哆咔互娱Agent开发实习一面【唯品会大模型算法实习追问：主流 Agent 框架在 Harness 上有什么差异】【[蚂蚁 Agent 开发一面](https://www.nowcoder.com/feed/main/detail/39451cad5d2245b491d16778f2a9ca01)】【[快手 AI 全栈一面](https://www.nowcoder.com/feed/main/detail/a30242712e8d456c839ff4223470f491)】
13. 如何比较 Coding Agent、通用助手与办公 Agent？ — 百度大模型研发二面（新增）【[杭州和为机电 AI 应用工程师面试](https://www.nowcoder.com/discuss/923620045412933632)】
14. Dify/Coze 这种低代码工作流平台和 Codex/Claude Code 这类 Coding Agent 的本质区别是什么？ — 成都某中厂Agent产品开发实习面经（新增）
15. LangChain 的传统 Chain 和 LCEL 有什么区别？LCEL 解决了哪些工程问题？ — 哔哩哔哩 AI应用岗 Agent开发一面（新增）
16. Hooks 在 Agent 系统中应该拦截哪些阶段，和 Prompt 约束有什么区别？ — B站 Agent二面（新增）
17. Coding Agent 如何通过规则和 Skills 治理代码规范？ — [百度 Agent Harness 研发工程师 - 9月8日 - 一面 - 秋招](https://www.nowcoder.com/discuss/926928449204129792)

18. Agent 和 Siri 这种传统助手的核心差别在哪？ — 高频题


## 16-agent-infra（28题）

1. 为什么需要 Checkpoint，恢复时从哪里继续？ — 长任务恢复与状态管理高频题 / [字节数据平台 Agent 一面](https://www.nowcoder.com/feed/main/detail/f5f840632a19417b91b8987762427a6a) / [MINISO Agent 开发实习一面](https://www.nowcoder.com/feed/main/detail/f844a4ac20be44bc9b3f756bd0ebb84c) / [哔哩哔哩秋招一面](https://www.nowcoder.com/feed/main/detail/87eadf9db3b14bb6912064ee79267c30)【阿里 Agent Infra 一面题库同题：状态管理、Checkpoint 与保存时机】【[拼多多 - Agent 开发岗（工程化 + 数据库）](https://www.nowcoder.com/discuss/926273867092430848)追问：断点恢复（服务重启后加载未完成状态）？】【[深圳tuitti视界之外实习一面](https://www.nowcoder.com/feed/main/detail/9b1329caf4b64389a0ab666585bda045)追问：这时候你是怎样恢复图的运行状态的？】
2. 如何支撑几十万并发 Agent Task，并把它观测清楚？ — 高并发调度与 Agent Observability 高频题 / [顺极 Agent 开发二面](https://www.nowcoder.com/feed/main/detail/93a26b84a6634558b7228bf350c709b5) / [中国电信风控 Agent 二面](https://www.nowcoder.com/feed/main/detail/22e18a3d20734429aec41b37744beadc)【阿里 Agent Infra 一面题库同题：MQ、背压、多租户、Scheduler 与 Worker 拆分】【[互联网金融 Agent 开发三面](https://www.nowcoder.com/feed/main/detail/88c55ee65af04ac98c218b9d17c47a71)】【[百度 Agent 一面](https://www.nowcoder.com/feed/main/detail/53542e2dcfd44b1d84b0ae55b4fc1b35)】【[拼多多 - Agent 开发岗（工程化 + 数据库）](https://www.nowcoder.com/discuss/926273867092430848)追问：长耗时 Agent 的资源占用及并发优化？】
3. 一次 Agent 请求的完整执行链路是什么？ — Agent Runtime 管线高频题【字节火山引擎 Managed Agent 一面同题】【阿里 Agent Infra 一面题库同题】【[阿里控股 Agent Infra 二面](https://www.nowcoder.com/feed/main/detail/627844d5923149b6ac46a631b2b41d5a)】【[深信服Agent开发实习生一面二面，长时间被吊着，最终被横向掉了](https://www.nowcoder.com/feed/main/detail/14b2c379ae434062a009aefea9fc5df9)追问：处理流程可以讲一下吗？整体链路是怎样的？】【[百度Agent一面](https://www.nowcoder.com/feed/main/detail/72858aade19d443facc870fea8bb134f)追问：如果问某上市公司去年毛利率下降，Agent 收到 Prompt 后的完整流程是什么？】
4. Kubernetes Pod/Deployment 从提交到就绪经历哪些控制链路？ — [百度 AI Infra 校招面经](https://www.nowcoder.com/feed/main/detail/436228d68ccb4ec78d08644bc9227dec) / [虾皮 AI Infra 实习一面](https://www.nowcoder.com/feed/main/detail/e610f57cfd3548cd96a27d92e2f8b25e) / [虾皮 AI Infra 实习二面](https://www.nowcoder.com/feed/main/detail/62b9123e4b7f497285e7d6f68844cdd6) / [字节社招一面](https://www.nowcoder.com/feed/main/detail/a385d6cc457d47c99c03cb8ea752ab89)【阿里 Agent Infra 一面题库追问：Kubernetes Scheduler 基本调度流程】
5. Tool 已成功但 Runtime 在写状态前宕机，如何避免重复副作用？ — 分布式幂等与部分失败高频题【[多益三面](https://www.nowcoder.com/discuss/922801355649974272)同题】【阿里 Agent Infra 一面题库同题：幂等、Exactly Once 与 Tool 部分成功】【[字节agent一面](https://www.nowcoder.com/feed/main/detail/612a1c20eea744a288b142f5b43f57e1)追问：Agent 超时重复下单是高风险问题，你们怎么实现幂等避免重复操作？】【[阿里边缘bu 秋招一面 （已过）](https://www.nowcoder.com/feed/main/detail/bdebbb6088b6405e9eb2bd2c345acb6e)追问：如果工具调用成功，但 Redis Checkpoint 写入失败，系统如何恢复并避免重复执行？】
6. 如果让你设计一个 Agent Runtime，你会怎么拆？ — Agent Infra 系统设计高频题【阿里 Agent Infra 一面题库追问：Runtime 定义、Framework 边界与无状态 Worker】【[字节中国交易与广告 AI 应用开发一面](https://www.nowcoder.com/feed/main/detail/b34f6902e8544fe2953696ed52e49dba)】【[百度 - Agent 研发岗（架构方向）](https://www.nowcoder.com/discuss/926273622006665216)追问：通用 Agent Runtime（兼容多种大模型）如何设计？】
7. Agent Sandbox 解决什么问题，为什么容器不一定够？ — 代码执行隔离高频题【阿里 Agent Infra 一面题库追问：隔离选型、资源约束与委托身份】【[互联网金融 Agent 开发三面](https://www.nowcoder.com/feed/main/detail/88c55ee65af04ac98c218b9d17c47a71)】
8. Agentic RL 采用同步还是异步 Rollout，如何权衡吞吐与稳定性？ — 美团/百度 AI Infra 面经（新增）
9. Agent Router 应以什么运行形态存在，请求数据流如何设计？ — 字节 AI Infra 实习一面（新增）【[月之暗面（Moonshot）- Agent 应用开发岗](https://www.nowcoder.com/discuss/926274239747952640)追问：如何设计路由机制，将请求交给合适的 Agent？】
10. 大量本地端 Agent 与云端 Agent 如何协同？身份、状态、离线和任务迁移边界怎么设计？ — [小红书 Agent 开发二面](https://www.nowcoder.com/feed/main/detail/9f7361c709f4413396988b4f334a0d6f)（新增）【[互联网金融 Agent 开发三面](https://www.nowcoder.com/feed/main/detail/88c55ee65af04ac98c218b9d17c47a71)】
11. Agent 平台或 Runtime 出现新框架时，如何评估迁移收益、兼容老旧服务并决定是否淘汰旧方案？ — [虾皮 Agent 二面](https://www.nowcoder.com/feed/main/detail/345b668e35a9451bb397a9189dfdc943) / [电商 Agent 三面](https://www.nowcoder.com/feed/main/detail/b6b453976c2d4e43a872054d695c2fe2)（新增）
12. Kubernetes 在 Agent Infra 中负责什么？ — Kubernetes/Controller 高频题【阿里 Agent Infra 一面题库同题：单 Agent 单 Pod、冷启动与 Reconcile 幂等】
13. Kubernetes 的 Request 与 Limit 分别怎样影响调度和资源隔离？ — 百度 AI Infra 面经（新增）
14. Kubernetes Scheduler 的三个队列如何流转？ — 虾皮 AI Infra 二面（新增）
15. Agent Worker 或 Sandbox 滚动发布时，如何逐步切流并保护长任务？ — 虾皮 AI Infra 面经（新增）
16. Ray 的核心调度链路是什么，节点 OOM 或上游故障后如何恢复？ — 虾皮 AI Infra 面经（新增）
17. Agentic RL 的 Rollout、Training 与推理引擎如何编排？ — AI Infra 小厂面经（新增）
18. Agent Infra 为什么能提升 Agent 的能力上限和任务成功率？ — 字节 Agent 后端终面（新增）
19. Agent 调用 Sandbox 的链路如何容错？Sandbox 运行中崩溃后怎么恢复？ — [字节 AML / 火山方舟 AI Infra 一面](https://www.nowcoder.com/discuss/921927475611869184)（2026-08-26）
20. Agent Task 适合建模为 Kubernetes CRD 吗？如何权衡声明式管理与高频任务吞吐？ — 阿里 Agent Infra 一面题库（新增）
21. verl AgentLoop 的运行模型、状态与扩展点是什么？ — [阿里云 AI Infer 一面](https://www.nowcoder.com/discuss/921086976030150656)（新增）
22. Agent 状态放在 Sandbox 内、用户状态放在 Sandbox 外时，边界如何设计？ — [顺极 Agent 开发二面](https://www.nowcoder.com/feed/main/detail/93a26b84a6634558b7228bf350c709b5)（新增）
23. 周期性 Agent 任务如何把 Schedule 与每次 Run 分离，并处理时区、漏跑、并发、幂等和失败通知？ — [淘宝闪购 AI 应用研发二面](https://www.nowcoder.com/feed/main/detail/09ec7c36a2774223a93044a02b2c3ec0)（新增）

24. Agent 如何实现主动向用户推送消息？ — [9.8 小厂 agent开发实习 面经](https://www.nowcoder.com/feed/main/detail/2f4e4cde4e524a16aae5f55a89c49273)
25. Agent 执行过程中如何提供安全停止功能？ — [青岛弯弓 Agent](https://www.nowcoder.com/feed/main/detail/89e9597f580840f5a6e9f740cc6b0b97)
26. 用户点击停止后，系统需要完成哪些清理和收尾？ — [青岛弯弓 Agent](https://www.nowcoder.com/feed/main/detail/89e9597f580840f5a6e9f740cc6b0b97)
27. 如何降低 Agent 依赖技术人员逐个配置的成本？ — [正浩创新 AI应用开发一面](https://www.nowcoder.com/feed/main/detail/14fe3975c0464b02bb58b24be1b63a21)
28. 如何让 Agent 执行过程可观测、可调试？ — [9.7 百度 agent开发日常实习面经](https://www.nowcoder.com/feed/main/detail/bb8c28105f364770b57ff5eb5649cc60)


## 17-ai-infra（32题）

1. 如何用 Roofline 和算术强度指导 CUDA 算子优化？ — 美团/拼多多/小鹏/快手等 AI Infra 面经（新增）【[华为 - 大模型算法岗（AI Infra / 训练优化）](https://www.nowcoder.com/discuss/926272625410674688)追问：如何用 Roofline 模型判断带宽瓶颈 vs 计算瓶颈？】【[昆仑芯 0903 一面（ai 高性能开发）](https://www.nowcoder.com/feed/main/detail/65b9990e774a4331bb603f0cf1ca4a88)追问：介绍一下 Roofline 模型和算术强度。】【[0907 百度一面 （AI Infra）](https://www.nowcoder.com/feed/main/detail/91f5187146864de5878349a2ecf497ce)追问：大矩阵 GEMM 在 DCU 上如何切分和实现？】
2. KV Cache 占用如何计算，为什么不能只按请求数做容量规划？ — [抖音搜推 AI Infra 一面](https://www.nowcoder.com/feed/main/detail/e5f1a15d50414c86a0e64f2dbc13a02f)、[百度 AI Infra 一面](https://www.nowcoder.com/feed/main/detail/05c5fe23173245a4ab39b3dddf2b95bb)、[字节 App Infra Agent 一面](https://www.nowcoder.com/feed/main/detail/0bec32fbb3344ff98f16b97f47c7b857)、[字节社招一面](https://www.nowcoder.com/feed/main/detail/a385d6cc457d47c99c03cb8ea752ab89)【阿里 Agent Infra 一面题库追问：KV Cache 原理】【[华为 - 大模型算法岗（AI Infra / 训练优化）](https://www.nowcoder.com/discuss/926272625410674688)追问：Transformer 推理中 KV Cache 显存估算及 batch 增大瓶颈？】
3. 如何估算 All-Reduce/All-to-All 通信量并实现计算通信重叠？ — 阶跃星辰/快手/字节/爱奇艺等 AI Infra 面经（新增）【[华为 - 大模型算法岗（AI Infra / 训练优化）](https://www.nowcoder.com/discuss/926272625410674688)追问：如何优化分布式推理中的 AllReduce 通信？】【[阿里巴巴（阿里云）- Agent Infra](https://www.nowcoder.com/discuss/926273487512113152)追问：如何优化分布式 AllReduce 通信？；如何平衡多机多卡推理中的通信与计算？】
4. CUDA 的 Thread、Warp、Block、Grid 和 SM 如何映射？SIMT、同步与 Warp 分歧如何影响性能？ — 小马智行/OPPO/蔚来/沐曦 AI Infra 面经（新增）【[0907 百度一面 （AI Infra）](https://www.nowcoder.com/feed/main/detail/91f5187146864de5878349a2ecf497ce)追问：SIMT 的特点是什么？遇到分支时会发生什么？】
5. FlashAttention 为什么更快？Online Softmax、Tiling、重计算和不同版本分别解决什么瓶颈？ — 阿里国际/快手/美团等 AI Infra 面经（新增）【[华为 - 大模型算法岗（AI Infra / 训练优化）](https://www.nowcoder.com/discuss/926272625410674688)追问：FlashAttention 如何减少 HBM 访问？】【[阶跃星辰（Stepfun）- 大模型算法岗（Post-train）](https://www.nowcoder.com/discuss/926273007276814336)追问：FlashAttention 加速原理？】
6. 量化后为什么不一定更快？量化 Matmul、反量化、Prefill 和 Decode 的瓶颈如何判断？ — 美团/拼多多/混元/爱奇艺 AI Infra 面经（新增）【[昆仑芯 0903 一面（ai 高性能开发）](https://www.nowcoder.com/feed/main/detail/65b9990e774a4331bb603f0cf1ca4a88)追问：怎么判断一个算子是带宽瓶颈还是计算瓶颈？】
7. 如何从模型结构估算参数量、FLOPs、训练显存、推理访存与 MFU？ — 美团/混元/讯飞/字节等 AI Infra 面经（新增）
8. Prefill 与 Decode 的算子形态和瓶颈为何不同？ — 小马智行/阿里云/腾讯/爱奇艺 AI Infra 面经（新增）
9. MoE 的 Expert Parallel 如何做 Dispatch/Combine、负载均衡和通信优化？ — 阿里/美团/快手/字节等 AI Infra 面经（新增）
10. CPU、GPU 与 NPU 的体系结构和优化目标有什么差异？ — 蔚来/美团/讯飞/小鹏等 AI Infra 面经（新增）
11. FP8、NVFP4、INT8 与 W4A16 的数值格式、缩放粒度和硬件执行路径有何不同？ — 混元/讯飞/智谱/摩尔线程等 AI Infra 面经（新增）
12. GPU 内存层次如何使用？Pinned Memory、Shared Memory、Bank Conflict 与异步 H2D/D2H 分别解决什么问题？ — 阿里国际/阶跃星辰/快手等 AI Infra 面经（新增）
13. 流水线并行的 Bubble 从哪里来？1F1B、Zero-Bubble 与 DualPipe 如何调度？ — 快手/百度/美团 AI Infra 面经（新增）
14. CUDA、Triton、CUTE 与 MLIR 分别位于什么抽象层？ — 拼多多/小马智行/飞腾 AI Infra 面经（新增）
15. Stride、View/Contiguous 与 NHWC/NCHW 如何影响张量算子的正确性和性能？ — 字节/荣耀/OPPO AI Infra 面经（新增）
16. Attention 与 FFN 的计算量和参数量谁更大？ — 阿里云/百度 AI Infra 一面
17. 如何设计大模型在线推理服务？ — 百度/智象未来 AI Infra 一面
18. 模型版本升级如何做到可观测、可灰度、可回滚？ — 模型发布与稳定性高频题【[Momenta 大模型算法工程师一面](https://www.nowcoder.com/feed/main/detail/f7518c865e07491cb1518d288698813c)追问：离线效果更好为何仍保留旧模型】【[百度 - Agent 研发岗（架构方向）](https://www.nowcoder.com/discuss/926273622006665216)追问：模型能力下降时如何快速回滚与隔离？】
19. CUDA Graph 为什么能降低推理开销？为什么可能额外占显存，Prefill 与 Decode 哪个阶段更适合？ — 小马智行/爱奇艺 AI Infra 面经（新增）
20. vLLM/SGLang 的请求调度与 Continuous Batching 如何工作？请求被抢占后如何恢复？ — 阿里国际/爱奇艺等 AI Infra 面经（新增）
21. 投机采样中 Draft 与 Target 模型如何交互？什么时候会加速，什么时候反而变慢？ — AI Infra 小厂/爱奇艺面经（新增）
22. 大模型训练吞吐低时，如何用 MFU、Profiler、通信和流水线空泡定位瓶颈？ — 阶跃星辰/快手等 AI Infra 面经（新增）
23. PD 分离解决什么问题，Prefill 与 Decode 资源比例怎么定？ — 百度 AI Infra 一面
24. 分布式训练为什么容易失败，如何恢复？ — 摩尔线程 AI Infra 一面
25. GPU 利用率很低，但请求延迟很高，怎么排查？ — [小鹏 AI Infra 一面题面线索](https://www.nowcoder.com/discuss/920776068619829248)（付费题库汇总线索，不计频次）
26. AIOps 如何结合告警、Metrics、Logs、Trace 和服务拓扑完成证据驱动的 RCA，并安全执行自动处置？ — 阿里 Agent Infra 一面题库（新增）
27. SpMV 和 GEMM 的计算、访存特征有什么不同？优化方向如何选择？ — [沐曦 AI 工程师一面](https://www.nowcoder.com/feed/main/detail/af4c228ca96f4f05b415f816d36a718c)（新增）
28. GPU 上的同步方法代码可能有哪些问题，如何排查？ — [本轮面经（文章 11）](https://www.nowcoder.com/feed/main/detail/64868531af8d424b8aa55f46e313b478)
29. DeepSpeed ZeRO 的三个阶段分别做什么？ — [本轮面经（文章 185）](https://www.nowcoder.com/discuss/926467109717118976)
30. AI Infra 和 Agent Infra 有什么区别？ — AI 平台边界高频题

---

## 薄弱维度（题数 < 10）

当前没有少于 10 题的维度。

31. 如果让你设计一个生产级 AI Infra 平台，你会怎么拆？ — AI 平台系统设计高频题
32. GPU 调度和普通 CPU 调度有什么不同？ — GPU Scheduler 高频题


