#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用多Agent协作Web UI
支持: 查询、编程、创作、法律等场景
"""

import json
import time
import logging
import requests
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import threading

# 添加父目录到路径，以便导入 config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_llm_base_url, DEFAULT_MODEL, WORKFLOW_UI_PORT, LLM_TIMEOUT

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# 场景模板
SCENES = {
    "query": {
        "name": "查询调研",
        "desc": "深入调研 → 分析洞察 → 总结报告",
        "icon": "🔍",
        "agents": [
            {"role": "研究员", "goal": "深入调研主题，收集全面信息", "temp": 0.3, "tokens": 2000},
            {"role": "分析师", "goal": "分析信息，提炼关键洞察", "temp": 0.3, "tokens": 1500},
            {"role": "总结者", "goal": "生成清晰、有条理的总结报告", "temp": 0.5, "tokens": 2000}
        ]
    },
    "code": {
        "name": "编程开发",
        "desc": "架构设计 → 代码实现 → 代码审查",
        "icon": "💻",
        "agents": [
            {"role": "架构师", "goal": "设计代码架构和实现方案", "temp": 0.3, "tokens": 2000},
            {"role": "程序员", "goal": "编写高质量代码", "temp": 0.5, "tokens": 3000},
            {"role": "审查员", "goal": "审查代码质量和潜在问题", "temp": 0.2, "tokens": 1500}
        ]
    },
    "novel": {
        "name": "小说创作",
        "desc": "故事大纲 → 内容创作 → 编辑润色",
        "icon": "✍️",
        "agents": [
            {"role": "大纲师", "goal": "设计故事大纲和人物设定", "temp": 0.8, "tokens": 2000},
            {"role": "作家", "goal": "创作生动的故事内容", "temp": 0.9, "tokens": 4000},
            {"role": "编辑", "goal": "优化文字表达和故事节奏", "temp": 0.4, "tokens": 2000}
        ]
    },
    "translate": {
        "name": "翻译润色",
        "desc": "直译 → 意译 → 润色",
        "icon": "🌐",
        "agents": [
            {"role": "直译员", "goal": "准确翻译原文，保持原意", "temp": 0.3, "tokens": 2000},
            {"role": "意译员", "goal": "调整表达，符合目标语言习惯", "temp": 0.5, "tokens": 2000},
            {"role": "润色师", "goal": "优化文笔，提升可读性", "temp": 0.4, "tokens": 1500}
        ]
    },
    "marketing": {
        "name": "营销文案",
        "desc": "市场分析 → 文案创作 → 效果优化",
        "icon": "📢",
        "agents": [
            {"role": "市场分析师", "goal": "分析目标受众和市场趋势", "temp": 0.3, "tokens": 1500},
            {"role": "文案师", "goal": "创作吸引人的营销文案", "temp": 0.8, "tokens": 2500},
            {"role": "优化师", "goal": "优化文案效果和转化率", "temp": 0.4, "tokens": 1500}
        ]
    },
    "custom": {
        "name": "自定义",
        "desc": "自定义Agent角色和流程",
        "icon": "⚙️",
        "agents": []  # 用户自定义
    }
}


def call_llm(role: str, goal: str, task: str, context: str = "", temp: float = 0.7, tokens: int = 1500):
    """调用LLM"""
    system_prompt = f"""你是{role}。

## 你的目标
{goal}

