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
├── config.py                    # 统一配置文件（端口、IP、模型等）
├── master/
│   ├── cluster_manager.py       # 集群管理器（Web UI，端口18080）
│   ├── crew.py                  # 多Agent协作框架
│   ├── task_scheduler.py        # 任务调度器（端口18083）
│   ├── universal_ui.py          # 通用工作流UI（端口18082）
│   └── bin/                     # llama-server.exe, rpc-server.exe
├── worker/
│   ├── cluster_worker.py        # Worker程序
│   └── bin/                     # rpc-server.exe
├── scripts/
│   ├── install-autostart-master.ps1  # Master自动启动配置
│   ├── install-autostart-worker.ps1  # Worker自动启动配置
│   ├── test-cluster.ps1              # 集群测试脚本
│   └── notify.ps1                    # Server酱微信通知
├── models/                      # GGUF模型文件（项目内）
├── docs/
│   └── system-migration-guide.md  # 系统盘更换指南
├── start-master.bat             # 启动Master
├── start-worker.bat             # 启动Worker
├── start-llama-server.bat       # 启动llama-server（本地GPU模式）
├── run-workflow.bat             # 启动通用工作流
└── open-firewall.bat            # 开放防火墙端口
```

## 已下载模型

| 模型 | 文件名 | 大小 | 说明 |
|------|--------|------|------|
| **Gemma 4 12B** ⭐ | `gemma-4-12b-it-Q4_K_M.gguf` | 6.7GB | Google最新，推荐使用 |
| DeepSeek R1 7B | `DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf` | 4.4GB | 轻量，速度快 |
| Qwen 2.5 14B | `Qwen2.5-14B-Instruct-Q4_K_M.gguf` | 8.4GB | 需更多内存 |

模型存放位置：`D:\AI-Models\`

## 快速开始

### Step 1: 下载llama.cpp

从 https://github.com/ggerganov/llama.cpp/releases 下载对应版本：
- Master: GPU版本（CUDA）
- Worker: CPU版本

### Step 2: 启动Master

```bash
双击 start-master.bat
```

浏览器打开 http://192.168.31.202:18080

### Step 3: 启动Worker

在每台Worker机器上：
```bash
双击 start-worker.bat
```

### Step 4: 启动llama-server

```bash
双击 start-llama-server.bat
```

## Web UI 端口说明

| 端口 | 服务 | 说明 |
|------|------|------|
| 18080 | 集群管理器 | 节点管理、模型选择、启动集群 |
| 18082 | 通用工作流 | 查询、编程、创作、翻译等场景 |
| 18083 | 任务调度器 | 驷马说法五Agent工作流 |
| 8080 | llama-server API | LLM推理接口 |
| 50051 | RPC Server | Worker节点通信 |
| 50053 | UDP广播 | 节点自动发现 |

## API使用

```bash
# 健康检查
curl http://192.168.31.202:8080/health

# 对话接口
curl -X POST http://192.168.31.202:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma-4-12b-it-Q4_K_M.gguf","messages":[{"role":"user","content":"Hello"}]}'
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
# 先设置环境变量（只需设置一次）
[Environment]::SetEnvironmentVariable('SERVERCHAN_SENDKEY', '你的SendKey', 'User')

# 发送通知
powershell -ExecutionPolicy Bypass -File scripts\notify.ps1 -Title "集群状态" -Desp "所有节点正常"
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
| 本地推理（GPU） | ~4.25 tokens/s | 推荐，速度快 |
| RPC分布式推理 | ~0.45 tokens/s | 网络开销大，不推荐 |

**结论**: Master有GPU时，本地推理比RPC分布式快约10倍。

## 故障排查

### Q: 推理速度很慢？
A: 优先使用本地推理模式（不加--rpc参数），GPU加速更快。

### Q: Worker节点离线？
A: 检查以下几点：
1. rpc-server是否运行：`tasklist | findstr rpc-server`
2. 防火墙是否放行50051端口：运行 `open-firewall.bat`
3. 网络是否连通：`ping 192.168.31.202`

### Q: 内存不够？
A: 使用更小的模型（7B替代14B），或使用Q2量化版本。

### Q: Web UI 打不开？
A: 检查以下几点：
1. Python是否安装：`python --version`
2. 端口是否被占用：`netstat -ano | findstr 18080`
3. 查看控制台错误信息

### Q: 模型加载失败？
A: 检查以下几点：
1. 模型文件是否存在：检查 `D:\AI-Models\` 目录
2. 磁盘空间是否充足
3. 显存是否足够（12B模型需要约8GB显存）

### Q: llama-server 启动报错？
A: 常见原因：
1. 缺少 CUDA：安装 CUDA Toolkit
2. DLL缺失：确保所有dll文件完整
3. 端口冲突：检查8080端口是否被占用

## 配置说明

所有配置集中在 `config.py`，包括：
- 网络端口
- 节点IP地址
- 模型路径
- Agent参数
- 工作流定义

修改配置后，重启相关服务即可生效。

## 系统迁移

如需更换系统盘，请参考 [系统盘更换指南](docs/system-migration-guide.md)。

## 致谢

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - 核心推理引擎
- [Server酱](https://sct.ftqq.com/) - 微信通知服务

---

**版本**: v1.1.0 | **更新日期**: 2026-06-09
