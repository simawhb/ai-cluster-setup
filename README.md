# AI分布式集群部署指南

基于llama.cpp的分布式LLM推理集群，支持多台电脑协同推理。

## 特点

- **自动发现** - Worker自动发现Master，无需手动配置IP
- **Web UI** - 现代化界面，可视化管理集群
- **一键部署** - 双击bat即可运行
- **实时监控** - 查看节点状态、在线情况

## 文件结构

```
ai-cluster-setup/
├── master/
│   ├── cluster_manager.py   # Master管理器（Web UI）
│   └── setup-master.bat     # 部署脚本
├── worker/
│   ├── cluster_worker.py    # Worker程序
│   └── setup-worker.bat     # 部署脚本
├── bin/                     # llama.cpp二进制文件（需下载）
├── models/                  # GGUF模型文件（需下载）
├── start-master.bat         # 启动Master
├── start-worker.bat         # 启动Worker
└── README.md
```

## 硬件配置

| 机器 | CPU | GPU | IP | 角色 |
|------|-----|-----|-----|------|
| Master | i7-3770K | GTX1060 | 自动获取 | **Master** |
| Worker 1 | i7-2700K | - | 自动获取 | Worker |
| Worker 2 | i5-13420H | - | 自动获取 | Worker |
| Worker 3 | i5-3210M | - | 自动获取 | Worker |

## 快速开始

### Step 1: 下载llama.cpp

从 https://github.com/ggerganov/llama.cpp/releases 下载：

- **Master机器**: 下载GPU版本（CUDA）
- **Worker机器**: 下载CPU版本

将以下文件放入 `bin/` 目录：
- `llama-server.exe`
- `rpc-server.exe`

### Step 2: 下载模型

从 https://huggingface.co/models?library=gguf 下载GGUF模型，放入 `models/` 目录。

推荐模型：
- `Qwen2.5-7B-Instruct-Q4_K_M.gguf`（约4.5GB）
- `Qwen2.5-3B-Instruct-Q4_K_M.gguf`（约2GB，内存小的机器用）

### Step 3: 启动Master

在GTX1060那台机器上：
```bash
双击 start-master.bat
```

浏览器会自动打开 http://localhost:18080

### Step 4: 启动Worker

在其他每台机器上：
```bash
双击 start-worker.bat
```

Worker会自动发现Master并注册。

### Step 5: 启动集群

在Web UI中：
1. 选择模型
2. 设置GPU层数（默认99）
3. 点击"启动集群"

## API使用

```bash
# 对话接口
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-7b",
    "messages": [{"role": "user", "content": "你好"}]
  }'

# 浏览器访问
http://localhost:8080
```

## 手动指定Master

如果自动发现失败，可以手动指定Master IP：

```bash
start-worker.bat 192.168.31.101
```

## 常见问题

### Q: Worker找不到Master？

1. 确保Master先启动
2. 检查防火墙是否放行 UDP 50053 端口
3. 尝试手动指定Master IP

### Q: 推理速度很慢？

1. 正常现象，分布式有通信开销
2. 先单独用Master测试（不启动Worker）
3. 考虑换更小的模型（Qwen2.5-3B）

### Q: 内存不够？

1. 减少GPU层数（ngl参数）
2. 使用更小的模型
3. 使用Q2量化版本

## 技术原理

```
┌─────────────────────────────────────────────────────────┐
│                      Master (GTX1060)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Web UI      │  │ API Server  │  │ RPC Server  │     │
│  │ (端口18080) │  │ (端口8080)  │  │ (端口50051) │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
        ↑                    ↑                ↑
        │                    │                │
        │ UDP广播            │ HTTP            │ RPC
        │ (端口50053)        │                 │
        │                    │                │
┌───────┴────────────────────┴────────────────┴───────────┐
│                    Worker节点们                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Worker 1    │  │ Worker 2    │  │ Worker 3    │     │
│  │ RPC Server  │  │ RPC Server  │  │ RPC Server  │     │
│  │ (端口50051) │  │ (端口50051) │  │ (端口50051) │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

1. Master启动后，通过UDP广播自己的存在
2. Worker启动后，监听UDP广播发现Master
3. Worker向Master注册自己的IP和端口
4. Master启动API服务器时，将所有Worker加入推理集群
5. 用户请求通过Master分发到各个Worker协同处理

## 开源协议

MIT License

## 致谢

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - 核心推理引擎
- [llamacpp-distributed-inference](https://github.com/ADT109119/llamacpp-distributed-inference) - 参考实现
