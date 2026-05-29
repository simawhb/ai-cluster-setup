# AI 分布式集群部署指南

## 文件结构

```
ai-cluster-setup/
├── scripts/
│   ├── setup-network.bat      ← 所有机器都要运行（设置固定IP+防火墙）
│   └── test-cluster.bat       ← 部署完成后测试用
├── master/
│   └── setup-master.bat       ← 在GTX1060那台机器运行
├── worker/
│   └── setup-worker.bat       ← 在每台Worker机器运行
└── README.md                  ← 你在看的这个
```

## IP地址规划

| 机器 | CPU | IP地址 | 角色 |
|------|-----|--------|------|
| DESKTOP-TFINHN6 | i7-3770K + GTX1060 | 192.168.31.101 | **Master** |
| DESKTOP-4LSVB5L | i7-2700K | 192.168.31.102 | Worker |
| sima / XiaoXin 16 | i5-13420H | 192.168.31.103 | Worker |
| DESKTOP-BRIV2VM | i5-3210M | 192.168.31.104 | Worker |
| DESKTOP-8I1BFGC | i5-5200U | 192.168.31.105 | Worker（可选） |
| DESKTOP-GPQGUTK | i3-3220 | 192.168.31.106 | Worker（可选） |

## 部署步骤

### Step 1: 网络配置（所有机器）

在**每台机器**上运行 `scripts/setup-network.bat`：
- 输入对应的IP地址（见上表）
- 自动设置固定IP和防火墙规则
- 需要管理员权限

### Step 2: Master节点部署（GTX1060那台）

1. 把 `master/` 文件夹拷贝到 GTX1060 机器
2. 运行 `setup-master.bat`
3. 自动下载 llama.cpp + Qwen2.5-7B 模型（约4.5GB）
4. 完成后运行 `start-master.bat` 启动

### Step 3: Worker节点部署（其他机器）

1. 把 `worker/` 文件夹拷贝到每台 Worker 机器
2. 运行 `setup-worker.bat`
3. 输入 Master 的 IP（192.168.31.101）
4. 自动下载 llama.cpp CPU版本
5. **先启动 Master，再启动 Worker**

### Step 4: 测试

在任意机器上运行 `scripts/test-cluster.bat`，检查：
- 所有节点是否在线
- Master API 是否可用
- 是否能正常对话

## 使用方法

### 启动顺序（重要！）

```
1. 先启动 Master:   在 GTX1060 机器运行 start-master.bat
2. 再启动 Workers:  在每台 Worker 运行 start-worker.bat
3. 最后使用:        在任何机器浏览器访问 http://192.168.31.101:8080
```

### 调用 API

```bash
# 对话接口
curl http://192.168.31.101:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5-7b","messages":[{"role":"user","content":"你好"}]}'

# 文本补全接口
curl http://192.168.31.101:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5-7b","prompt":"Once upon a time"}'
```

### 浏览器访问

打开 `http://192.168.31.101:8080`，llama.cpp 自带 Web UI。

## 常见问题

### Q: Worker连接不上Master？
- 确认 Master 先启动
- 检查防火墙是否放行 50051 端口
- 互相 ping 测试

### Q: 推理速度很慢？
- 正常现象，老旧硬件+分布式有通信开销
- 先单独用 GTX1060 测试（start-master-solo.bat）
- 如果 solo 模式也慢，考虑换更小的模型（Qwen2.5-3B）

### Q: 内存不够？
- Worker 8GB 的可能比较紧张
- 可以减少 `--ctx-size` 参数（如改为 2048）
- 或者不参与该 Worker

### Q: 换其他模型？
把模型文件放到 `master/models/` 目录
修改 `start-master.bat` 中的 `-m` 参数路径即可

## 进阶：添加更多模型

```bash
# 代码辅助
# 下载 DeepSeek-Coder-6.7B 到 models/ 目录
curl -L -o models/deepseek-coder-6.7b.gguf "https://huggingface.co/..."

# 轻量任务
# 下载 Qwen2.5-3B
curl -L -o models/qwen2.5-3b.gguf "https://huggingface.co/..."
```

修改 start-master.bat 中的模型路径即可切换。
