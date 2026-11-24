# 课程目录

这门中文课程以推理基础设施为深入主线，覆盖八个知识模块。GPU 与高速互联三章、深度学习计算三章和推理基础设施四章已补充内容，并提供普通电脑可运行的自动微分、资源估算、屋顶线、集合通信、指标和分布式路由练习；其余章节仍是学习计划骨架。“待补全”表示详细课文或实验脚本尚未提交，并不代表实验已经验证。

## 01 计算机基础

- [01 操作系统与资源定位](01-computer-systems/01-os-and-resources.md)：从进程、内存、I/O 定位服务瓶颈。
- [02 并发与网络](01-computer-systems/02-concurrency-and-network.md)：理解请求队列、锁与网络延迟。
- [03 性能测量](01-computer-systems/03-performance-measurement.md)：建立可复现的基线。

## 02 分布式与云原生

- [01 容器与部署](02-distributed-cloud-native/01-containers-and-deployment.md)：服务封装与资源限制。
- [02 分布式服务治理](02-distributed-cloud-native/02-distributed-services.md)：发现、负载均衡与故障。
- [03 可观测性](02-distributed-cloud-native/03-observability.md)：指标、日志和链路追踪。

## 03 GPU 与高速互联

- [01 GPU 架构与存储](03-gpu-interconnect/01-gpu-architecture.md)：计算单元与显存层级。
- [02 计算与带宽分析](03-gpu-interconnect/02-compute-and-bandwidth.md)：识别性能上限。
- [03 多卡通信](03-gpu-interconnect/03-multi-gpu-communication.md)：拓扑与集合通信。

## 04 深度学习计算

- [01 张量计算与自动微分](04-deep-learning-compute/01-tensors-and-autograd.md)：模型执行基础。
- [02 Transformer 与注意力](04-deep-learning-compute/02-transformer-and-attention.md)：解释模型计算量。
- [03 精度与 KV 缓存](04-deep-learning-compute/03-precision-and-kv-cache.md)：解释显存占用。

## 05 大规模 GPU 调度

- [01 GPU 资源暴露与隔离](05-gpu-scheduling/01-gpu-resources.md)：设备与工作负载。
- [02 队列、配额与拓扑](05-gpu-scheduling/02-queues-and-topology.md)：安排共享集群资源。
- [03 弹性与故障](05-gpu-scheduling/03-elasticity-and-failures.md)：容量变化与恢复。

## 06 训练基础设施

- [01 并行策略](06-training-infra/01-parallelism.md)：数据、张量、流水线与分片。
- [02 检查点与恢复](06-training-infra/02-checkpointing.md)：减少故障损失。
- [03 训练性能分析](06-training-infra/03-training-performance.md)：计算、通信与输入流水线。

## 07 推理基础设施：深入主线

- [01 请求生命周期](07-inference-infra/01-request-lifecycle.md)：预填充、解码与流式输出。
- [02 批处理与 KV 缓存](07-inference-infra/02-batching-and-cache.md)：并发与显存权衡。
- [03 基准测试与服务目标](07-inference-infra/03-benchmark-and-slo.md)：延迟、吞吐与有效吞吐。
- [04 分布式推理服务](07-inference-infra/04-distributed-serving.md)：路由、扩缩容与故障。

## 08 AI 平台与成本

- [01 多租户平台](08-ai-platform-finops/01-multitenant-platform.md)：接入、权限与配额。
- [02 容量与成本模型](08-ai-platform-finops/02-capacity-and-cost.md)：成本口径与容量规划。
- [03 可靠性与治理](08-ai-platform-finops/03-reliability-and-governance.md)：服务目标、监控与变更。

继续阅读 [六个月路线](https://github.com/TangHuaiZhe/ai-infra-course/blob/main/ROADMAP.md)、[参考资料](references.md)或[仓库首页](https://github.com/TangHuaiZhe/ai-infra-course)。
