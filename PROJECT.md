# AI分布式集群项目 - 项目跟踪

## 基本信息

| 项目 | 详情 |
|------|------|
| 名称 | AI分布式集群 |
| 目标 | 多台老旧电脑组建本地AI推理集群 |
| 技术栈 | llama.cpp + Qwen2.5-7B |
| 创建时间 | 2026-05-20 |
| 状态 | 部署脚本完成，待实际部署 |

---

## 硬件配置

| 机器 | CPU | GPU | 内存 | IP | 角色 |
|------|-----|-----|------|-----|------|
| DESKTOP-TFINHN6 | i7-3770K | GTX1060 6GB | 16GB | 192.168.31.101 | **Master** |
| DESKTOP-4LSVB5L | i7-2700K | - | 8GB | 192.168.31.102 | Worker |
| sima/XiaoXin 16 | i5-13420H | - | 16GB | 192.168.31.103 | Worker |
| DESKTOP-BRIV2VM | i5-3210M | - | 8GB | 192.168.31.104 | Worker |
| DESKTOP-8I1BFGC | i5-5200U | - | 8GB | 192.168.31.105 | Worker（可选） |
| DESKTOP-GPQGUTK | i3-3220 | - | 4GB | 192.168.31.106 | Worker（可选） |

---

## 文件结构

```
ai-cluster-setup/
├── scripts/
│   ├── setup-network.bat      # 网络配置（所有机器）
│   └── test-cluster.bat       # 集群测试
├── master/
│   ├── setup-master.bat       # Master部署
│   └── start-master.bat       # Master启动
├── worker/
│   ├── setup-worker.bat       # Worker部署
│   └── start-worker.bat       # Worker启动
├── README.md                  # 部署指南
└── PROJECT.md                 # 本文件 - 项目跟踪
```

---

## 部署进度

### 网络配置

| 机器 | IP配置 | 防火墙 | 状态 |
|------|--------|--------|------|
| Master (101) | ⏳ 待配置 | ⏳ 待配置 | - |
| Worker (102) | ⏳ 待配置 | ⏳ 待配置 | - |
| Worker (103) | ⏳ 待配置 | ⏳ 待配置 | - |
| Worker (104) | ⏳ 待配置 | ⏳ 待配置 | - |
| Worker (105) | ⏳ 待配置 | ⏳ 待配置 | - |
| Worker (106) | ⏳ 待配置 | ⏳ 待配置 | - |

### Master节点

| 步骤 | 状态 | 说明 |
|------|------|------|
| 下载llama.cpp | ⏳ 待做 | GPU版本 |
| 下载Qwen2.5-7B | ⏳ 待做 | 约4.5GB |
| 配置启动脚本 | ⏳ 待做 | - |
| 启动测试 | ⏳ 待做 | - |

### Worker节点

| 机器 | 步骤 | 状态 | 说明 |
|------|------|------|------|
| 102 | 下载llama.cpp | ⏳ 待做 | CPU版本 |
| 102 | 连接Master | ⏳ 待做 | - |
| 103 | 下载llama.cpp | ⏳ 待做 | CPU版本 |
| 103 | 连接Master | ⏳ 待做 | - |
| 104 | 下载llama.cpp | ⏳ 待做 | CPU版本 |
| 104 | 连接Master | ⏳ 待做 | - |

---

## 部署步骤

### Step 1: 网络配置（所有机器）

```bash
# 在每台机器上运行
scripts/setup-network.bat
```

### Step 2: Master部署（GTX1060机器）

```bash
# 在Master机器上运行
master/setup-master.bat
```

### Step 3: Worker部署（其他机器）

```bash
# 在每台Worker机器上运行
worker/setup-worker.bat
# 输入Master IP: 192.168.31.101
```

### Step 4: 启动集群

```bash
# 1. 先启动Master
master/start-master.bat

# 2. 再启动Workers
worker/start-worker.bat
```

### Step 5: 测试

```bash
# 在任意机器上运行
scripts/test-cluster.bat
```

---

## API使用

```bash
# 对话接口
curl http://192.168.31.101:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5-7b","messages":[{"role":"user","content":"你好"}]}'

# 浏览器访问
http://192.168.31.101:8080
```

---

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| Worker连接不上 | 确认Master先启动，检查防火墙50051端口 |
| 推理速度慢 | 正常现象，可换更小模型（Qwen2.5-3B） |
| 内存不够 | 减少ctx-size参数（如2048） |

---

## 更新日志

### 2026-05-20
- [x] 完成部署脚本开发
- [x] 完成README文档

### 2026-05-29
- [x] 创建项目跟踪文档
- [ ] 实际部署测试

---

## 待办事项

### 紧急
- [ ] 在Master机器上运行网络配置
- [ ] 部署Master节点
- [ ] 测试Master单独运行

### 重要
- [ ] 部署Worker节点
- [ ] 测试集群通信
- [ ] 测试分布式推理

### 一般
- [ ] 优化推理参数
- [ ] 测试不同模型
- [ ] 性能基准测试

---

## 备注

- 主要目标：利用老旧硬件搭建本地AI
- 预期效果：GTX1060为主，CPU辅助推理
- 后续计划：测试后决定是否扩展
