
# Agent Infra：Runtime、Sandbox 与可靠执行

Agent Demo 能完成一次工具调用，不代表它能承受 Worker 重启、网络超时和几十万等待中的任务。Agent Infra 面试真正考察的是：当模型把执行路径变得动态以后，你能否继续用分布式系统方法保证副作用、状态和资源都可控。

这一章不把 `Gateway → Queue → Worker` 当作万能架构图，而是沿着可靠性边界追问：状态写到哪里、超时后能不能重试、Kubernetes 重建 Pod 后谁来恢复业务执行。

> **真实面经信号**：岗位名称不等于只考 Agent 概念。[阿里云 Agent Infra 一面](https://www.nowcoder.com/feed/main/detail/d1fd4cd344bc4d928e708c3e69c8f59c)同时考了 Go/Java、Spring Bean、gRPC、TCP、MySQL、Redis、RAG 和项目源码；另一篇[阿里云 Agent Infra 一面](https://www.nowcoder.com/feed/main/detail/1da22ebd6e8e47f4a775cae00f09ced0)考了缓存系统、并发编程与快速排序。准备这类岗位时，Runtime 设计和传统后端底座缺一不可。

---

## Q：Kubernetes Pod/Deployment 从提交到就绪经历哪些控制链路？

> 来源：[百度 AI Infra 校招面经](https://www.nowcoder.com/feed/main/detail/436228d68ccb4ec78d08644bc9227dec) / [虾皮 AI Infra 实习一面](https://www.nowcoder.com/feed/main/detail/e610f57cfd3548cd96a27d92e2f8b25e) / [虾皮 AI Infra 实习二面](https://www.nowcoder.com/feed/main/detail/62b9123e4b7f497285e7d6f68844cdd6)

**新手答**：“请求交给 API Server，Scheduler 选节点，Kubelet 拉起容器。”

**高手答**：

客户端请求先经过 API Server 的鉴权、准入和校验，再持久化到 etcd。Deployment Controller 通过 watch/Informer 观察期望状态并创建 ReplicaSet，ReplicaSet 再创建 Pod。Scheduler 为未绑定 Pod 做过滤、评分并写入节点绑定；目标节点上的 Kubelet 调用 CRI 拉镜像和启动容器，按声明协调 CSI 存储与 CNI 网络。探针通过后 Pod 才 Ready，Service 对应的 EndpointSlice 随之更新。

这是一组异步、最终一致的 Reconcile，不是一条同步 RPC。CSI、CNI 的具体调用位置还受运行时、插件和 Kubernetes 版本影响，回答时应说明组件责任，不硬背一条固定时序。

**差距在哪**：新手背组件顺序，高手能讲清对象所有权、watch/reconcile、调度绑定与数据面就绪的边界。

---

## Q：Agentic RL 采用同步还是异步 Rollout，如何权衡吞吐与稳定性？

> 来源：[美团 AI Infra 实习面经](https://www.nowcoder.com/feed/main/detail/c94734d67c9f461ab950bf1d800c5643) / [百度 AI Infra 实习面经](https://www.nowcoder.com/feed/main/detail/4a848f5616cf4f8783020b3143a68fbc) / [AI Infra 实习面经](https://www.nowcoder.com/feed/main/detail/166e576d5afa4a298cf9492ed51bed04)

**新手答**：“异步能让 GPU 不空闲，所以一定比同步好。”

**高手答**：

同步 Rollout 接近 on-policy、批次边界清楚，但慢请求和阶段屏障容易让 Learner 或推理资源空转。异步可以重叠采样与训练，提高吞吐，却会产生 Policy Lag：轨迹来自旧策略，版本差越大，偏差和训练不稳定风险越高。

工程上要给轨迹标记 `policy_version`，设置最大滞后和有界队列，对过旧样本丢弃、降权或重采；是否使用重要性采样、裁剪等校正必须服从具体算法，不能套一个万能公式。监控应同时看版本滞后分布、队列等待、有效样本量、KL、吞吐和 Reward，而非只看 MFU。

**差距在哪**：新手只看吞吐，高手能把调度产生的数据陈旧性连接到算法偏差，并给出可观测门槛。

---

## Q：Agent 调用 Sandbox 的链路如何容错？Sandbox 运行中崩溃后怎么恢复？

> 来源：字节 AML / 火山方舟 AI Infra 一面（2026-08-26）

**新手答**：“让 Kubernetes 重启 Pod，再从 Checkpoint 继续执行。”

**高手答**：

先把 Sandbox 执行建模成带 `execution_id`、attempt 和 lease 的状态机：`PENDING → DISPATCHED → RUNNING → SUCCEEDED/FAILED/UNKNOWN`。调度前持久化执行意图，Sandbox 启动后上报心跳，并持续外传 stdout、错误、资源指标和 Artifact；Runtime 设置启动、空闲、单工具和全局 Deadline，不能等 HTTP 连接自然超时才发现崩溃。

Sandbox 退出时区分正常非零码、OOM、硬超时、节点丢失和控制面失联。只读或幂等动作可在新的一次性环境中重试；可能已产生外部副作用但结果未提交时标记 `UNKNOWN`，先按幂等键查询或对账，不能盲目重放。恢复使用不可变镜像、输入 Artifact 和最近 Checkpoint，不复用可能残留进程、文件或凭据的脏环境。

Kubernetes 只负责重建计算实例，Agent Runtime 才负责业务状态恢复。控制面还要回收孤儿 Pod、过期 lease、临时卷和短期凭据；在途取消必须传播到 Sandbox，终止后拒绝过期 Worker 提交结果。观测上分别统计启动失败、OOM、超时、节点故障、UNKNOWN 副作用和恢复成功率。

**差距在哪**：新手把 Pod 重启等同于任务恢复，高手能处理状态提交、未知副作用、环境重建和孤儿资源回收四个故障边界。

---

## Q：一次 Agent 请求的完整执行链路是什么？

> 来源：[字节跳动 Agent 后端开发业务终面](https://www.nowcoder.com/feed/main/detail/1dd33c4b7bda453a82f7d645bde7f3ff) / Agent Runtime 完整管线设计高频题【字节火山引擎 Managed Agent 一面同题】

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

## Q：如果让你设计一个 Agent Runtime，你会怎么拆？

> 来源：Agent Infra / 平台工程系统设计高频题

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

生产目标通常是 **at-least-once 调度 + 幂等副作用**，而不是轻易承诺 exactly-once。还要为每个 Run 固定模型、Prompt、Tool 和策略版本，否则恢复后可能在另一套行为定义上继续执行。

**差距在哪**：新手罗列组件，高手先定义执行语义，再说明状态所有权、并发控制和版本边界。

---

## Q：为什么需要 Checkpoint，恢复时从哪里继续？

> 来源：长任务恢复与状态管理高频题

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

**差距在哪**：新手把 Checkpoint 当消息快照，高手能处理快照之后的事件、并发恢复和不确定副作用。

---

## Q：Tool 已成功但 Runtime 在写状态前宕机，如何避免重复副作用？

> 来源：分布式幂等与部分失败高频题

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

> 来源：[荣耀 AI Infra 一面](https://www.nowcoder.com/feed/main/detail/60ab2e3a45074b7391199acb9b5c6ca3) / [百度 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/436228d68ccb4ec78d08644bc9227dec) / 代码执行与隔离设计高频题

**新手答**：“Docker 有 Namespace 和 Cgroup，可以安全运行模型生成的代码。”

**高手答**：

Sandbox 运行的是不可信代码，目标不只是限制 CPU 和内存，还要控制文件系统、网络、系统调用、凭据、进程树、磁盘和执行时间。容器共享宿主机内核，隔离强度取决于 user namespace、capabilities、seccomp、SELinux/AppArmor 和宿主配置，不能把“用了 Docker”直接等同于安全。

| 场景 | 可选隔离 | 主要代价 |
|------|---------|---------|
| 内部只读工具 | 加固容器 | 隔离较轻，启动快 |
| 多租户代码执行 | gVisor / Kata | 兼容性或启动开销 |
| 高风险不可信代码 | MicroVM | 镜像、池化和运维成本 |

无论采用哪种方案，都应使用短期身份、只读根文件系统、默认拒绝网络、资源上限和硬 Deadline。复用预热 Sandbox 可以降低冷启动，但必须证明租户间文件、进程、缓存和凭据已经清理；高风险任务更适合一次性销毁环境。

进程地址空间隔离只能阻止普通进程直接读取彼此内存，不等于完整安全边界；容器仍要面对共享内核、错误授权和网络外泄等攻击面。Namespace 负责隔离“看见什么”，Cgroup 负责约束“能用多少”，两者也都不能替代系统调用和身份权限控制。

**差距在哪**：新手只比较容器技术名称，高手从威胁模型、信任等级和清理边界选择隔离方案。

---

## Q：Kubernetes 在 Agent Infra 中负责什么？

> 来源：Kubernetes 调度与 Controller 高频题

**新手答**：“负责创建 Pod、自动扩容和故障迁移。”

**高手答**：

Kubernetes 管的是计算实例和资源期望状态，不负责恢复 Agent 的业务状态。Pod 被重建以后，Run 能否继续取决于外部状态、lease、Checkpoint 和工具幂等。

它适合承担 Worker/Sandbox 生命周期、资源请求与限制、节点选择、弹性伸缩、ServiceAccount 和 NetworkPolicy。Controller 的 Reconcile 是 level-triggered：每次都根据 Desired State 和 Actual State 收敛，必须能处理重复事件、缓存陈旧和部分成功。

“一个 Agent 一个 Pod”还会带来 API Server/etcd 对象规模、Scheduler 吞吐、镜像拉取、IP 消耗、资源碎片和回收压力。短任务可以使用 Worker Pool 或预热 Sandbox；强隔离任务可以保留一任务一环境，但要通过池化和容量规划控制冷启动。

**差距在哪**：新手把 Kubernetes 当业务恢复系统，高手明确基础设施重调度与 Agent 状态恢复的责任边界。

---

## Q：如何支撑几十万并发 Agent Task，并把它观测清楚？

> 来源：高并发调度与 Agent Observability 高频题

**新手答**：“用 MQ 解耦，再水平扩容 Worker，接入日志、指标和链路追踪。”

**高手答**：

我会先澄清“几十万并发”是活跃会话、等待任务还是同时计算，并给出到达率、平均步骤数、各阶段耗时和 SLO。大量 Run 可能在等待 LLM、Tool 或人工事件，不能都占用 Worker。

控制面按租户、优先级和资源类型分队列；用 visibility timeout/lease、ack、DLQ 和毒任务隔离保证消费；用 weighted fair scheduling、并发配额和 admission control 防止大租户挤占资源；对 LLM、GPU 和外部 Tool 分别实施背压，而不是只按 CPU 扩容。

一个 Run 是根 Trace，模型、检索、工具、Sandbox 和状态提交是 Span。核心指标包括任务语义成功率、基础设施失败率、队列等待、端到端延迟、步骤数、Token/Cost 和 `UNKNOWN` 副作用数。Prompt、Tool 参数和结果可能包含隐私，必须脱敏、采样、分级存储和审计，不能直接放进高基数 Metrics Label。

**差距在哪**：新手会画 Queue + Worker，高手先定义负载模型，并同时处理公平性、下游瓶颈和可观测数据治理。

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
