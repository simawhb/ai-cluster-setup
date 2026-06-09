#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI集群统一配置文件
所有配置集中管理，便于维护和修改
"""

import os
from pathlib import Path

# ==================== 路径配置 ====================
BASE_DIR = Path(__file__).parent
BIN_DIR = BASE_DIR / "bin"
MASTER_BIN_DIR = BASE_DIR / "master" / "bin"
MODELS_DIR = BASE_DIR / "models"
EXTRA_MODELS_DIR = Path("D:/AI-Models")
OUTPUTS_DIR = BASE_DIR / "outputs"
LOGS_DIR = BASE_DIR / "logs"

# ==================== 网络端口配置 ====================
WEB_UI_PORT = 18080          # 集群管理器 Web UI
API_PORT = 8080              # llama-server API
RPC_PORT = 50051             # RPC Server 端口
BROADCAST_PORT = 50053       # UDP 广播端口
WORKFLOW_UI_PORT = 18082     # 通用工作流 Web UI
SCHEDULER_UI_PORT = 18083    # 任务调度器 Web UI

# ==================== Master 节点配置 ====================
MASTER_IP = "192.168.31.202"
MASTER_HOSTNAME = "DESKTOP-AL202"

# ==================== Worker 节点配置 ====================
WORKERS = {
    "worker1": {
        "ip": "192.168.31.110",
        "hostname": "DESKTOP-8I1BFGC",
        "ram": 16,
        "ssh_user": "ASUS"
    },
    "worker2": {
        "ip": "192.168.31.50",
        "hostname": "DESKTOP-4LSVB5L",
        "ram": 4,
        "ssh_user": None
    },
    "worker3": {
        "ip": "192.168.31.139",
        "hostname": "sima",
        "ram": 8,
        "ssh_user": "14712"
    },
    "worker4": {
        "ip": "192.168.31.216",
        "hostname": "DESKTOP-BRIV2VM",
        "ram": 16,
        "ssh_user": "whb"
    }
}

# ==================== 模型配置 ====================
DEFAULT_MODEL = "gemma-4-12b-it-Q4_K_M.gguf"
AVAILABLE_MODELS = {
    "gemma-4-12b": {
        "file": "gemma-4-12b-it-Q4_K_M.gguf",
        "size": "6.7GB",
        "desc": "Google Gemma 4 12B，推荐"
    },
    "deepseek-7b": {
        "file": "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf",
        "size": "4.4GB",
        "desc": "DeepSeek R1 蒸馏版，轻量"
    },
    "qwen-14b": {
        "file": "Qwen2.5-14B-Instruct-Q4_K_M.gguf",
        "size": "8.4GB",
        "desc": "Qwen 2.5 14B，需更多内存"
    }
}

# ==================== LLM 推理参数 ====================
DEFAULT_NGL = 99             # GPU 层数
DEFAULT_PARALLEL = 2         # 并行请求数
DEFAULT_MAX_TOKENS = 2000    # 默认最大输出 token
DEFAULT_TEMPERATURE = 0.7    # 默认温度
LLM_TIMEOUT = 1200           # LLM 调用超时（秒）

# ==================== Agent 配置 ====================
AGENTS = {
    "scout": {
        "name": "Scout 司徒特 🔍",
        "desc": "市场监管情报收集",
        "temperature": 0.3,
        "max_tokens": 2000,
        "system_prompt": "你是Scout，负责搜集市场监管、广告合规相关的情报。请提供准确、及时的信息。"
    },
    "digit": {
        "name": "Digit 迪哥 📊",
        "desc": "数据分析与风险评估",
        "temperature": 0.3,
        "max_tokens": 1500,
        "system_prompt": "你是Digit，负责数据分析和风险评估。请用数据说话，提供客观的分析结果。"
    },
    "nova": {
        "name": "Nova 娜娜 ✨",
        "desc": "抖音内容创作",
        "temperature": 0.7,
        "max_tokens": 3000,
        "system_prompt": "你是Nova，负责创作抖音内容。请创作吸引人、合规的短视频文案。"
    },
    "lex": {
        "name": "Lex 雷虎 ⚖️",
        "desc": "广告法合规审核",
        "temperature": 0.1,
        "max_tokens": 2000,
        "system_prompt": "你是Lex，广告法合规专家。请严格审核内容是否符合广告法规定，指出违规风险。"
    },
    "memo": {
        "name": "Memo 小蔓 📝",
        "desc": "行政管理汇总",
        "temperature": 0.2,
        "max_tokens": 1500,
        "system_prompt": "你是Memo，负责行政管理和汇总。请整理工作成果，生成规范的报告。"
    }
}

# ==================== 工作流配置 ====================
WORKFLOWS = {
    "content_review": {
        "name": "内容审核流程",
        "desc": "搜集情报 → 内容创作 → 合规审核",
        "steps": ["scout", "nova", "lex"],
        "parallel_groups": [["scout"], ["nova"], ["lex"]]
    },
    "risk_analysis": {
        "name": "风险分析流程",
        "desc": "搜集情报 → 数据分析 → 合规审核",
        "steps": ["scout", "digit", "lex"],
        "parallel_groups": [["scout"], ["digit"], ["lex"]]
    },
    "full_workflow": {
        "name": "完整工作流",
        "desc": "搜集 ‖ 分析 → 创作 → 审核 → 汇总",
        "steps": ["scout", "digit", "nova", "lex", "memo"],
        "parallel_groups": [["scout", "digit"], ["nova"], ["lex"], ["memo"]]
    }
}

# ==================== Server酱通知配置 ====================
# 优先从环境变量读取，否则使用默认值
SERVERCHAN_SENDKEY = os.environ.get("SERVERCHAN_SENDKEY", "")

# ==================== 集群管理配置 ====================
NODE_TIMEOUT = 30            # 节点超时时间（秒）
HEARTBEAT_INTERVAL = 10      # 心跳间隔（秒）
BROADCAST_INTERVAL = 5       # 广播间隔（秒）

# ==================== 版本信息 ====================
VERSION = "1.1.0"


def get_model_path(model_name: str) -> Path:
    """获取模型文件的完整路径"""
    # 先在 models 目录查找
    local_path = MODELS_DIR / model_name
    if local_path.exists():
        return local_path

    # 再在额外模型目录查找
    extra_path = EXTRA_MODELS_DIR / model_name
    if extra_path.exists():
        return extra_path

    # 返回默认路径（可能不存在）
    return extra_path


def list_available_models() -> list:
    """列出所有可用的模型文件"""
    models = set()
    for d in [MODELS_DIR, EXTRA_MODELS_DIR]:
        if d.exists():
            models.update(f.name for f in d.glob("*.gguf"))
    return sorted(models)


def get_llm_base_url() -> str:
    """获取 LLM API 基础 URL"""
    return f"http://{MASTER_IP}:{API_PORT}"
