# 开源参考资料

以下链接指向项目仓库或官方文档。它们提供进一步阅读入口，不表示本课程已复现所有功能。使用时请核对项目许可、版本和硬件要求。

| 主题 | 资料 | 建议关注 |
| --- | --- | --- |
| 推理引擎 | [vLLM 项目](https://github.com/vllm-project/vllm) · [官方文档](https://docs.vllm.ai/) | 请求调度、缓存管理、部署与评测 |
| 推理引擎 | [SGLang 项目](https://github.com/sgl-project/sglang) · [官方文档](https://docs.sglang.ai/) | 推理服务与缓存复用 |
| 推理引擎 | [TensorRT-LLM 项目](https://github.com/NVIDIA/TensorRT-LLM) | NVIDIA 平台的推理实现与限制 |
| 张量与训练 | [PyTorch 项目](https://github.com/pytorch/pytorch) · [分布式文档](https://docs.pytorch.org/docs/stable/distributed.html) · [FSDP2 教程](https://docs.pytorch.org/tutorials/intermediate/FSDP_tutorial.html) | 自动微分、分布式训练、参数分片 |
| 训练优化 | [DeepSpeed 项目](https://github.com/deepspeedai/DeepSpeed) | ZeRO 等训练技术的实现 |
| 集群计算与服务 | [Ray 项目](https://github.com/ray-project/ray) · [Ray Serve LLM 文档](https://docs.ray.io/en/latest/serve/llm/index.html) | 分布式执行与模型服务 |
| GPU 编程 | [Triton 项目](https://github.com/triton-lang/triton) · [文档](https://triton-lang.org/main/index.html) | GPU 算子与性能实验 |
| 集群编排 | [Kubernetes 项目](https://github.com/kubernetes/kubernetes) · [GPU 调度文档](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/) | 设备插件与资源请求 |
| 作业排队 | [Kueue 项目](https://github.com/kubernetes-sigs/kueue) · [文档](https://kueue.sigs.k8s.io/) | 配额和排队机制 |
| GPU 通信 | [NCCL 文档](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/) | 集合通信与拓扑 |

**阅读顺序建议：** vLLM → PyTorch 分布式 → Ray Serve → Kubernetes GPU 调度；按实验需要回看 Triton、SGLang 和 NCCL。建议顺序是课程设计选择，不代表工具之间存在唯一的先修关系。
