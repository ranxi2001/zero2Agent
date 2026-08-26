---
layout: default
title: AI Infra：训练、推理与 GPU 平台工程
description: 拆解训练平台、推理服务、GPU 调度与 AIOps
eyebrow: Agent 面试通关 / 17
---

# AI Infra：训练、推理与 GPU 平台工程

AI Infra 不是“给 Kubernetes 加几台 GPU”。模型训练关心吞吐、Checkpoint 和集合通信，在线推理关心首 Token 延迟、批处理和容量水位，Agent 又会带来长上下文、突发 Tool 回调和多模型路由。面试官要看的是你能否把模型特性翻译成资源、调度和 SLO。

本章把 AI Infra 分成训练平台、推理平台、数据与制品平台、资源控制面和可观测/AIOps，而不是把训练与在线服务混在一张架构图里。

---

## Q：CUDA 的 Thread、Warp、Block、Grid 和 SM 如何映射？SIMT、同步与 Warp 分歧如何影响性能？

> 来源：[小马智行 AI Infra 实习面经](https://www.nowcoder.com/feed/main/detail/0e543b8a02b84b05950e55851687450f)、[OPPO AI Infra 实习一面](https://www.nowcoder.com/feed/main/detail/d8bc7618c7234ca8b67d18866ddc4542)、[蔚来 AI Infra 实习面经](https://www.nowcoder.com/feed/main/detail/738d29de77ef4675bbac0a7d18ed1371)、[沐曦 AI Infra 实习一面](https://www.nowcoder.com/feed/main/detail/5f3629b12be346de8dbc954a75d0990f)

**新手答**：“Grid 里有很多 Block，Block 里有很多 Thread，线程越多性能越好。”

**高手答**：

Kernel 启动后形成 Grid，Block 被调度到 SM；Block 内线程再按 Warp 成组执行。SIMT 表示同一 Warp 的线程共享指令推进，但各自维护寄存器和地址：分支条件不同会用不同活动掩码分段执行，形成分歧；地址不连续则可能增加内存事务。`__syncthreads()` 只解决 Block 内屏障，普通 Kernel 不能假设不同 Block 同时驻留并直接做全局屏障，跨 Block 阶段通常要拆 Kernel，或在满足约束时使用 Cooperative Groups。调优不能只追求 Occupancy：寄存器、Shared Memory 和 Block 大小会共同限制驻留量，最终要看有效吞吐、访存合并和延迟隐藏。

**差距在哪**：新手只会背层级，高手能把调度范围、同步边界、分支与访存行为连接到真实性能。

---

## Q：如何用 Roofline 和算术强度指导 CUDA 算子优化？从 GEMM 分块到寄存器压力如何逐层定位？

> 来源：[美团北斗 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/841452f926a140babb84585de97c04aa)、[拼多多 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/9e1f4f4b8642496e85cf7802d03112df)、[小鹏 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/a79383aa92f64e8eb4e85959bf2660a0)、[快手 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/c582fdfbc29d4c93ac9044005ad0a311)、[飞腾 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/90c405df0a0f4dd99298768496b0c942)、[字节 AI Infra 二面](https://www.nowcoder.com/feed/main/detail/eaea5cf9e9e44c5bb5fecf3f1d8243ce)、[太初 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/45c0b82115024f16a88ad9a37f2ab398)、[壁仞 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/5baf1aaa7ff646a8a38d9c7ece43a808)、[寒武纪 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/7dfe46da13ad4ae8a3dd94c3ca7f5d05)

**新手答**：“多用 Shared Memory、增加线程数，再做算子融合。”

**高手答**：

先以 `算术强度 = FLOPs / 搬运字节数` 判断 Kernel 更可能受计算峰值还是内存带宽约束，再用 Profiler 验证。Memory-bound 时优先检查合并访问、分块复用、向量化、减少中间写回和 Fusion；Compute-bound 时再看 Tensor Core 路径、数据布局和指令流水。GEMM 的 Tile 不能越大越好：更大的复用也会增加寄存器和 Shared Memory，占用过高可能降低驻留 Block，甚至发生 Register Spill。可靠流程是先建立正确 Baseline，再测不同 Shape，定位瓶颈、提出单一假设、微基准验证，并检查数值误差。前缀和、Reduce、Softmax、转置等手撕题都应沿这条方法回答。

**差距在哪**：新手堆优化技巧，高手先建立性能模型，再用证据决定优化顺序并守住正确性。

---

## Q：如何从模型结构估算参数量、FLOPs、训练显存、推理访存与 MFU？

> 来源：[美团北斗 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/841452f926a140babb84585de97c04aa)、[混元 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/2a9106374f0842c6af57cdb3acb51190)、[讯飞飞星 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/aed72ed951f54745b240e723df9a9f96)、[荣耀 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/59dece94af144cba94157481f2e2b5ce)、[AI Infra 小厂面经](https://www.nowcoder.com/feed/main/detail/166e576d5afa4a298cf9492ed51bed04)、[字节 AI Infra 二面](https://www.nowcoder.com/feed/main/detail/eaea5cf9e9e44c5bb5fecf3f1d8243ce)

**新手答**：“参数量乘数据类型字节数就是显存，FLOPs 越高训练越慢。”

**高手答**：

先写模型形状，再分对象核算。参数量由 Embedding、Attention 投影、FFN/Expert 和输出头组成；FLOPs 要区分训练、Prefill 与 Decode，并明确是否把乘加计作一次或两次操作。训练显存不只有权重，还包括梯度、优化器状态、Master Weight、激活、通信缓冲、临时 Workspace 和碎片；推理还要加入 KV Cache、Batch 与上下文长度。推理访存则关注每 Token 需要读取的权重、KV 和中间结果。MFU 应写成“实际有效模型计算吞吐 / 选定硬件峰值”，同时声明稀疏 MoE、重计算、Padding 和精度口径。最终用实测 Profile 校准估算，而不是拿理论峰值直接当容量结论。

**差距在哪**：新手只算权重，高手能声明口径、覆盖隐藏内存，并按执行阶段建立可校准的成本模型。

---

## Q：Prefill 与 Decode 的算子形态和瓶颈为何不同？Matmul、KV 传输和量化应如何分别优化？

> 来源：[小马智行 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/0e543b8a02b84b05950e55851687450f)、[阿里云 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/87e2d275ec62435ca036b6a99eb972be)、[荣耀 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/59dece94af144cba94157481f2e2b5ce)、[vLLM/SGLang 小厂面经](https://www.nowcoder.com/feed/main/detail/c7eee5b04fb8424aa4847f0e21fab875)、[腾讯 CDG AI Infra 面经](https://www.nowcoder.com/feed/main/detail/6bbfaca62dc64d45851f3ea6c48ff168)、[爱奇艺 AI 平台研发面经](https://www.nowcoder.com/discuss/918635351327924224)

**新手答**：“Prefill 是计算密集，Decode 是访存密集，所以前者加算力、后者加带宽。”

**高手答**：

Prefill 一次处理多个输入 Token，矩阵通常更大、并行度更高，Attention 还随序列长度增加，因此更容易有效使用矩阵计算单元；Decode 每步只生成少量 Token，常表现为小 GEMM/GEMV，并反复读取权重和持续增长的 KV Cache，更受带宽、调度和单步延迟影响。但这只是工作负载判断，不是所有模型和 Batch 下的定律。Prefill 可从 FlashAttention、分块、张量并行和长 Prompt 准入入手；Decode 更依赖 Continuous Batching、KV 布局/量化、算子融合和投机采样。量化是否提速还要看对应 Shape 是否有高效 Kernel，以及反量化开销。验证时分别看 TTFT、TPOT、算力与带宽指标。

**差距在哪**：新手背阶段标签，高手从矩阵形状和数据移动推导瓶颈，再为两个阶段选择不同优化。

---

## Q：如何估算 All-Reduce/All-to-All 通信量并实现计算通信重叠？拓扑和 RDMA 如何影响结果？

> 来源：[阶跃星辰 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/320def38cd484da3bb26b01932996ef2)、[快手 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/eccb5cafdfce452c8d56374ef070685d)、[字节 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/b99b6a7c7ff54453a2451d43488ade5a)、[AI Infra 小厂面经](https://www.nowcoder.com/feed/main/detail/166e576d5afa4a298cf9492ed51bed04)、[数坤科技 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/f6b2716a6e1b4c0f96564ca06af3609b)、[阿里控股 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/7d75c82afe80416ea8a489a18b79b144)、[爱奇艺 AI 平台研发面经](https://www.nowcoder.com/discuss/918635351327924224)

**新手答**：“All-Reduce 用 Ring，通信和反向计算异步执行就能隐藏开销。”

**高手答**：

先从并行切分推导每次 Collective 的参与组、Payload 和依赖，再用 `通信时间 ≈ 启动时延 × 轮次 + 字节数 / 有效带宽` 建模。All-Reduce 常用于聚合梯度或 TP 部分结果；MoE 的 All-to-All 还会受 Token 路由不均和 Straggler 影响。重叠不是简单开异步：只有某个 Bucket 已就绪且后续计算不依赖其结果时，才能用独立 Stream/通信引擎覆盖，并要防止计算和通信争抢同一带宽。实际性能还取决于 NVLink/NVSwitch、PCIe、NUMA、跨机网络和 RDMA 路径。最终用 Timeline 检查依赖与空洞，并按拓扑选择分组、Bucket 和 Collective 算法。

**差距在哪**：新手只背通信算子，高手能从张量形状估量、识别依赖，并用真实拓扑验证重叠。

---

## Q：MoE 的 Expert Parallel 如何做 Dispatch/Combine、负载均衡和通信优化？DeepEP/EPLB 分别解决什么问题？

> 来源：[阿里 AI Infra 实习面经](https://www.nowcoder.com/feed/main/detail/31edaaa47197404a8647601612312786)、[美团 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/c94734d67c9f461ab950bf1d800c5643)、[快手 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/12a74831ffa543cb9117c646faf214fd)、[vLLM/SGLang 小厂面经](https://www.nowcoder.com/feed/main/detail/c7eee5b04fb8424aa4847f0e21fab875)、[字节 AI Infra 二面](https://www.nowcoder.com/feed/main/detail/eaea5cf9e9e44c5bb5fecf3f1d8243ce)、[阿里控股 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/7d75c82afe80416ea8a489a18b79b144)、[爱奇艺 AI 平台研发面经](https://www.nowcoder.com/discuss/918635351327924224)

**新手答**：“Router 把 Token 发给不同 Expert，用 All-to-All 通信，再把结果合回来。”

**高手答**：

Router 产生 Top-K Expert 选择后，Runtime 先按目标 Rank 对 Token 打包并 Dispatch，经 Expert GEMM 计算，再按原 Token 顺序 Combine。真正瓶颈常是路由倾斜：热点 Expert 让部分 Rank 过载，其他 Rank 等待，All-to-All 还会放大跨节点流量。治理要同时考虑训练侧的负载均衡目标、容量与丢弃策略，以及推理侧的 Expert 放置、复制、动态迁移和拓扑感知。DeepEP 侧重为 MoE Dispatch/Combine 提供高效通信能力，EPLB 侧重依据负载调整 Expert 布局；具体接口和算法随版本变化，应查官方实现。评测必须同时看吞吐、尾延迟、丢弃率、负载偏斜和通信占比。

**差距在哪**：新手只知道 EP 等于 All-to-All，高手能把路由、布局、通信与 Straggler 串成闭环。

---

## Q：CPU、GPU 与 NPU 的体系结构和优化目标有什么差异？如何为训练/推理工作负载选硬件？

> 来源：[蔚来 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/7cb7ccbb4a3145cf99dbb05aff767299)、[快手 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/eccb5cafdfce452c8d56374ef070685d)、[美团北斗 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/841452f926a140babb84585de97c04aa)、[讯飞飞星 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/aed72ed951f54745b240e723df9a9f96)、[小鹏 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/953ea04c2c5d420fa1e04db93bb2a5a4)、[荣耀 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/59dece94af144cba94157481f2e2b5ce)、[太初 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/45c0b82115024f16a88ad9a37f2ab398)

**新手答**：“CPU 擅长串行，GPU 擅长并行，NPU 专门跑 AI，所以 NPU 效率最高。”

**高手答**：

CPU 用较少但复杂的核心、较强缓存和分支预测换低延迟与通用控制能力；GPU 用大量并行执行资源和高显存带宽追求吞吐，要求足够并行度与适合的数据布局；NPU 通常围绕矩阵/张量数据流和特定低精度路径设计，但通用算子与动态控制能力取决于具体芯片和软件栈。选型不能只比峰值 FLOPS/TOPS，还要看模型算子覆盖、精度支持、显存容量/带宽、互联拓扑、编译器和 Kernel 成熟度、部署可用性及 TTFT/TPOT SLO。H100、A100、昇腾等只能作为带明确型号、软件版本和实测负载的案例，不能用代际标签替代 Benchmark。

**差距在哪**：新手按设备标签判断强弱，高手按工作负载、软件生态和端到端 SLO 做条件化选型。

---

## Q：FP8、NVFP4、INT8 与 W4A16 的数值格式、缩放粒度和硬件执行路径有何不同？

> 来源：[混元 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/2a9106374f0842c6af57cdb3acb51190)、[讯飞飞星 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/aed72ed951f54745b240e723df9a9f96)、[AI Infra 小厂面经](https://www.nowcoder.com/feed/main/detail/166e576d5afa4a298cf9492ed51bed04)、[智谱 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/846a09e34fea4fe9a7e14da2a88e3f72)、[摩尔线程 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/a908b218f4824f2bbae0dc8262aadf8c)

**新手答**：“位宽越低越省显存、速度越快，FP8 比 INT8 精度更好。”

**高手答**：

先区分存储格式、计算格式和累加格式。INT8 是定点量化，真实值由整数与 Scale/Zero Point 共同表达；W4A16 表示权重低位存储而激活保留较高精度，执行时可能需要解包和反量化。FP8 是低位浮点格式家族，不同指数/尾数分配在动态范围与精度间取舍；NVFP4 等格式还会绑定特定的分块缩放和硬件路径。Per-Tensor、Per-Channel、Per-Group 或更细粒度会影响 Scale 元数据、Kernel 复杂度和误差。最终收益取决于目标设备是否原生支持对应输入、乘法与累加路径，以及框架能否为实际 Shape 选择高效 Kernel；格式名称本身不能证明端到端更快。

**差距在哪**：新手只比较位宽，高手会核对 Scale、Accumulator、Kernel 和硬件支持组成的完整执行契约。

---

## Q：量化后为什么不一定更快？量化 Matmul、反量化、Prefill 和 Decode 的瓶颈如何判断？

> 来源：[美团北斗 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/841452f926a140babb84585de97c04aa)、[拼多多 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/9e1f4f4b8642496e85cf7802d03112df)、[混元 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/2a9106374f0842c6af57cdb3acb51190)、[爱奇艺 AI 平台研发面经](https://www.nowcoder.com/discuss/918635351327924224)

**新手答**：“量化减少权重和显存占用，所以所有阶段都会更快。”

**高手答**：

量化首先减少存储和搬运字节数，但端到端速度还取决于计算路径。若硬件与 Kernel 原生支持该格式，Decode 这类频繁读取权重、带宽敏感的阶段更可能受益；Prefill 的大矩阵计算利用率较高，收益可能受反量化、Scale 读取、数据重排和累加格式限制。某些 Batch、Shape 或算子没有合适 Kernel 时还会回退到较高精度，甚至增加转换和 Launch 开销。排查时先确认实际选中的 Kernel 与输入格式，再分别测权重带宽、反量化占比、Tensor Core/矩阵单元利用、TTFT、TPOT 和端到端成本，同时做质量回归。结论必须绑定模型、硬件、框架版本和流量分布。

**差距在哪**：新手把压缩率等同于加速比，高手能沿真实数据路径解释量化收益为何因阶段和实现而异。

---

## Q：GPU 内存层次如何使用？Pinned Memory、Shared Memory、Bank Conflict 与异步 H2D/D2H 分别解决什么问题？

> 来源：[阿里国际 AI Infra 实习面经](https://www.nowcoder.com/feed/main/detail/6cbfd441972d4a96ae47e1cdf54a3fef)、[阶跃星辰 AI Infra 实习面经](https://www.nowcoder.com/feed/main/detail/320def38cd484da3bb26b01932996ef2)、[快手 AI Infra 校招面经](https://www.nowcoder.com/feed/main/detail/eccb5cafdfce452c8d56374ef070685d)、[蔚来 AI Infra 实习面经](https://www.nowcoder.com/feed/main/detail/738d29de77ef4675bbac0a7d18ed1371)、[文远知行 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/cc35269c89d645c3a510c22504355ce0)、[寒武纪 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/7dfe46da13ad4ae8a3dd94c3ca7f5d05)

**新手答**：“把 Global Memory 数据搬到 Shared Memory 就会更快，Pinned Memory 可以加速拷贝。”

**高手答**：

优化目标是减少高代价数据移动并提高复用。寄存器最靠近线程，Shared Memory 由 Block 显式共享，L2/显存容量更大但访问代价更高；只有数据会被重复使用且分块、同步成本可摊薄时，搬进 Shared Memory 才有收益。Bank Conflict 会让同一 Warp 的某些 Shared Memory 访问产生额外事务，具体映射要按目标架构验证。Pinned Host Memory 便于 DMA 和异步传输，但会占用不可分页的主机内存。H2D、Kernel、D2H 能否重叠，还取决于设备 copy engine、独立 Stream、锁页缓冲区和正确的事件依赖，不能只调用异步 API 就认定已经并行。

**差距在哪**：新手把内存类型当速度排名，高手会按复用、事务、同步和软硬件条件判断收益。

---

## Q：FlashAttention 为什么更快？Online Softmax、Tiling、重计算和不同版本分别解决什么瓶颈？

> 来源：[阿里国际 AI Infra 实习面经](https://www.nowcoder.com/feed/main/detail/6cbfd441972d4a96ae47e1cdf54a3fef)、[快手 AI Infra 校招面经](https://www.nowcoder.com/feed/main/detail/eccb5cafdfce452c8d56374ef070685d)、[美团北斗 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/841452f926a140babb84585de97c04aa)、[混元 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/2a9106374f0842c6af57cdb3acb51190)、[科大讯飞 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/140a45bc0b314798a0d94b512cb7ea90)、[飞腾 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/90c405df0a0f4dd99298768496b0c942)、[阿里校招 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/84dc13404a6048c7b0f8431179d33623)、[爱奇艺 AI 平台研发面经](https://www.nowcoder.com/discuss/918635351327924224)

**新手答**：“FlashAttention 把复杂度从平方降到线性，所以显存更少、速度更快。”

**高手答**：

FlashAttention 的核心是 IO-aware，而不是把稠密 Attention 的数学计算复杂度改成线性。标准实现会把较大的 Score/Probability 中间矩阵写入显存；FlashAttention 对 Q、K、V 分块，在片上存储中完成局部计算，并用 Online Softmax 维护每行的运行最大值和归一化和，从而避免完整中间矩阵落到高带宽内存。反向阶段可通过保存少量统计量并重计算部分结果，交换存储与计算。不同版本主要继续改进工作划分、并行度、流水和新硬件能力利用，具体支持受 GPU 架构、数据类型、Head Dimension 和软件版本约束，必须以原论文和官方实现为准。

**差距在哪**：新手只背“省显存”，高手能推导 Online Softmax 的正确性，并区分 FLOPs 与 IO 复杂度。

---

## Q：流水线并行的 Bubble 从哪里来？1F1B、Zero-Bubble 与 DualPipe 如何调度？

> 来源：[快手 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/eccb5cafdfce452c8d56374ef070685d)、[百度 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/4a848f5616cf4f8783020b3143a68fbc)、[美团 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/c94734d67c9f461ab950bf1d800c5643)、[AI Infra 小厂面经](https://www.nowcoder.com/feed/main/detail/166e576d5afa4a298cf9492ed51bed04)

**新手答**：“把 Batch 切成 Micro-batch，前后向流水起来，就能消除 GPU 空闲。”

**高手答**：

流水线并行把层分到不同 Stage，Micro-batch 在 Stage 间传递；启动时下游无输入、排空时上游无工作，再加前后向依赖和 Stage 不均衡，就形成 Bubble。1F1B 在预热后交替执行一次前向和一次反向，通常比先做完全部前向再反向更早释放部分激活，但仍有填充/排空成本。Zero-Bubble 会进一步拆分并重排反向阶段，DualPipe 则利用双向流水提高重叠；两者的精确定义和可行依赖应以对应论文/实现为准。选型时同时核算 Stage 平衡、Micro-batch 数、激活峰值、跨 Stage 通信和调度复杂度，不能只比较理论 Bubble 比例。

**差距在哪**：新手只会画流水线，高手能解释空泡来源、依赖约束和显存/通信取舍。

---

## Q：CUDA、Triton、CUTE 与 MLIR 分别位于什么抽象层？算子编译链和选型依据是什么？

> 来源：[拼多多 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/9e1f4f4b8642496e85cf7802d03112df)、[小马智行 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/0e543b8a02b84b05950e55851687450f)、[飞腾 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/90c405df0a0f4dd99298768496b0c942)

**新手答**：“CUDA 最底层、Triton 更简单、MLIR 是编译器，所以追求性能就手写 CUDA。”

**高手答**：

这些概念不在同一维度。CUDA C++ 让开发者显式控制线程、内存和同步，通常经前端编译到 PTX，再由工具链生成目标 GPU 指令；Triton 是面向并行张量程序的 DSL，由编译器完成一部分映射与优化；CUTE 提供更细的 Layout、Tile 和数据搬运组合抽象，可服务高性能 Kernel 构建；MLIR 则是一套多层中间表示与 Pass 基础设施，常用于连接图级、算子级和硬件级降级。选型要同时看目标硬件、算子规则性、动态 Shape、已有 Kernel、性能差距、调试可观测性和维护成本。高层 DSL 达不到目标时再逐层下沉，并用同一正确性与基准口径比较。

**差距在哪**：新手把工具排成高低级排名，高手理解编译链、控制权和工程成本之间的交换关系。

---

## Q：Stride、View/Contiguous 与 NHWC/NCHW 如何影响张量算子的正确性和性能？

> 来源：[字节 AI Infra 实习面经](https://www.nowcoder.com/feed/main/detail/b99b6a7c7ff54453a2451d43488ade5a)、[荣耀 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/59dece94af144cba94157481f2e2b5ce)、[OPPO AI Infra 二面低置信截断稿](https://www.nowcoder.com/feed/main/detail/101e205200ab480db5677ee2852e7d91)

**新手答**：“Transpose 后调用 `contiguous()`，GPU 用 NCHW、CPU 用 NHWC。”

**高手答**：

张量由 Storage、Shape、Stride 和 Offset 共同定义；Transpose 往往只改元数据，因此逻辑连续不等于物理连续。`view` 只有在现有 Stride 可表达目标形状时才能零拷贝，`reshape` 可能返回 View，也可能物化新内存；`contiguous()` 会按指定内存格式复制，能满足 Kernel 契约，但也可能引入昂贵搬运。布局选择要看算子的遍历维度、Warp 访问是否合并、向量化、Tensor Core/矩阵单元要求和上下游转换次数。NHWC/NCHW 没有脱离硬件与框架的固定胜负：应尽量让整段算子链保持兼容布局，并用 Profile 确认布局转换没有吞掉 Kernel 收益。

**差距在哪**：新手背框架口诀，高手能从 Storage/Stride 推导零拷贝条件，并把布局选择放回完整算子链评估。

---

## Q：Attention 与 FFN 的计算量和参数量谁更大？

> 来源：[阿里云 AI Infra 一面](https://www.nowcoder.com/feed/main/detail/a2ba1ef152ea4328a9f2d30baadd78f8)、[百度 AI Infra 一面](https://www.nowcoder.com/feed/main/detail/09c161adbf1f459f8e2799d908321420)

**新手答**：“Attention 是平方复杂度，所以一定比 FFN 大。”

**高手答**：

不能脱离形状直接下结论。忽略常数后，Self-Attention 的投影约为 `O(B × S × H²)`，注意力矩阵计算约为 `O(B × S² × H)`；两层 FFN 约为 `O(B × S × H × I)`，其中中间维度 `I` 常是 `H` 的数倍。短序列、大隐藏维度时 FFN 可能占更多 FLOPs；序列足够长时，Attention 的 `S²` 项才会主导。

参数量同样主要取决于投影矩阵：标准 Attention 约为 `4H²`，FFN 约为 `2HI`，若 `I≈4H`，FFN 参数通常更多。GQA、MLA、MoE、门控 FFN 和稀疏激活都会改变公式。单请求 Decode 的矩阵形状还可能更接近 GEMV，而训练、Prefill 或批量 Decode 通常仍可组织成 GEMM；最终要以真实 batch、序列长度和 Profiler 为准。

**差距在哪**：新手只背复杂度标签，高手先写出维度和工作负载，再判断参数、算力与访存瓶颈。

---

## Q：KV Cache 占用如何计算，为什么不能只按请求数做容量规划？

> 来源：[抖音搜推 AI Infra 一面](https://www.nowcoder.com/feed/main/detail/e5f1a15d50414c86a0e64f2dbc13a02f)、[百度 AI Infra 一面](https://www.nowcoder.com/feed/main/detail/05c5fe23173245a4ab39b3dddf2b95bb)

**新手答**：“KV Cache 和上下文长度成正比，显存不够就减少并发。”

**高手答**：

对常见 Decoder-only 模型，可以从下面的近似式开始估算：

```text
KV bytes ≈ 2 × layers × tokens × kv_heads × head_dim × bytes_per_element
总容量再乘以并发序列数，并加 block 尾部浪费、元数据和运行时预留
```

前面的 `2` 代表 K 和 V。MHA 中 `kv_heads` 通常等于 query heads；MQA/GQA 会减少 KV heads；MLA 的缓存结构要按具体实现重新计算，不能套同一个维度。Prefill 后每生成一个 Token 都继续增长 KV，因此相同请求数下，长上下文与长输出可能相差几个数量级。

生产准入应按预计 Token Budget、可回收 block 和租户 SLO 做，而不是只限制并发请求数。Paged KV 能减少连续分配和外部碎片，但仍有尾块浪费、页表元数据和间接寻址开销；Prefix Cache 还必须把模型、Tokenizer、Adapter 和模板版本纳入正确性边界。

**差距在哪**：新手只知道 KV Cache 占显存，高手能从模型结构算容量，并把分页、准入和缓存正确性连起来。

---

## Q：如何设计大模型在线推理服务？

> 来源：[百度 AI Infra 提前批一面](https://www.nowcoder.com/feed/main/detail/09c161adbf1f459f8e2799d908321420)、[智象未来 AI Infra 一面](https://www.nowcoder.com/discuss/920057298502811648)

**新手答**：“把模型加载到 GPU，通过 API 提供推理，再根据 QPS 自动扩容。”

**高手答**：

我会先定义 TTFT、TPOT、端到端 P99、吞吐、可用性和成本目标。LLM 推理分为 Prefill 和 Decode：长 Prompt 的 Prefill 偏计算密集，逐 Token Decode 更受内存带宽和 KV Cache 容量影响，因此不能只看请求 QPS。

Serving 层通常需要 continuous batching、流式输出、请求取消、长度感知调度和 KV Cache 管理。路由时考虑模型版本、上下文长度、预计输出、租户优先级、Deadline 和副本水位。过载时优先 admission control、排队上限和明确拒绝，不能让无限排队把 P99 拖垮。

自动扩容要观察队列时间、Token 吞吐、KV Cache 使用率和可用 GPU，而不是只看利用率；模型加载和权重分发很慢，因此还需要预热容量和发布期间的双版本资源预算。

**差距在哪**：新手把 LLM 当普通 HTTP 服务，高手理解 Prefill/Decode、动态批处理、KV Cache 与排队延迟。

---

## Q：CUDA Graph 为什么能降低推理开销？为什么可能额外占显存，Prefill 与 Decode 哪个阶段更适合？

> 来源：[小马智行 AI Infra 实习面经](https://www.nowcoder.com/feed/main/detail/0e543b8a02b84b05950e55851687450f)、[爱奇艺 AI 平台研发面经](https://www.nowcoder.com/discuss/918635351327924224)

**新手答**：“CUDA Graph 把多个 Kernel 合并起来，所以执行更快，通常用于 Decode。”

**高手答**：

CUDA Graph 不是算子融合，而是先捕获一段 Kernel、Memcpy 和依赖关系，再低开销重复提交，主要减少 CPU Launch、框架调度和同步间隙。Decode 每轮形状和执行拓扑较稳定，且小 Kernel 多，通常更容易从重放获益；Prefill 的长度和 Batch 变化大，可能要按 Shape 分桶、填充，或回退 Eager。额外显存常来自捕获期的稳定地址、私有内存池、不同 Shape 的多份 Graph 以及为最大形状预留的张量。是否值得使用要比较捕获/预热成本、命中率、显存水位和端到端 TPOT，而不是只看单次 Kernel 时间；具体捕获限制以 CUDA 与推理框架版本为准。

**差距在哪**：新手把 Graph 误解成 Fusion，高手能说明它优化的是提交路径，并量化动态形状和显存代价。

---

## Q：vLLM/SGLang 的请求调度与 Continuous Batching 如何工作？请求被抢占后如何恢复？

> 来源：[阿里国际 AI Infra 实习面经](https://www.nowcoder.com/feed/main/detail/6cbfd441972d4a96ae47e1cdf54a3fef)、[AI Infra 小厂面经](https://www.nowcoder.com/feed/main/detail/166e576d5afa4a298cf9492ed51bed04)、[vLLM/SGLang 小厂面经](https://www.nowcoder.com/feed/main/detail/c7eee5b04fb8424aa4847f0e21fab875)、[爱奇艺 AI 平台研发面经](https://www.nowcoder.com/discuss/918635351327924224)

**新手答**：“Continuous Batching 会不断把新请求塞进 Batch，所以 GPU 利用率更高。”

**高手答**：

调度器管理 Waiting、Running 等请求状态，并在每次迭代按可用 KV Block、Token Budget、优先级和 Deadline 选择工作。Decode 请求通常每轮推进少量 Token，长 Prefill 可切成 Chunk，与 Decode 交错，避免一次 Prefill 长时间阻塞其他请求；请求完成或取消后立即回收容量，新请求无需等待整批结束。容量不足时可能选择重计算、交换或重新排队，具体抢占与恢复策略依框架版本和配置，不能把某一版实现当协议。生产设计还要处理排队上限、长短请求公平性、取消传播和资源回收，并分别观察 Queue Time、TTFT、TPOT 与 KV 水位。

**差距在哪**：新手只说动态拼批，高手能讲清调度状态、预算、抢占代价与 SLO 公平性。

---

## Q：投机采样中 Draft 与 Target 模型如何交互？什么时候会加速，什么时候反而变慢？

> 来源：[AI Infra 小厂面经](https://www.nowcoder.com/feed/main/detail/c7eee5b04fb8424aa4847f0e21fab875)、[爱奇艺 AI 平台研发面经](https://www.nowcoder.com/discuss/918635351327924224)

**新手答**：“小模型一次预测多个 Token，大模型一起验证，因此输出不变且一定更快。”

**高手答**：

Draft 模型先提出一段候选 Token，Target 模型用一次并行前向验证；系统接受符合采样规则的前缀，在首次拒绝处按正确分布继续采样，再进入下一轮。性能取决于平均接受长度能否覆盖 Draft 推理、Target 验证、调度和 KV 管理成本。任务分布与 Draft 不匹配、Batch 很大、验证 Kernel 不高效或请求很短时，额外工作可能抵消收益。工程上还要处理两个模型的 Tokenizer/词表兼容、各自 KV Cache、拒绝后的状态回退、流式输出和请求取消。vLLM、SGLang 等框架支持的 Draft 方法与调度细节会迭代，回答时先讲算法契约，再按明确版本讨论实现。

**差距在哪**：新手只背“双模型加速”，高手能说明正确性边界、接受率成本模型和双份运行状态。

---

## Q：大模型训练吞吐低时，如何用 MFU、Profiler、通信和流水线空泡定位瓶颈？

> 来源：[大模型算法题整理（低置信二手来源）](https://www.nowcoder.com/feed/main/detail/c8eac6f9d7804a488b41c98128108e3a)、[阶跃星辰 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/320def38cd484da3bb26b01932996ef2)、[快手 AI Infra 面经](https://www.nowcoder.com/feed/main/detail/12a74831ffa543cb9117c646faf214fd)、[AI Infra 小厂面经](https://www.nowcoder.com/feed/main/detail/166e576d5afa4a298cf9492ed51bed04)

**新手答**：“先看 GPU 利用率，低了就增加 Batch、开启混合精度或换更多 GPU。”

**高手答**：

先固定模型、序列、全局 Batch、精度和并行拓扑，按 Step Time 拆成 DataLoader、前反向、Optimizer、Collective、流水线等待与 Checkpoint，而不是先调参数。MFU 只说明有效模型计算相对选定峰值的比例，必须声明稠密/MoE FLOPs、重计算和 Padding 口径；同时看每 Rank 时间线、算力/带宽指标、NCCL 时延、Stage 空泡、数据等待和 Straggler。若通信暴露，检查 Bucket、依赖和拓扑；若 Kernel 低效，再下钻 Shape、布局和算术强度；若只有少数 Rank 变慢，检查节点、数据倾斜与硬件健康。每次只改变一个变量并重复测量，用吞吐、稳定性和成本共同验收。

**差距在哪**：新手凭单个利用率调参，高手先建立可重复 Baseline，再逐层定位 Job、通信和 Kernel 瓶颈。

---

## Q：PD 分离解决什么问题，Prefill 与 Decode 资源比例怎么定？

> 来源：[百度 AI Infra 提前批一面](https://www.nowcoder.com/feed/main/detail/09c161adbf1f459f8e2799d908321420)、[百度 AI Infra 暑期一面](https://www.nowcoder.com/feed/main/detail/05c5fe23173245a4ab39b3dddf2b95bb)

**新手答**：“Prefill 计算密集、Decode 访存密集，所以把它们部署到不同 GPU。”

**高手答**：

PD 分离的目标是减少长 Prefill 对 Decode TPOT 的干扰，并让两类阶段独立批处理、扩容和选硬件。但拆分后必须传输或共享 KV Cache，引入网络带宽、序列化、调度、故障恢复和额外排队；小模型、短 Prompt 或低负载时，分离成本可能高于收益。

资源比例不能背固定数字，应由流量画像推导：Prompt/Output Token 分布、到达率、Prefill Token/s、Decode Token/s、TTFT/TPOT SLO、KV 传输成本和峰值余量。可以分别建立两个队列，用在线水位和 Deadline 调整路由；`chunked prefill` 也能在单集群内把长 Prefill 切块，与 Decode 迭代交错，是独立部署之外的另一种取舍。

压测必须覆盖长短请求混合、突发流量、跨节点 KV 传输和某一侧容量不足。只报告平均吞吐无法证明分离有效，还要比较 TTFT、TPOT、P99、GPU 利用率和每 Token 成本。

**差距在哪**：新手只说异构部署，高手会量化流量、传输代价、排队和 SLO，再决定是否分离及如何配比。

---

## Q：分布式训练为什么容易失败，如何恢复？

> 来源：[摩尔线程 AI Infra 一面](https://www.nowcoder.com/feed/main/detail/50b0cc495d594f51adbf05fd90cd896e)

**新手答**：“做数据并行，节点挂了就从 Checkpoint 重新训练。”

**高手答**：

训练失败可能来自 GPU Xid/ECC、节点重启、网络抖动、集合通信超时、数据坏样本、OOM 或软件版本不一致。先确定并行策略：数据并行、张量并行、流水线并行和参数分片解决的瓶颈不同，也引入不同通信和恢复成本。

Checkpoint 不只是模型权重，还可能包含 Optimizer、Scheduler、随机数状态、Sampler 进度和并行拓扑信息。保存频率需要权衡写入开销与重算成本：

```text
期望浪费 ≈ 故障概率 × Checkpoint 间隔内的平均重算量
```

大规模训练应采用异步或分层 Checkpoint、制品完整性校验和原子发布，避免读到半写文件。恢复前还要隔离疑似坏节点，并验证新的 world size 或并行拓扑是否被框架支持；“Pod 重启”并不自动等于训练可恢复。

**差距在哪**：新手只知道保存权重，高手能说明训练状态、通信故障、拓扑变化和 Checkpoint 成本模型。

---

## Q：GPU 利用率很低，但请求延迟很高，怎么排查？

> 来源：[小鹏 AI Infra 一面](https://www.nowcoder.com/discuss/920776068619829248)

**新手答**：“可能 GPU 不够，增加实例或者调大 batch。”

**高手答**：

先确认指标口径：低的是 SM Active、Tensor Core 利用、显存带宽还是平均 GPU Utilization。然后按等待链路拆分：

```text
入口排队 → Tokenize → Prefill → Decode → 通信 → Detokenize/Streaming
```

常见根因包括 batch 太小、CPU Tokenizer 饱和、Host-to-Device 拷贝、同步点过多、长短请求互相阻塞、KV Cache 碎片、模型并行通信或下游流式消费慢。训练场景还要看 DataLoader、存储吞吐、NCCL straggler 和数据倾斜。

排查时关联请求 Trace、Serving Scheduler 指标、GPU Profile、节点和网络遥测，找到延迟增加的第一个等待阶段。AIOps 可以做异常检测、相似故障检索和根因候选排序，但自动扩容或重启必须经过 SLO、容量和冷却时间约束，不能把相关性直接当因果。

**差距在哪**：新手看到低利用率就加卡，高手先分解等待时间和硬件指标，再判断瓶颈在 CPU、GPU、通信还是调度。

---

## Q：AI Infra 和 Agent Infra 有什么区别？

> 来源：AI 平台 / Agent 平台边界高频题

**新手答**：“AI Infra 管模型和 GPU，Agent Infra 管 Agent 和工具。”

**高手答**：

两者按照主要状态和 SLO 区分：

| 维度 | AI Infra | Agent Infra |
|------|----------|-------------|
| 核心对象 | Dataset、Job、Model、Endpoint、GPU | Run、Step、Context、Tool Call、Sandbox |
| 主要目标 | 训练吞吐、推理延迟、资源利用率 | 执行可靠性、恢复、安全和任务成功率 |
| 典型状态 | 训练 Checkpoint、模型版本、KV Cache | Run State、事件日志、Tool 副作用 |
| 失败边界 | GPU/节点/通信/模型服务故障 | 部分成功、重复调用、等待与恢复 |

它们会在模型网关处相交：Agent Runtime 提交带 Deadline、租户、优先级和模型约束的请求；AI Infra 负责路由到合适的模型副本并返回流式结果。两边共同承担配额、成本、Trace 关联和取消传播，但不能互相替代。

**差距在哪**：新手按技术名词分层，高手按状态所有权、SLO 和故障域划分责任。

---

## Q：如果让你设计一个生产级 AI Infra 平台，你会怎么拆？

> 来源：AI 平台系统设计高频题

**新手答**：“用 Kubernetes 调度 GPU，训练完成后部署成 API，再加监控。”

**高手答**：

```text
Management Plane：项目、权限、配额、模型目录、发布与审计
Training Plane：数据准备、分布式训练、Checkpoint、评测
Serving Plane：模型网关、路由、批处理、缓存、流式推理
Resource Plane：GPU Inventory、队列、调度、弹性与故障域
Artifact/Data Plane：Dataset、Feature、Checkpoint、Model Registry
Observability/AIOps：Metrics、Logs、Trace、Profile、告警与自动处置
```

所有训练和发布都应可追溯到代码、数据快照、配置、镜像和模型制品；上线链路包含离线评测、安全检查、压测、灰度和回滚。平台还要把交互式开发、离线训练和在线推理分成不同队列与配额，避免低优先级训练挤占在线容量。

**差距在哪**：新手只讲算力和部署，高手覆盖制品血缘、发布门禁、租户治理与训练/推理隔离。

---

## Q：GPU 调度和普通 CPU 调度有什么不同？

> 来源：Kubernetes GPU Scheduler 高频题

**新手答**：“给 Pod 配置 GPU Request，让 Kubernetes 调度即可。”

**高手答**：

GPU 通常是稀缺、异构且拓扑敏感的资源。除了型号和显存，还要考虑 NVLink/NVSwitch、PCIe、NUMA、RDMA 网络、故障域以及多卡任务的 gang scheduling。一个分布式 Job 少一张卡也可能完全不能启动，逐 Pod 调度容易造成资源碎片和死锁式等待。

平台需要队列、优先级、配额、公平共享、抢占和回填；在线推理与训练使用不同的抢占策略。MIG 或 time-slicing 可以提高小负载利用率，但会引入性能干扰、显存边界和可观测复杂度，不能默认适用于所有模型。

还要维护 GPU 健康状态：对 Xid、ECC、温度、掉卡和链路降速进行检测，隔离问题设备并保留诊断证据，避免任务在坏节点上反复失败。

**差距在哪**：新手只会写资源声明，高手理解拓扑、成组调度、碎片、公平性和设备健康。

---

## Q：模型版本升级如何做到可观测、可灰度、可回滚？

> 来源：模型发布与稳定性高频题

**新手答**：“部署新版本，先放 10% 流量，指标异常就回滚。”

**高手答**：

发布单元必须绑定模型权重、Tokenizer、推理参数、量化方式、镜像和 Prompt/Adapter 兼容信息。上线前完成离线质量、安全、性能和资源回归；线上先 shadow 验证协议与容量，再按租户或任务类型 canary，避免随机流量掩盖分布差异。

同时观察两类指标：系统指标包括 TTFT、TPOT、P99、错误率、OOM 和成本；质量指标包括任务成功率、拒答率、安全率和分层 Eval。质量指标通常反馈更慢，不能只靠五分钟技术监控判定成功。

回滚也要预留旧版本权重、副本容量和路由配置，并考虑会话粘性、KV Cache 不兼容以及 Agent Run 的版本固定。审计记录必须回答“谁在何时把哪套制品以什么配置发布给了哪些流量”。

**差距在哪**：新手只有流量百分比，高手把制品一致性、质量评估、容量和有状态会话纳入发布计划。

---

## AI Infra 系统设计答题主线

```text
先定目标：训练吞吐，还是在线 TTFT/TPOT/P99
再定对象：Dataset、Job、Checkpoint、Model、Endpoint
再定资源：GPU 型号、显存、拓扑、网络、存储和配额
再做平台：调度、Serving、Registry、灰度、回滚
最后治理：血缘、成本、租户、安全、可观测与 AIOps
```

记住一个结论：**AI Infra 的核心不是让 GPU 忙起来，而是在质量和 SLO 约束下，把数据、模型、算力和发布过程变成可复现、可调度、可治理的系统。**

下一篇建议继续看：

- [架构选型：ReAct、Plan-and-Execute 与 ToT 怎么选](../01-architecture-design/index.html)
