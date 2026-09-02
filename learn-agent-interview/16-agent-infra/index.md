---
layout: default
title: Agent Infra：Runtime、Sandbox 与可靠执行
description: 拆解 Agent Runtime、状态恢复、沙箱与高并发调度
eyebrow: Agent 面试通关 / 16
---

# Agent Infra：Runtime、Sandbox 与可靠执行

Agent Demo 能完成一次工具调用，不代表它能承受 Worker 重启、网络超时和几十万等待中的任务。Agent Infra 面试真正考察的是：当模型把执行路径变得动态以后，你能否继续用分布式系统方法保证副作用、状态和资源都可控。

这一章不把 `Gateway → Queue → Worker` 当作万能架构图，而是沿着可靠性边界追问：状态写到哪里、超时后能不能重试、Kubernetes 重建 Pod 后谁来恢复业务执行。

> **真实面经信号**：岗位名称不等于只考 Agent 概念。[阿里云 Agent Infra 一面](https://www.nowcoder.com/feed/main/detail/d1fd4cd344bc4d928e708c3e69c8f59c)同时考了 Go/Java、Spring Bean、gRPC、TCP、MySQL、Redis、RAG 和项目源码；另一篇[阿里云 Agent Infra 一面](https://www.nowcoder.com/feed/main/detail/1da22ebd6e8e47f4a775cae00f09ced0)考了缓存系统、并发编程与快速排序。准备这类岗位时，Runtime 设计和传统后端底座缺一不可。

---

## Q：如何支撑几十万并发 Agent Task，并把它观测清楚？

> 来源：高并发调度与 Agent Observability 高频题 / [顺极 Agent 开发二面](https://www.nowcoder.com/feed/main/detail/93a26b84a6634558b7228bf350c709b5) / [中国电信风控 Agent 二面](https://www.nowcoder.com/feed/main/detail/22e18a3d20734429aec41b37744beadc) / [互联网金融 Agent 开发三面](https://www.nowcoder.com/feed/main/detail/88c55ee65af04ac98c218b9d17c47a71) / [百度 Agent 一面](https://www.nowcoder.com/feed/main/detail/53542e2dcfd44b1d84b0ae55b4fc1b35)【阿里 Agent Infra 一面题库同题：MQ、背压、多租户、Scheduler 与 Worker 拆分】

**新手答**：“用 MQ 解耦，再水平扩容 Worker，接入日志、指标和链路追踪。”

**高手答**：

我会先澄清“几十万并发”是活跃会话、等待任务还是同时计算，并给出到达率、平均步骤数、各阶段耗时和 SLO。大量 Run 可能在等待 LLM、Tool 或人工事件，不能都占用 Worker。

控制面按租户、优先级和资源类型分队列；用 visibility timeout/lease、ack、DLQ 和毒任务隔离保证消费；用 weighted fair scheduling、并发配额和 admission control 防止大租户挤占资源；对 LLM、GPU 和外部 Tool 分别实施背压，而不是只按 CPU 扩容。

全量开放前还要把模型分层和成本预算放进准入：简单步骤走低成本模型，复杂或高风险步骤才升级；Run、租户和平台分别设置 Token、金额、并发和 Deadline 上限。容量规划用到达率、各资源阶段服务时间和长尾分布估算，不能把“sub-agent 最多开几个”写成固定常数。容器 CPU/内存水位、GPU/KV 容量、模型配额和外部 Tool 限流必须分别观测，哪个先饱和就在哪一层背压。

Sandbox 容量要单独建模：区分冷启动、预热池、活跃执行和回收中实例，按租户与风险等级设并发配额。扩容信号不只看队列长度，还要看队列等待时间、启动耗时、CPU/内存/磁盘水位和回收失败率。预热复用必须先验证文件、进程、缓存和凭证已清理，否则优先牺牲冷启动时延而保持一次性隔离。

一个 Run 是根 Trace，模型、检索、工具、Sandbox 和状态提交是 Span。核心指标包括任务语义成功率、基础设施失败率、队列等待、端到端延迟、步骤数、Token/Cost 和 `UNKNOWN` 副作用数。Prompt、Tool 参数和结果可能包含隐私，必须脱敏、采样、分级存储和审计，不能直接放进高基数 Metrics Label。

**差距在哪**：新手会画 Queue + Worker，高手先定义负载模型，并同时处理公平性、下游瓶颈和可观测数据治理。

---

## Q：Kubernetes Pod/Deployment 从提交到就绪经历哪些控制链路？

> 来源：[百度 AI Infra 校招面经](https://www.nowcoder.com/feed/main/detail/436228d68ccb4ec78d08644bc9227dec) / [虾皮 AI Infra 实习一面](https://www.nowcoder.com/feed/main/detail/e610f57cfd3548cd96a27d92e2f8b25e) / [虾皮 AI Infra 实习二面](https://www.nowcoder.com/feed/main/detail/62b9123e4b7f497285e7d6f68844cdd6) / [字节社招一面](https://www.nowcoder.com/feed/main/detail/a385d6cc457d47c99c03cb8ea752ab89)【阿里 Agent Infra 一面题库追问：Kubernetes Scheduler 基本调度流程】

**新手答**：“请求交给 API Server，Scheduler 选节点，Kubelet 拉起容器。”

**高手答**：

客户端请求先经过 API Server 的鉴权、准入和校验，再持久化到 etcd。Deployment Controller 通过 watch/Informer 观察期望状态并创建 ReplicaSet，ReplicaSet 再创建 Pod。Scheduler 为未绑定 Pod 做过滤、评分并写入节点绑定；目标节点上的 Kubelet 调用 CRI 拉镜像和启动容器，按声明协调 CSI 存储与 CNI 网络。探针通过后 Pod 才 Ready，Service 对应的 EndpointSlice 随之更新。

这是一组异步、最终一致的 Reconcile，不是一条同步 RPC。CSI、CNI 的具体调用位置还受运行时、插件和 Kubernetes 版本影响，回答时应说明组件责任，不硬背一条固定时序。

**差距在哪**：新手背组件顺序，高手能讲清对象所有权、watch/reconcile、调度绑定与数据面就绪的边界。

---

## Q：为什么需要 Checkpoint，恢复时从哪里继续？

> 来源：长任务恢复与状态管理高频题 / [字节数据平台 Agent 一面](https://www.nowcoder.com/feed/main/detail/f5f840632a19417b91b8987762427a6a) / [MINISO Agent 开发实习一面](https://www.nowcoder.com/feed/main/detail/f844a4ac20be44bc9b3f756bd0ebb84c) / [哔哩哔哩秋招一面](https://www.nowcoder.com/feed/main/detail/87eadf9db3b14bb6912064ee79267c30)【阿里 Agent Infra 一面题库同题：状态管理、Checkpoint 与保存时机】

**新手答**：“每一步保存消息，Pod 挂了以后读取最后一条继续执行。”

**高手答**：

我会区分三类持久化数据：

| 数据 | 作用 | 典型内容 |
|------|------|---------|
| 事件日志 | 记录已经发生的事实 | 状态转换、模型响应、Tool 执行状态 |
| Checkpoint | 加速恢复 | 当前 Step、Context 引用、Budget、版本 |
| 副作用记录 | 去重和对账 | `execution_id`、下游请求 ID、结果摘要 |

Checkpoint 应围绕一致性边界保存，而不是机械地“每轮保存一次”。模型已经产生 Tool Call、工具即将分发、工具结果提交、进入人工等待，都是重要边界。

恢复时先取得 Run 的新 lease，加载最近 Checkpoint，再重放后续事件，最后检查未决 Tool Call。只有状态明确为未执行且重试安全时才继续；如果外部操作可能成功但结果未落库，应进入 `UNKNOWN`，通过下游幂等查询或对账确认，不能直接重放。

Worker 中断时还要验证 Checkpoint 之后的事件是否完整、Artifact 是否已原子提交、原 Worker 的 lease 是否失效。失败点重试不是从某个函数行号继续，而是从最近的**可验证业务边界**重建输入；过期 Worker 晚到的结果必须被 fencing token 或状态版本拒绝。

**差距在哪**：新手把 Checkpoint 当消息快照，高手能处理快照之后的事件、并发恢复和不确定副作用。

---

## Q：一次 Agent 请求的完整执行链路是什么？

> 来源：[字节跳动 Agent 后端开发业务终面](https://www.nowcoder.com/feed/main/detail/1dd33c4b7bda453a82f7d645bde7f3ff) / [阿里控股 Agent Infra 二面](https://www.nowcoder.com/feed/main/detail/627844d5923149b6ac46a631b2b41d5a) / Agent Runtime 完整管线设计高频题【字节火山引擎 Managed Agent 一面同题】【阿里 Agent Infra 一面题库同题】

**新手答**：“用户请求模型，模型调用工具，拿到结果后继续推理。”

**高手答**：

```text
1. Gateway 完成身份、租户、限流和请求幂等校验
2. Control Plane 创建 Run，持久化初始状态和版本快照
3. Scheduler 发放带 lease 的下一步任务
4. Worker 装配 Context，调用模型并持久化响应或 Tool Call
5. Policy 层校验工具、参数、权限、预算和审批要求
6. Tool Runtime 以 execution_id 执行动作
7. 结果进入 SUCCEEDED、FAILED 或 UNKNOWN，并写入事件日志
8. 状态机决定继续、降级、等待、补偿或结束
9. 全链路记录 Trace、成本、版本和审计信息
```

这里记录的是模型响应和结构化决策，不依赖保存模型私有推理过程。Run 还要有最大步骤、总 Deadline、Token/Cost Budget 和取消传播，防止模型循环无限消耗资源。

**差距在哪**：新手只描述模型循环，高手能指出接入幂等、租约、策略门禁、状态提交和退出条件。

---

## Q：如果让你设计一个 Agent Runtime，你会怎么拆？

> 来源：Agent Infra / 平台工程系统设计高频题 / [字节中国交易与广告 AI 应用开发一面](https://www.nowcoder.com/feed/main/detail/b34f6902e8544fe2953696ed52e49dba)【阿里 Agent Infra 一面题库追问：Runtime 定义、Framework 边界与无状态 Worker】

**新手答**：“接入 LLM，再提供工具、Memory 和日志，最后部署到 Kubernetes。”

**高手答**：

我会先把一次 Agent Run 建模为**可能暂停和恢复的有状态执行**，再拆成管理面、控制面和执行面：

```text
Management Plane：Agent/Tool/Skill 注册、版本、发布与租户配置
Control Plane：状态机、租约、调度、超时、配额与恢复
Execution Plane：LLM Worker、Tool Worker、Sandbox
Data Plane：Run State、事件日志、Checkpoint、Artifact、Memory
Observability：Trace、Metrics、Logs、Eval、Cost、Audit
```

Runtime 不应依赖某个 Worker 的本地内存。每次状态转换都带版本号，Worker 通过 lease 领取任务，提交结果时检查 lease 和状态版本，避免过期 Worker 覆盖新结果。暂停等待人工审批时释放 Worker，审批事件到达后再唤醒任务。

LangChain、LangGraph 等 Framework 主要提供 Agent/Graph 的开发抽象；Runtime 负责租约、持久化、恢复、隔离、配额和跨 Framework 的执行治理。两者可以集成，但不能把“Graph 能表达状态”误认为“平台已经具备生产运行语义”。

生产目标通常是 **at-least-once 调度 + 幂等副作用**，而不是轻易承诺 exactly-once。还要为每个 Run 固定模型、Prompt、Tool 和策略版本，否则恢复后可能在另一套行为定义上继续执行。

取消也是一次并发状态转换，不是发一个中断信号就结束。Runtime 先持久化 `CANCEL_REQUESTED`，停止派发新 Step，再把取消传播到模型、Tool 和 Sandbox。完成结果与取消同时到达时，用状态版本和明确的转换表决定胜者；过期 Worker 的迟到结果只可审计，不能覆盖终态。

对发送消息、付款、写外部系统等不可逆副作用，取消只能阻止尚未发生的动作；已分发但结果未知的进入 `UNKNOWN`，通过幂等查询、对账或补偿收敛。最终给用户的结果应区分“已取消且无副作用”、“部分完成”和“结果待确认”，并保留已完成步骤的证据。

**差距在哪**：新手罗列组件，高手先定义执行语义，再说明状态所有权、并发控制和版本边界。

---

## Q：Tool 已成功但 Runtime 在写状态前宕机，如何避免重复副作用？

> 来源：分布式幂等与部分失败高频题【[多益三面](https://www.nowcoder.com/discuss/922801355649974272)同题】【阿里 Agent Infra 一面题库同题：幂等、Exactly Once 与 Tool 部分成功】

**新手答**：“给 Tool Call 加一个唯一 ID，恢复时查数据库。”

**高手答**：

唯一 ID 只有被副作用边界识别才有价值。我会为逻辑动作生成稳定的 `execution_id`，重试时保持不变，并优先把它传给下游作为幂等键：

```text
PENDING → DISPATCHED → RUNNING → SUCCEEDED
                              ├→ FAILED
                              └→ UNKNOWN
```

- 下游支持幂等键：重复请求返回同一业务结果；
- 同一数据库内：用唯一约束、事务或 Transactional Outbox；
- 下游支持查询：按业务键查询并对账；
- 下游既不幂等也不可查询：超时后标记 `UNKNOWN`，交由人工确认或补偿流程。

对支付、发消息、删除资源等操作还应增加审批、操作分级和审计。Saga 补偿也不等于回滚，补偿本身可能失败并且必须幂等。

**差距在哪**：新手只说“去重”，高手知道最危险的是执行结果未知，并能按下游能力选择事务、对账或人工介入。

---

## Q：Agent Sandbox 解决什么问题，为什么容器不一定够？

> 来源：[荣耀 AI Infra 一面](https://www.nowcoder.com/feed/main/detail/60ab2e3a45074b7391199acb9b5c6ca3) / [百度 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/436228d68ccb4ec78d08644bc9227dec) / [互联网金融 Agent 开发三面](https://www.nowcoder.com/feed/main/detail/88c55ee65af04ac98c218b9d17c47a71) / 代码执行与隔离设计高频题【阿里 Agent Infra 一面题库追问：隔离选型、资源约束与委托身份】

**新手答**：“Docker 有 Namespace 和 Cgroup，可以安全运行模型生成的代码。”

**高手答**：

Sandbox 运行的是不可信代码，目标不只是限制 CPU 和内存，还要控制文件系统、网络、系统调用、凭据、进程树、磁盘和执行时间。容器共享宿主机内核，隔离强度取决于 user namespace、capabilities、seccomp、SELinux/AppArmor 和宿主配置，不能把“用了 Docker”直接等同于安全。

| 场景 | 可选隔离 | 主要代价 |
|------|---------|---------|
| 内部只读工具 | 加固容器 | 隔离较轻，启动快 |
| 多租户代码执行 | gVisor / Kata | 兼容性或启动开销 |
| 高风险不可信代码 | MicroVM | 镜像、池化和运维成本 |

无论采用哪种方案，都应使用短期身份、只读根文件系统、默认拒绝网络、资源上限和硬 Deadline。复用预热 Sandbox 可以降低冷启动，但必须证明租户间文件、进程、缓存和凭据已经清理；高风险任务更适合一次性销毁环境。

当 Agent 代表用户调用外部系统时，Runtime 应把已认证用户映射为短期、限定 audience/scope 的委托凭证，并在受控传输层注入；长期密钥、刷新令牌和授权决策不能进入 Prompt。模型只提出 Tool Call，Runtime 仍要按用户、租户、工具和资源重新做 AuthZ，高风险操作再绑定审批范围与审计记录。

进程地址空间隔离只能阻止普通进程直接读取彼此内存，不等于完整安全边界；容器仍要面对共享内核、错误授权和网络外泄等攻击面。Namespace 负责隔离“看见什么”，Cgroup 负责约束“能用多少”，两者也都不能替代系统调用和身份权限控制。

隔离单元要与信任边界对齐：高风险且不可信的代码通常按 Run 或 Task 创建一次性 Sandbox，不因为属于同一用户就复用全部环境。若为了性能按用户或租户复用预热实例，必须将工作区、进程树、网络、凭证和资源计量继续按 Task 分区，并在复用前执行可验证的清理。

**差距在哪**：新手只比较容器技术名称，高手从威胁模型、信任等级和清理边界选择隔离方案。

---

## Q：Agentic RL 采用同步还是异步 Rollout，如何权衡吞吐与稳定性？

> 来源：[美团 AI Infra 实习面经](https://www.nowcoder.com/feed/main/detail/c94734d67c9f461ab950bf1d800c5643) / [百度 AI Infra 实习面经](https://www.nowcoder.com/feed/main/detail/4a848f5616cf4f8783020b3143a68fbc) / [AI Infra 实习面经](https://www.nowcoder.com/feed/main/detail/166e576d5afa4a298cf9492ed51bed04)

**新手答**：“异步能让 GPU 不空闲，所以一定比同步好。”

**高手答**：

同步 Rollout 接近 on-policy、批次边界清楚，但慢请求和阶段屏障容易让 Learner 或推理资源空转。异步可以重叠采样与训练，提高吞吐，却会产生 Policy Lag：轨迹来自旧策略，版本差越大，偏差和训练不稳定风险越高。

工程上要给轨迹标记 `policy_version`，设置最大滞后和有界队列，对过旧样本丢弃、降权或重采；是否使用重要性采样、裁剪等校正必须服从具体算法，不能套一个万能公式。监控应同时看版本滞后分布、队列等待、有效样本量、KL、吞吐和 Reward，而非只看 MFU。

**差距在哪**：新手只看吞吐，高手能把调度产生的数据陈旧性连接到算法偏差，并给出可观测门槛。

---

## Q：大量本地端 Agent 与云端 Agent 如何协同？身份、状态、离线和任务迁移边界怎么设计？

> 来源：[小红书 Agent 开发二面](https://www.nowcoder.com/feed/main/detail/9f7361c709f4413396988b4f334a0d6f) / [互联网金融 Agent 开发三面](https://www.nowcoder.com/feed/main/detail/88c55ee65af04ac98c218b9d17c47a71)

**新手答**：“端侧断网时先缓存，联网后同步到云端；复杂任务都放云上跑。”

**高手答**：

先按数据所有权拆分，不能做一个“双向同步所有状态”的大接口：

| 状态 | 权威方 | 离线策略 |
|------|--------|----------|
| 用户身份、授权和配额 | 云端控制面 | 端侧持有短期、限定 scope 的快照，过期后降权或停止高风险动作 |
| 设备能力、实时传感器和本地文件 | 端侧 | 本地读取，按最小必要原则上传摘要或 Artifact 引用 |
| Run 事件、Checkpoint 和副作用 | 创建该 Run 的控制面 | 用单调序号、幂等键和 lease 同步，不能靠最后写入覆盖 |
| 模型、Prompt、Tool 和策略版本 | 云端发布面 | 端侧缓存已签名版本，离线期间固定版本运行 |

断网时端侧只能执行预先授权、可撤销、风险受限的动作，并把事件写入有界本地队列。恢复连接后先做身份续期和版本协商，再按 `run_id + event_seq + execution_id` 上传；服务端逐条确认，重复事件幂等吸收，冲突进入显式仲裁。KubeEdge 的 [EdgeHub](https://kubeedge.io/docs/architecture/edge/edgehub/)和 [Device Controller](https://kubeedge.io/docs/architecture/cloud/device_controller/)展示了端云连接、上/下行状态和 desired/reported state 分离，但 Agent 的用户授权与副作用语义仍需业务层自己实现。

任务迁移只在语义 Checkpoint 处发生：冻结旧执行者、提交工作区/Artifact 清单、释放 lease，新执行者取得 fencing token 后校验模型与工具版本，再查询未知副作用并继续。没有可迁移状态的本地进程应从可验证步骤重建，而不是复制内存快照后假定外部世界没有变化。

从本地迁到云端前先做能力与数据分类：可携带的是结构化 Run State、已授权 Artifact 和版本化执行契约；设备私钥、本地绝对路径、未授权文件与活进程不直接上传。云端先验证目标 Tool/模型版本和数据驻留约束，不兼容时应停在已验证 Checkpoint 并显式降级，而不是让云端在缺失上下文时猜测继续。

**差距在哪**：新手只有“缓存后同步”，高手能定义权威状态、离线权限、冲突协议和任务唯一执行权。

---

## Q：Agent 平台或 Runtime 出现新框架时，如何评估迁移收益、兼容老旧服务并决定是否淘汰旧方案？

> 来源：[虾皮 Agent 二面](https://www.nowcoder.com/feed/main/detail/345b668e35a9451bb397a9189dfdc943) / [电商 Agent 三面](https://www.nowcoder.com/feed/main/detail/b6b453976c2d4e43a872054d695c2fe2)

**新手答**：“先做 PoC，新框架效果好就逐步迁移，出问题再回滚。”

**高手答**：

先盘点**迁移契约**，再比较框架功能：Run 状态机、Tool ABI、消息格式、Checkpoint schema、Artifact、权限、Trace、取消/超时和错误分类。只比较 Demo 成功率，会在迁移长任务和部分失败时付出代价。

我会分四步推进：

1. **适配**：在旧业务和新 Runtime 之间加防腐层，先统一 Tool/状态/Trace 契约；老服务通过 Adapter 暴露能力，不要求一次性重写。
2. **双轨**：固定模型、Prompt、数据和预算做离线回放，再用 shadow traffic 对比语义成功率、恢复率、P99、成本和可观测缺口。副作用工具只影子验证，不重复执行。
3. **迁移**：新 Run 按租户/任务 canary；在途 Run 默认固定旧 Runtime 到结束，只有 Checkpoint 可转换且经过校验时才迁移。
4. **退出**：预先定义旧平台停止条件、数据导出、回滚窗口和 owner；新框架达不到门槛就终止迁移，而不是形成永久双栈。

框架 API 会演进，版本兼容必须成为发布门禁。Kubernetes 的 [API Deprecation Policy](https://kubernetes.io/docs/reference/using-api/deprecation-policy/)说明了稳定 API 不能在同一版本中随意移除；Agent 平台虽不必复制其时间规则，但应采用相同思路：版本化 schema、明确弃用窗口和转换器。Trace 字段也应基于版本化的 [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/)，不要让迁移前后同名指标含义改变。

**差距在哪**：新手把迁移当换 SDK，高手会治理协议、在途状态、双轨证据、旧服务适配和退出成本。

---

## Q：Kubernetes 在 Agent Infra 中负责什么？

> 来源：Kubernetes 调度与 Controller 高频题【阿里 Agent Infra 一面题库同题：单 Agent 单 Pod、冷启动与 Reconcile 幂等】

**新手答**：“负责创建 Pod、自动扩容和故障迁移。”

**高手答**：

Kubernetes 管的是计算实例和资源期望状态，不负责恢复 Agent 的业务状态。Pod 被重建以后，Run 能否继续取决于外部状态、lease、Checkpoint 和工具幂等。

它适合承担 Worker/Sandbox 生命周期、资源请求与限制、节点选择、弹性伸缩、ServiceAccount 和 NetworkPolicy。Controller 的 Reconcile 是 level-triggered：每次都根据 Desired State 和 Actual State 收敛，必须能处理重复事件、缓存陈旧和部分成功。

“一个 Agent 一个 Pod”还会带来 API Server/etcd 对象规模、Scheduler 吞吐、镜像拉取、IP 消耗、资源碎片和回收压力。短任务可以使用 Worker Pool 或预热 Sandbox；强隔离任务可以保留一任务一环境，但要通过池化和容量规划控制冷启动。

**差距在哪**：新手把 Kubernetes 当业务恢复系统，高手明确基础设施重调度与 Agent 状态恢复的责任边界。

---

## Q：Kubernetes 的 Request 与 Limit 分别怎样影响调度和资源隔离？

> 来源：[百度 AI Infra 校招面经](https://www.nowcoder.com/feed/main/detail/436228d68ccb4ec78d08644bc9227dec)

**新手答**：“Request 是申请资源，Limit 是最多能用的资源。”

**高手答**：

Request 主要参与调度容量判断，Scheduler 看节点可分配资源与已承诺 Request，而不是瞬时利用率；它也参与 Pod QoS 分类。Limit 由 Kubelet、容器运行时和内核 Cgroup 落实：CPU 超过 Limit 通常被节流，进程不会因此直接退出；内存限制是反应式的，压力下可能触发 OOM Kill。未配置项、默认值以及 Pod 级资源能力会随集群策略和版本变化，不能假设所有集群行为一致。

Agent 平台还要在 Kubernetes 之外做租户并发和任务预算控制，因为“Pod 能调度”不代表 LLM、GPU 或外部 Tool 有容量。

**差距在哪**：新手只会写 YAML，高手能区分调度承诺、内核执行和业务侧 Admission Control。

---

## Q：Kubernetes Scheduler 的三个队列如何流转？

> 来源：[虾皮 AI Infra 实习二面](https://www.nowcoder.com/feed/main/detail/62b9123e4b7f497285e7d6f68844cdd6)

**新手答**：“Pod 排队，调度失败就过一会儿重试。”

**高手答**：

典型实现中，ActiveQ 保存当前可尝试调度的对象；调度失败且暂时没有合适节点时进入 Unschedulable 集合；需要退避的对象进入 BackoffQ，退避到期后再回 ActiveQ。节点容量、标签等相关集群事件发生时，Queueing Hint 或等价机制可以只激活可能受益的对象，避免无差别重试；对象停留过久也要获得再次尝试的机会。

这些是 kube-scheduler 的内部队列，不是 Agent Runtime 的 MQ。具体类型名和 PodGroup 等能力会随版本、特性门控变化，面试应先讲状态转换和触发条件，再补当前版本实现。

**差距在哪**：新手只说重试，高手能解释失败对象为何沉淀、何时被事件唤醒，以及如何避免热循环。

---

## Q：Agent Worker 或 Sandbox 滚动发布时，如何逐步切流并保护长任务？

> 来源：[虾皮 AI Infra 实习一面](https://www.nowcoder.com/feed/main/detail/e610f57cfd3548cd96a27d92e2f8b25e)

**新手答**：“用 Deployment 滚动更新和 Readiness Probe，新 Pod 好了就切流。”

**高手答**：

Deployment 通过新旧 ReplicaSet 和 `maxSurge`、`maxUnavailable` 控制替换速度；新 Pod 通过 Startup/Readiness Probe 后才应进入 Service Endpoint。旧 Pod 终止前先摘流，执行 `preStop` 和优雅终止。对长生命周期 Agent，仅靠 HTTP 摘流不够：Worker 要停止领取新 lease，等待可完成步骤 drain；超时任务持久化 Checkpoint、释放租约，由新 Worker 幂等恢复。

还要验证客户端重连、重复请求和版本兼容。PDB 主要约束自愿驱逐，并不保存 Agent 业务状态；不同入口控制器和服务网格的切流细节也不能一概而论。

**差距在哪**：新手只讲 Pod 数量，高手同时处理 Kubernetes 发布、任务租约、状态恢复和协议兼容。

---

## Q：Ray 的核心调度链路是什么，节点 OOM 或上游故障后如何恢复？

> 来源：[虾皮 AI Infra 实习一面](https://www.nowcoder.com/feed/main/detail/e610f57cfd3548cd96a27d92e2f8b25e) / [虾皮 AI Infra 实习二面](https://www.nowcoder.com/feed/main/detail/62b9123e4b7f497285e7d6f68844cdd6)

**新手答**：“Ray 会把任务调度到其他节点，失败后自动重试。”

**高手答**：

Driver 提交 Task/Actor，Raylet 按资源和放置约束调度 Worker，GCS 保存集群控制元数据，对象通过分布式 Object Store 传递。节点故障后，普通 Task 是否重试取决于 `max_retries` 等配置；丢失对象只有在 lineage 仍可用、生产任务可重放等条件满足时才能重建。Actor、应用状态和外部副作用另有生命周期，不能承诺透明恢复。

节点内存紧张时，Ray 的 Memory Monitor 可能终止 Worker，但选择和重试策略具有版本边界。Agent Tool 写库、发消息等副作用仍需业务幂等，不能把 Ray 重试当成 exactly-once。

**差距在哪**：新手把框架重试等同于恢复，高手会逐一检查任务、对象、Actor 和外部副作用的可重建条件。

---

## Q：Agentic RL 的 Rollout、Training 与推理引擎如何编排？

> 来源：[AI Infra 实习面经](https://www.nowcoder.com/feed/main/detail/166e576d5afa4a298cf9492ed51bed04)

**新手答**：“推理引擎生成轨迹，训练器算奖励并更新模型，然后同步权重。”

**高手答**：

系统通常包含 Actor/Learner、Rollout Engine、Reference Policy、Reward，以及算法需要时的 Critic。调度器把 Prompt 分发给 Rollout，轨迹连同模型版本进入奖励与训练阶段；Learner 产出新权重后，通过全量、分片或增量传输到推理侧。切换必须有 `policy_version`、完整性校验和原子激活，避免某条轨迹混用两版参数。

Actor 与 Rollout 共置可降低权重传输成本，却会产生显存和计算争用；分离部署隔离更好，但增加网络和同步开销。具体角色、同步协议和一致性强度取决于框架，回答应先给不变量，再谈实现。

**差距在哪**：新手只会画训练循环，高手能说明资源编排、权重版本、轨迹可追溯性和共置取舍。

---

## Q：Agent Router 应以什么运行形态存在，请求数据流如何设计？

> 来源：[字节 AI Infra 实习一面](https://www.nowcoder.com/feed/main/detail/fcf6cf54ae5f437eb9356b98cc69fd9f)

**新手答**：“用一个模型判断请求应该交给哪个 Agent。”

**高手答**：

Router 可以是进程内库、Workflow 节点或独立服务。低延迟、策略简单时进程内更省开销；多团队共享、策略频繁变化或需要独立扩容审计时，服务化更合适。典型数据流是 Gateway 完成身份和租户解析，Router 提取任务特征、召回候选 Agent/Tool，再结合能力、权限、预算、延迟和健康度打分，最后交给 Runtime 创建带版本快照的 Run。

策略要支持灰度、热更新、回滚和确定性 Fallback，并记录候选集、决策版本与结果反馈。这里讨论的是通用 Router 设计，不把某个项目中的同名组件当成行业标准。

**差距在哪**：新手只谈分类准确率，高手会交代部署边界、权限门禁、策略版本和端到端数据流。

---

## Q：Agent Infra 为什么能提升 Agent 的能力上限和任务成功率？

> 来源：[字节跳动 Agent 后端开发业务终面](https://www.nowcoder.com/feed/main/detail/1dd33c4b7bda453a82f7d645bde7f3ff)

**新手答**：“Infra 更稳定、并发更高，所以 Agent 效果会更好。”

**高手答**：

Infra 不会直接提高基础模型智力，但会扩大模型可可靠利用的能力：Context 组装提高有效信息密度，Tool/Router 把决策连接到可执行动作，Memory 支撑跨步骤延续，Checkpoint 和幂等让长任务能够恢复，Sandbox 与权限门禁允许系统安全放权，Trace/Eval 则把 Badcase 变成可迭代数据。

最难的是模型语义不确定性与分布式部分失败叠加：一次“成功”既要判断基础设施完成，也要判断任务语义正确。证明收益应在同模型、同任务集下做消融，对比任务成功率、步骤数、工具失败率、恢复率、延迟和成本，避免把流量变化误认为能力提升。

**差距在哪**：新手把能力等同于可用性，高手能建立基础设施机制、效果指标与反馈闭环之间的因果关系。

---

## Q：Agent 调用 Sandbox 的链路如何容错？Sandbox 运行中崩溃后怎么恢复？

> 来源：[字节 AML / 火山方舟 AI Infra 一面](https://www.nowcoder.com/discuss/921927475611869184)（2026-08-26）

**新手答**：“让 Kubernetes 重启 Pod，再从 Checkpoint 继续执行。”

**高手答**：

先把 Sandbox 执行建模成带 `execution_id`、attempt 和 lease 的状态机：`PENDING → DISPATCHED → RUNNING → SUCCEEDED/FAILED/UNKNOWN`。调度前持久化执行意图，Sandbox 启动后上报心跳，并持续外传 stdout、错误、资源指标和 Artifact；Runtime 设置启动、空闲、单工具和全局 Deadline，不能等 HTTP 连接自然超时才发现崩溃。

Sandbox 退出时区分正常非零码、OOM、硬超时、节点丢失和控制面失联。只读或幂等动作可在新的一次性环境中重试；可能已产生外部副作用但结果未提交时标记 `UNKNOWN`，先按幂等键查询或对账，不能盲目重放。恢复使用不可变镜像、输入 Artifact 和最近 Checkpoint，不复用可能残留进程、文件或凭据的脏环境。

Kubernetes 只负责重建计算实例，Agent Runtime 才负责业务状态恢复。控制面还要回收孤儿 Pod、过期 lease、临时卷和短期凭据；在途取消必须传播到 Sandbox，终止后拒绝过期 Worker 提交结果。观测上分别统计启动失败、OOM、超时、节点故障、UNKNOWN 副作用和恢复成功率。

**差距在哪**：新手把 Pod 重启等同于任务恢复，高手能处理状态提交、未知副作用、环境重建和孤儿资源回收四个故障边界。

---

## Q：Agent Task 适合建模为 Kubernetes CRD 吗？如何权衡声明式管理与高频任务吞吐？

> 来源：阿里 Agent Infra 一面题库

**新手答**：“适合。定义一个 AgentTask CRD，再写 Controller 创建 Pod，Kubernetes 会负责状态管理和失败恢复。”

**高手答**：

先判断对象是否符合 Kubernetes 的资源语义，而不是因为任务跑在集群里就做 CRD。Kubernetes [Custom Resources 官方文档](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)建议在对象适合声明式 API、天然属于集群或 Namespace、需要 `kubectl`/RBAC/审计及 Controller 持续 Reconcile 时使用自定义资源。

因此，长生命周期、数量受控的 `AgentPool`、`SandboxClass`、租户执行环境或需要运维人员声明目标状态的 Agent Run 可以建模为 CRD。`spec` 保存期望状态和不可变版本引用，`status` 保存 Controller 观察到的阶段、Condition 与关联资源；Reconcile 必须幂等，并处理 Finalizer、取消、过期 Worker 回写和孤儿资源回收。

但每个 LLM Step、Tool Call 或几秒钟完成的高频 Task 不适合直接写成 CR。它们会产生大量创建、状态更新、List/Watch 和删除流量，把业务任务吞吐耦合到 API Server、etcd 和 Controller 队列；Prompt、消息、Trace 和 Artifact 也不适合塞进 Kubernetes 对象。此时应把任务事实放进专用数据库、事件日志和 Queue，只让 CRD 管理较粗粒度的执行环境，并在两侧保存稳定引用。

最终要用对象基数、创建峰值、状态更新频率、保留周期、单对象大小和控制面 SLO 压测决定。需要 Watch 时还要正确处理 `resourceVersion`、断线重连和 `410 Gone`，不能把 Watch 当作永久可靠的消息队列。

**差距在哪**：新手把 CRD 当免费数据库，高手会先判断资源语义，再隔离 Kubernetes 控制面与 Agent 高频执行面的容量和一致性边界。

---

## Q：verl AgentLoop 的运行模型、状态与扩展点是什么？

> 来源：[阿里云 AI Infer 一面](https://www.nowcoder.com/discuss/921086976030150656)

**新手答**：“它就是在训练时循环调用模型和工具，生成多轮轨迹给 RL。”

**高手答**：

先固定版本。以下基于 verl 官方 `main` 的 commit [`8df88be746801b6d87c42e15f9a5a0ec1d5eeeae`](https://github.com/verl-project/verl/blob/8df88be746801b6d87c42e15f9a5a0ec1d5eeeae/verl/experimental/agent_loop/agent_loop.py)（核对日期：2026-08-28）。官方 [Agent Loop 文档](https://verl.readthedocs.io/en/latest/advance/agent_loop.html)标明该能力从 v0.4.2 加入、状态为 alpha，API 仍可能变化，因此面试回答必须带版本。

它的定位是**多轮 Rollout 与 Agentic RL 训练之间的接口**：

```text
Trainer 取一个 Prompt Batch
  → AgentLoopManager 分发到 AgentLoopWorker
  → Worker 为每个样本实例化 AgentLoopBase
  → run coroutine 多次请求异步 LLM Server、调用 Tool/环境
  → AgentLoopOutput 返回 token、mask、logprob、turn、reward/metrics
  → Reward 与训练阶段消费轨迹并更新策略
```

这里有三类状态：

- **训练/样本状态**：样本索引、`agent_name`、policy/step 等轨迹元数据；
- **循环内状态**：消息、Tool 上下文、环境对象和终止条件，由具体 `AgentLoopBase.run` 实现管理；
- **训练输出状态**：`prompt_ids`、`response_ids`、`response_mask`、可选 logprobs/reward、多模态数据和指标。

Observation/Tool Result 会进入模型后续上下文，但不应被误当成策略生成 token；token mask 和 chat template 一致性直接影响训练正确性。AgentLoop 也不自动提供生产 Agent Runtime 的持久 Checkpoint、业务幂等或外部副作用恢复，这些是另一层责任。

扩展自定义 Loop 时，按官方 [How to Extend verl](https://verl.readthedocs.io/en/latest/extend_guide.html)继承 `AgentLoopBase` 并实现异步 `run`，通过配置注册；Tool 配置和生命周期是独立扩展面。实现必须保持 token-in/token-out，不能把 token decode 成文本、修改后再 encode，否则 Rollout token 与训练 logprob 对不上。异步 Worker 和多推理 Server 用于隐藏 Tool 等待并做请求级负载均衡，但并发数、最大轮数和 Tool 响应长度仍要设上限。

**差距在哪**：新手只看到 ReAct 循环，高手能说明 Manager/Worker/Base/Output 的责任、训练状态边界、扩展方法和 alpha API 风险。

---

## Q：Agent 状态放在 Sandbox 内、用户状态放在 Sandbox 外时，边界如何设计？

> 来源：[顺极 Agent 开发二面](https://www.nowcoder.com/feed/main/detail/93a26b84a6634558b7228bf350c709b5)

**新手答**：“临时状态放沙箱，长期用户信息放数据库，任务结束后销毁沙箱。”

**高手答**：

边界判断不是“临时/长期”两个词，而是**谁是事实源、Sandbox 丢失后能否恢复、数据是否允许进入不可信执行域**。

```text
Sandbox 内：工作区副本、临时文件、进程、编译缓存、本次 Tool 输入、短期日志
Sandbox 外：Run 事件、Checkpoint、用户画像、授权策略、Secret 引用、Artifact 索引、审计与租约
```

Kubernetes [Local Ephemeral Storage](https://kubernetes.io/docs/concepts/storage/ephemeral-storage/)明确提醒节点失败时本地临时数据可能丢失，所以 Sandbox 不是业务状态源。需要跨重启保留的文件先生成 manifest、hash 和 Artifact，再由控制面原子确认；只有确认后的引用才能进入 Checkpoint。

用户状态不能全量复制进 Sandbox。Context Builder 按当前任务和权限生成最小只读视图；敏感值尽量只给 opaque reference，需要调用外部系统时由凭证代理注入短期 token。Kubernetes [ServiceAccount 文档](https://kubernetes.io/docs/concepts/security/service-accounts/)同样推荐 TokenRequest/投射卷等短期、可轮换凭证，而不是长期静态 token。模型和沙箱内代码都不能决定最终 AuthZ。

状态提交采用 `run_id + state_version + execution_id`，Sandbox 只提出增量；控制面校验 lease、schema、权限和副作用后再提交。Sandbox 销毁时清理工作区、进程、挂载和凭据；复用池必须验证租户隔离，否则省下的冷启动会换来数据串扰。

**差距在哪**：新手按保存时长分层，高手按事实所有权、恢复语义和信任边界决定状态位置。

---

## Q：周期性 Agent 任务如何把 Schedule 与每次 Run 分离，并处理时区、漏跑、并发、幂等和失败通知？

> 来源：[淘宝闪购 AI 应用研发二面](https://www.nowcoder.com/feed/main/detail/09ec7c36a2774223a93044a02b2c3ec0)

**新手答**：“用定时器每隔一段时间触发 Agent，失败就重试和发告警。”

**高手答**：

`Schedule` 是可变更的触发契约，保存调度表达式、时区、有效期、漏跑策略、并发策略、任务模板和通知规则；每个 `Run` 是某个逻辑触发时刻生成的不可变执行实例，固定 `schedule_id + logical_fire_time`、输入、配置版本和执行状态。这样修改 Schedule 不会偷偷改写已经创建的 Run，历史也可以按逻辑触发时刻对账。

时区必须显式存 IANA 标识并定义 DST 重复或跳过时的行为，不依赖服务器本地时区。Scheduler 扫描逻辑时间窗口：对短时漏跑可限定 catch-up 窗口补跑，超窗口则记录 `MISSED` 并通知，避免恢复后瞬间补齐大量过期任务。并发策略至少区分 `ALLOW`、`FORBID` 和 `REPLACE`；`REPLACE` 仍要遵守取消语义，不能假定旧 Run 的外部副作用已撤销。

创建 Run 时以 `schedule_id + logical_fire_time` 建唯一约束，调度器用 lease/fencing 避免多实例重复创建；工具副作用再使用稳定 `execution_id` 做下游幂等。不宣称 exactly-once：失败按错误类型做有界重试，最终进入失败终态或人工队列。通知事件本身也带幂等键，包含最后成功时间、本次失败阶段、重试次数和下次触发时间。

这套语义可参考 Kubernetes [CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) 对时区、错过调度和并发策略的处理，但 Agent Runtime 仍需自己定义 Run 状态、Tool 幂等和通知收敛，不把设计绑定到某个调度框架。

**差距在哪**：新手只有“定时器 + 重试”，高手把配置和执行实例分开，并为时间语义、重复触发、重叠执行、副作用幂等和可操作告警定义了可恢复契约。

---

## Agent Infra 系统设计答题主线

```text
先定义：负载、SLO、信任边界、任务是否可暂停
再建模：状态机、事件、Checkpoint、lease、执行语义
再执行：Queue、Scheduler、Worker、Sandbox、Kubernetes
再兜底：幂等、UNKNOWN、对账、补偿、审批、恢复
最后治理：多租户、配额、Trace、Eval、Cost、Audit
```

记住一个结论：**Agent 带来了动态执行路径，但没有消灭分布式系统的部分失败；Runtime 必须把不确定性收敛成显式状态。**

下一篇建议继续看：

- [AI Infra：训练、推理与 GPU 平台工程](../17-ai-infra/index.html)
