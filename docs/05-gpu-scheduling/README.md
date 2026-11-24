# 大规模 GPU 调度

理解设备暴露、作业排队、拓扑、配额和弹性。三章围绕一个普通电脑可运行的教学调度器展开：先识别可分配资源，再比较排队与放置策略，最后注入节点不可放置窗口并分析恢复边界。

模拟器把 GPU（图形处理器）简化为同质整数槽位，不连接 Kubernetes（容器编排系统），也不执行真实模型。它适合验证调度推理，不是生产调度器或性能基准。

## 章节

- [GPU 资源暴露与隔离](01-gpu-resources.md)
- [队列、配额与拓扑](02-queues-and-topology.md)
- [弹性与故障](03-elasticity-and-failures.md)

## 实验入口

在仓库根目录运行：

```bash
python3 examples/gpu_scheduler_simulator.py examples/gpu_jobs.csv \
  --quota team-a=4 \
  --quota team-b=6 \
  --quota team-c=2
```

程序会对同一组假设性作业比较 FIFO（先到先服务）和 Priority（优先级）策略。具体结果、解释与故障实验分别见第二、三章。

返回[课程总目录](../README.md)。
