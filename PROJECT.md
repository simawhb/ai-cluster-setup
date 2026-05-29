# AI分布式集群项目 - 项目跟踪

## 基本信息

| 项目 | 详情 |
|------|------|
| 名称 | AI分布式集群 |
| 目标 | 多台老旧电脑组建本地AI推理集群 |
| 技术栈 | llama.cpp + Python + Web UI |
| GitHub | https://github.com/simawhb/ai-cluster-setup |
| 创建时间 | 2026-05-20 |
| 状态 | 开发完成，待实际部署 |

---

## 功能清单

| 功能 | 状态 | 说明 |
|------|------|------|
| 自动节点发现 | ✅ 完成 | UDP广播，无需手动配置IP |
| Web UI管理界面 | ✅ 完成 | 可视化管理集群 |
| Worker自动注册 | ✅ 完成 | 启动即注册 |
| 实时状态监控 | ✅ 完成 | 查看节点在线状态 |
| 一键启动集群 | ✅ 完成 | Web UI操作 |
| 手动指定Master | ✅ 完成 | 备用方案 |

---

## 硬件配置

| 机器 | CPU | GPU | 内存 | 角色 |
|------|-----|-----|------|------|
| DESKTOP-TFINHN6 | i7-3770K | GTX1060 6GB | 16GB | **Master** |
| DESKTOP-4LSVB5L | i7-2700K | - | 8GB | Worker |
| sima/XiaoXin 16 | i5-13420H | - | 16GB | Worker |
| DESKTOP-BRIV2VM | i5-3210M | - | 8GB | Worker |
| DESKTOP-8I1BFGC | i5-5200U | - | 8GB | Worker（可选） |
| DESKTOP-GPQGUTK | i3-3220 | - | 4GB | Worker（可选） |

---

## 文件结构

```
ai-cluster-setup/
├── master/
│   ├── cluster_manager.py   # Master管理器（Web UI）
│   └── setup-master.bat     # 部署脚本
├── worker/
│   ├── cluster_worker.py    # Worker程序（自动发现）
│   └── setup-worker.bat     # 部署脚本
├── scripts/
│   ├── setup-network.bat    # 网络配置
│   └── test-cluster.bat     # 集群测试
├── bin/                     # llama.cpp二进制（需下载）
├── models/                  # GGUF模型（需下载）
├── start-master.bat         # 启动Master
├── start-worker.bat         # 启动Worker
├── README.md                # 部署指南
└── PROJECT.md               # 本文件
```

---

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                      Master (GTX1060)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Web UI      │  │ API Server  │  │ RPC Server  │     │
│  │ (端口18080) │  │ (端口8080)  │  │ (端口50051) │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
        ↑                    ↑                ↑
        │ UDP广播            │ HTTP            │ RPC
        │ (端口50053)        │                 │
        ↓                    ↓                ↓
┌─────────────────────────────────────────────────────────┐
│                    Worker节点们                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Worker 1    │  │ Worker 2    │  │ Worker 3    │     │
│  │ RPC Server  │  │ RPC Server  │  │ RPC Server  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

---

## 部署步骤

### Step 1: 下载llama.cpp

从 https://github.com/ggerganov/llama.cpp/releases 下载

- **Master**: GPU版本（CUDA）
- **Worker**: CPU版本

放入 `bin/` 目录

### Step 2: 下载模型

从 https://huggingface.co/models?library=gguf 下载

推荐：`Qwen2.5-7B-Instruct-Q4_K_M.gguf`

放入 `models/` 目录

### Step 3: 启动Master

```bash
双击 start-master.bat
```

浏览器打开 http://localhost:18080

### Step 4: 启动Worker

```bash
双击 start-worker.bat
```

### Step 5: 启动集群

在Web UI中选择模型，点击"启动集群"

---

## 部署进度

| 步骤 | 状态 | 说明 |
|------|------|------|
| 下载llama.cpp | ⏳ 待做 | 需要分别下载GPU/CPU版本 |
| 下载模型 | ⏳ 待做 | Qwen2.5-7B约4.5GB |
| 启动Master | ⏳ 待做 | - |
| 启动Worker | ⏳ 待做 | 3台机器 |
| 测试推理 | ⏳ 待做 | - |

---

## API使用

```bash
# 对话接口
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5-7b","messages":[{"role":"user","content":"你好"}]}'

# 浏览器访问
http://localhost:8080
```

---

## 更新日志

### 2026-05-20
- [x] 完成基础部署脚本

### 2026-05-29
- [x] 参考llamacpp-distributed-inference改进
- [x] 添加自动节点发现（UDP广播）
- [x] 添加Web UI管理界面
- [x] 添加Worker自动注册
- [x] 添加实时状态监控
- [x] 更新README文档
- [x] 推送到GitHub

---

## 待办事项

### 紧急
- [ ] 下载llama.cpp二进制文件
- [ ] 下载Qwen2.5-7B模型
- [ ] 在Master机器上测试

### 重要
- [ ] 部署所有Worker节点
- [ ] 测试自动发现功能
- [ ] 测试分布式推理

### 一般
- [ ] 优化推理参数
- [ ] 测试不同模型
- [ ] 性能基准测试

---

## 参考项目

- [llamacpp-distributed-inference](https://github.com/ADT109119/llamacpp-distributed-inference) ⭐82
  - Electron桌面应用
  - mDNS节点发现
  - 完整的模型管理

---

## 备注

- 主要目标：利用老旧硬件搭建本地AI
- 预期效果：GTX1060为主，CPU辅助推理
- 改进来源：参考GitHub上的成熟项目
