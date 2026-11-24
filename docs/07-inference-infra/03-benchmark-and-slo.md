# 基准测试与服务目标

本章面向准备评估推理服务的人。完成练习后，你应能从请求记录计算延迟分位数、输出吞吐和满足服务目标的有效吞吐。

## 学习目标与前置知识

- 明确首词元延迟（TTFT）、每输出词元平均间隔（TPOT）、端到端延迟（E2E）、吞吐与尾延迟的测量点。
- 用服务级目标（Service Level Objective，SLO）定义“有效请求”。
- 先完成[请求生命周期](01-request-lifecycle.md)与[性能测量](../01-computer-systems/03-performance-measurement.md)。

## 先定测量口径

练习从客户端视角记录每个请求的发送、首词元到达和结束时间。指标定义见[上一章](01-request-lifecycle.md)。P95 用**最近秩法**：样本排序后取 `ceil(0.95 × 样本数)` 名次的值。只有五条请求时，P95 就是最大值，不能视为稳定的生产尾延迟。

本练习的**输出词元吞吐**等于全部输出词元数除以“最早请求发送到最晚请求结束”的时间跨度。**有效请求吞吐**等于同时满足 TTFT、TPOT、E2E 阈值的请求数除以同一跨度。单个输出词元的 TPOT 不定义，只检查另外两项。真实服务还要处理失败、取消、超时和输入词元；示例记录没有这些字段。

## 在普通电脑上运行练习

需要 Python 3.9 或更新版本；不需要第三方库或 GPU。在仓库根目录执行：

```bash
python3 examples/inference_metrics.py examples/sample_trace.csv \
  --slo-ttft-ms 500 --slo-tpot-ms 200 --slo-e2e-ms 2000
```

输入是[教学用模拟记录](https://github.com/TangHuaiZhe/ai-infra-course/blob/main/examples/sample_trace.csv)，不是模型实测。关键结果应为：请求数 `5`、TTFT P50 `200 ms`、TTFT P95 `600 ms`、满足目标的请求数 `4`、观测跨度 `1.7 s`、有效请求吞吐约 `2.35 请求/s`。把 TTFT 阈值改为 `100 ms`，观察有效请求数如何变化。

运行自检：

```bash
python3 -m unittest discover -s tests -v
```

脚本拒绝缺列、重复请求编号、倒序时间、非有限时间和少于一个输出词元的记录。它只分析已有时间戳，**不会发起请求、调用模型或测量 GPU**。

## 迁移到真实服务时

记录硬件和驱动、模型与精度、引擎版本、请求到达分布、输入与输出长度、并发控制、缓存冷热、预热时间、采样次数，以及失败和取消请求。不同基准工具对 TTFT、TPOT 等术语可能有不同聚合口径；比较前核对测量点与公式。可参考 [vLLM 官方基准文档](https://docs.vllm.ai/en/latest/benchmarking/cli/)。

## 验收标准

- 能复现示例结果，并解释 P95 在五条样本上为何等于最大值。
- 能说明改变 SLO 阈值为何改变有效吞吐，但不改变原始请求吞吐。
- 能指出这份记录未覆盖的至少四类真实服务因素。

下一章：[分布式推理服务](04-distributed-serving.md)。返回[推理模块目录](README.md)。
