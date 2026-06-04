# AI分布式集群部署指南

基于llama.cpp的分布式LLM推理集群，支持多台电脑协同推理。

## 特点

- **Web UI** - 现代化界面，可视化管理集群
- **一键部署** - 双击bat即可运行
- **实时监控** - 查看节点状态、在线情况
- **自动启动** - 开机自动运行所有服务
- **微信通知** - Server酱推送集群状态

## 硬件配置

| 机器 | 主机名 | IP | 内存 | 角色 |
|------|--------|-----|------|------|
| Master | DESKTOP-AL202 | 192.168.31.202 | 32GB | **Master** + GPU推理 |
| Worker 1 | DESKTOP-8I1BFGC | 192.168.31.110 | 16GB | RPC Worker |
| Worker 2 | DESKTOP-4LSVB5L | 192.168.31.50 | 4GB | RPC Worker |
| Worker 3 | sima | 192.168.31.139 | 8GB | RPC Worker |
| Worker 4 | DESKTOP-BRIV2VM | 192.168.31.216 | 16GB | RPC Worker |

## 文件结构

```
ai-cluster-setup/
├── master/
│   ├── cluster_manager.py   # 集群管理器（Web UI，端口18080）
│   └── bin/                 # llama-server.exe, rpc-server.exe
├── worker/
│   ├── cluster_worker.py    # Worker程序
│   └── bin/                 # rpc-server.exe
├── scripts/
│   ├── install-autostart-master.ps1  # Master自动启动配置
│   ├── install-autostart-worker.ps1  # Worker自动启动配置
│   ├── test-cluster.ps1              # 集群测试脚本
│   └── notify.ps1                    # Server酱微信通知
├── models/                  # GGUF模型文件
├── docs/
│   └── system-migration-guide.md  # 系统盘更换指南
├── start-master.bat         # 启动Master
├── start-worker.bat         # 启动Worker
└── start-llama-server.bat   # 启动llama-server
```

## 快速开始

### Step 1: 下载llama.cpp

从 https://github.com/ggerganov/llama.cpp/releases 下载对应版本：
- Master: GPU版本（CUDA）
- Worker: CPU版本

### Step 2: 下载模型

```bash
# 推荐模型（存放在 D:\AI-Models\）
DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf   # 4.4GB，推荐
Qwen2.5-14B-Instruct-Q4_K_M.gguf           # 8.4GB，需更多内存
gemma-4-12b-it-Q4_K_M.gguf                 # 6.8GB，Google最新
```

### Step 3: 启动Master

```bash
双击 start-master.bat
```

浏览器打开 http://192.168.31.202:18080

### Step 4: 启动Worker

在每台Worker机器上：
```bash
双击 start-worker.bat
```

### Step 5: 启动llama-server

```bash
双击 start-llama-server.bat
```

## API使用

```bash
# 健康检查
curl http://192.168.31.202:8080/health

# 对话接口
curl -X POST http://192.168.31.202:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf","messages":[{"role":"user","content":"Hello"}]}'
```

## 自动启动配置

### Master节点
```powershell
# 以管理员身份运行
powershell -ExecutionPolicy Bypass -File scripts\install-autostart-master.ps1
```

### Worker节点
```powershell
# 以管理员身份运行
powershell -ExecutionPolicy Bypass -File scripts\install-autostart-worker.ps1
```

## 微信通知

使用Server酱推送集群状态到微信：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\notify.ps1 -Title "Title" -Desp "Content"
```

## SSH远程管理

```bash
# Worker 1 (ASUS)
ssh ASUS@192.168.31.110

# Worker 3 (sima)
ssh 14712@192.168.31.139

# Worker 4
ssh whb@192.168.31.216
```

## 性能参考

| 模式 | 生成速度 | 说明 |
|------|----------|------|
| 本地推理（GPU） | 4.25 tokens/s | 推荐，速度快 |
| RPC分布式推理 | 0.45 tokens/s | 网络开销大，不推荐 |

**结论**: Master有GPU时，本地推理比RPC分布式快约10倍。

## 常见问题

### Q: 推理速度很慢？
A: 优先使用本地推理模式（不加--rpc参数），GPU加速更快。

### Q: Worker节点离线？
A: 检查rpc-server是否运行，以及防火墙是否放行50051端口。

### Q: 内存不够？
A: 使用更小的模型（7B替代14B），或使用Q2量化版本。

## 系统迁移

如需更换系统盘，请参考 [系统盘更换指南](docs/system-migration-guide.md)。

## 致谢

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - 核心推理引擎
- [Server酱](https://sct.ftqq.com/) - 微信通知服务