## 工作要求
- 用中文回答
- 输出结构化、有条理
- 基于事实，不编造信息"""

    messages = [{"role": "system", "content": system_prompt}]
    if context:
        messages.append({"role": "user", "content": f"## 前置信息\n{context}\n\n## 当前任务\n{task}"})
    else:
        messages.append({"role": "user", "content": task})

    try:
        resp = requests.post(
            f"{get_llm_base_url()}/v1/chat/completions",
            json={"model": DEFAULT_MODEL, "messages": messages, "max_tokens": tokens, "temperature": temp},
            timeout=LLM_TIMEOUT
        )
        result = resp.json()
        return result["choices"][0]["message"].get("content", ""), result.get("usage", {})
    except Exception as e:
        logger.error(f"LLM调用失败 ({role}): {e}")
        return f"[错误] {e}", {}


def run_scene(scene_id: str, topic: str, custom_agents=None, max_workers=2):
    """执行场景"""
    if scene_id == "custom" and custom_agents:
        agents = custom_agents
    else:
        agents = SCENES[scene_id]["agents"]

    results = []
    context_map = {}

    logger.info(f"{'='*50}")
    logger.info(f"场景: {SCENES[scene_id]['name']}")
    logger.info(f"主题: {topic}")
    logger.info(f"{'='*50}")

    for i, agent_config in enumerate(agents):
        role = agent_config["role"]
        goal = agent_config["goal"]
        temp = agent_config.get("temp", 0.7)
        tokens = agent_config.get("tokens", 1500)

        logger.info(f"[{i+1}/{len(agents)}] {role} 执行中...")

        ctx = "\n\n".join(f"## {k} 的输出:\n{v}" for k, v in context_map.items())
        content, usage = call_llm(role, goal, topic, ctx, temp, tokens)

        results.append({
            "role": role,
            "content": content,
            "tokens": usage.get("total_tokens", 0)
        })
        context_map[role] = content

        logger.info(f"  ✅ 完成 ({usage.get('total_tokens', '?')} tokens)")

    return results


# HTTP API
class UIHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_html()
        elif self.path == '/api/scenes':
            self.send_json({"scenes": {k: {"name": v["name"], "desc": v["desc"], "icon": v["icon"]} for k, v in SCENES.items()}})
        elif self.path.startswith('/api/run'):
            self.handle_run()
        else:
            super().do_GET()

    def handle_run(self):
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        scene_id = params.get("scene", ["query"])[0]
        topic = params.get("topic", ["测试"])[0]
        max_workers = int(params.get("max_workers", ["2"])[0])

        # 自定义Agent
        custom_agents = None
        if scene_id == "custom":
            agents_json = params.get("agents", [None])[0]
            if agents_json:
                custom_agents = json.loads(agents_json)

        results = run_scene(scene_id, topic, custom_agents, max_workers)
        self.send_json({"scene": scene_id, "topic": topic, "results": results})

    def send_json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def send_html(self):
        html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>通用AI工作流</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
.container { max-width: 1000px; margin: 0 auto; }
h1 { color: white; text-align: center; margin-bottom: 30px; font-size: 2em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
.card { background: white; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); }
h3 { color: #333; margin-bottom: 15px; font-size: 1.1em; }
.scene-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.scene-btn { background: #f5f5f5; border: 2px solid transparent; border-radius: 10px; padding: 16px; cursor: pointer; text-align: center; transition: all 0.3s; }
.scene-btn:hover { border-color: #667eea; background: #f0f0ff; }
.scene-btn.active { border-color: #667eea; background: #e8eaff; }
.scene-icon { font-size: 2em; margin-bottom: 8px; }
.scene-name { font-weight: bold; color: #333; }
.scene-desc { font-size: 0.8em; color: #666; margin-top: 4px; }
textarea { width: 100%; height: 100px; padding: 12px; border-radius: 8px; border: 2px solid #eee; font-size: 14px; resize: vertical; }
textarea:focus { border-color: #667eea; outline: none; }
.btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 14px 28px; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold; width: 100%; transition: transform 0.2s; }
.btn:hover { transform: translateY(-2px); }
.btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
#result { white-space: pre-wrap; background: #f9f9f9; padding: 20px; border-radius: 8px; min-height: 150px; max-height: 600px; overflow-y: auto; line-height: 1.6; }
.loading { color: #667eea; font-style: italic; }
.agent-result { margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid #eee; }
.agent-result:last-child { border-bottom: none; }
.agent-role { font-weight: bold; color: #667eea; font-size: 1.1em; margin-bottom: 8px; }
.custom-agents { display: none; }
.custom-agents.show { display: block; }
.agent-form { background: #f9f9f9; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
.agent-form input, .agent-form select { width: 100%; padding: 8px; margin: 4px 0; border-radius: 4px; border: 1px solid #ddd; }
</style>
</head>
<body>
<div class="container">
<h1>🐎 通用AI工作流</h1>

<div class="card">
    <h3>选择场景</h3>
    <div class="scene-grid" id="sceneGrid"></div>
</div>

<div class="card" id="customCard" style="display:none">
    <h3>自定义Agent</h3>
    <div id="customAgents"></div>
    <button onclick="addAgent()" style="margin-top:10px;padding:8px 16px;background:#4CAF50;color:white;border:none;border-radius:4px;cursor:pointer">+ 添加Agent</button>
</div>

<div class="card">
    <h3>输入主题</h3>
    <textarea id="topic" placeholder="输入任务主题..."></textarea>
</div>

<div class="card">
    <button class="btn" onclick="runWorkflow()" id="runBtn">🚀 开始执行</button>
</div>

<div class="card">
    <h3>执行结果</h3>
    <div id="result">等待执行...</div>
</div>
</div>

<script>
let currentScene = 'query';
let customAgentCount = 0;

const SCENES = {
    "query": {"name":"查询调研","desc":"深入调研 → 分析洞察 → 总结报告","icon":"🔍","example":"量子计算的最新进展"},
    "code": {"name":"编程开发","desc":"架构设计 → 代码实现 → 代码审查","icon":"💻","example":"Python爬虫抓取网页数据"},
    "novel": {"name":"小说创作","desc":"故事大纲 → 内容创作 → 编辑润色","icon":"✍️","example":"一个程序员穿越到古代的故事"},
    "translate": {"name":"翻译润色","desc":"直译 → 意译 → 润色","icon":"🌐","example":"将这篇英文论文翻译成中文"},
    "marketing": {"name":"营销文案","desc":"市场分析 → 文案创作 → 效果优化","icon":"📢","example":"新款智能手表的营销文案"},
    "custom": {"name":"自定义","desc":"自定义Agent角色和流程","icon":"⚙️","example":""}
};

function init() {
    const grid = document.getElementById('sceneGrid');
    for (const [id, scene] of Object.entries(SCENES)) {
        const btn = document.createElement('div');
        btn.className = 'scene-btn' + (id === 'query' ? ' active' : '');
        btn.onclick = () => selectScene(id);
        btn.innerHTML = `
            <div class="scene-icon">${scene.icon}</div>
            <div class="scene-name">${scene.name}</div>
            <div class="scene-desc">${scene.desc}</div>
        `;
        grid.appendChild(btn);
    }
    document.getElementById('topic').placeholder = '示例: ' + SCENES.query.example;
}

function selectScene(id) {
    currentScene = id;
    document.querySelectorAll('.scene-btn').forEach(b => b.classList.remove('active'));
    event.currentTarget.classList.add('active');
    document.getElementById('topic').placeholder = '示例: ' + SCENES[id].example;
    document.getElementById('customCard').style.display = id === 'custom' ? 'block' : 'none';
}

function addAgent() {
    customAgentCount++;
    const div = document.createElement('div');
    div.className = 'agent-form';
    div.id = 'agent-' + customAgentCount;
    div.innerHTML = `
        <input placeholder="角色名称" class="agent-role">
        <input placeholder="目标" class="agent-goal">
        <select class="agent-temp">
            <option value="0.3">精确 (0.3)</option>
            <option value="0.5">平衡 (0.5)</option>
            <option value="0.7" selected>创意 (0.7)</option>
            <option value="0.9">发散 (0.9)</option>
        </select>
        <button onclick="this.parentElement.remove()" style="background:#f44336;color:white;border:none;padding:4px 8px;border-radius:4px;cursor:pointer">删除</button>
    `;
    document.getElementById('customAgents').appendChild(div);
}

async function runWorkflow() {
    const topic = document.getElementById('topic').value;
    if (!topic) { alert('请输入主题'); return; }

    const btn = document.getElementById('runBtn');
    const result = document.getElementById('result');
    btn.disabled = true;
    result.innerHTML = '<span class="loading">执行中，请稍候...</span>';

    let url = `/api/run?scene=${currentScene}&topic=${encodeURIComponent(topic)}`;

    // 自定义Agent
    if (currentScene === 'custom') {
        const agents = [];
        document.querySelectorAll('.agent-form').forEach(form => {
            agents.push({
                role: form.querySelector('.agent-role').value,
                goal: form.querySelector('.agent-goal').value,
                temp: parseFloat(form.querySelector('.agent-temp').value)
            });
        });
        url += `&agents=${encodeURIComponent(JSON.stringify(agents))}`;
    }

    try {
        const resp = await fetch(url);
        const data = await resp.json();

        let html = `<strong>场景:</strong> ${SCENES[data.scene].name}\n`;
        html += `<strong>主题:</strong> ${data.topic}\n\n`;

        data.results.forEach(r => {
            html += `<div class="agent-result">`;
            html += `<div class="agent-role">${r.role}</div>`;
            html += `<div>${r.content}</div>`;
            html += `<div style="color:#999;font-size:0.8em;margin-top:8px">${r.tokens} tokens</div>`;
            html += `</div>`;
        });

        result.innerHTML = html;
    } catch (e) {
        result.innerHTML = '执行失败: ' + e.message;
    }
    btn.disabled = false;
}

init();
</script>
</body>
</html>"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())


def main():
    port = WORKFLOW_UI_PORT
    server = HTTPServer(("0.0.0.0", port), UIHandler)
    logger.info(f"通用AI工作流启动: http://localhost:{port}")
    logger.info(f"支持场景: 查询、编程、创作、翻译、营销、自定义")
    server.serve_forever()


if __name__ == "__main__":
    main()
