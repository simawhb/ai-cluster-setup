#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI集群任务调度器 - 驷马说法工作流专用"""

import json
import time
import requests
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# 节点配置
NODES = {
    "master": {"ip": "192.168.31.202", "port": 8080, "ram": 32, "model": "gemma-4-12b-it-Q4_K_M.gguf"},
    "worker1": {"ip": "192.168.31.110", "port": 50051, "ram": 16},
    "worker2": {"ip": "192.168.31.50", "port": 50051, "ram": 4},
    "worker3": {"ip": "192.168.31.139", "port": 50051, "ram": 8},
    "worker4": {"ip": "192.168.31.216", "port": 50051, "ram": 12},
}

# Agent 任务配置
AGENTS = {
    "scout": {
        "name": "Scout 司徒特",
        "desc": "市场监管情报收集",
        "model": "gemma-4-12b-it-Q4_K_M.gguf",
        "temperature": 0.3,
        "max_tokens": 2000,
        "system_prompt": "你是Scout，负责搜集市场监管、广告合规相关的情报。请提供准确、及时的信息。"
    },
    "digit": {
        "name": "Digit 迪哥",
        "desc": "数据分析与风险评估",
        "model": "gemma-4-12b-it-Q4_K_M.gguf",
        "temperature": 0.3,
        "max_tokens": 1500,
        "system_prompt": "你是Digit，负责数据分析和风险评估。请用数据说话，提供客观的分析结果。"
    },
    "nova": {
        "name": "Nova 娜娜",
        "desc": "抖音内容创作",
        "model": "gemma-4-12b-it-Q4_K_M.gguf",
        "temperature": 0.7,
        "max_tokens": 3000,
        "system_prompt": "你是Nova，负责创作抖音内容。请创作吸引人、合规的短视频文案。"
    },
    "lex": {
        "name": "Lex 雷虎",
        "desc": "广告法合规审核",
        "model": "gemma-4-12b-it-Q4_K_M.gguf",
        "temperature": 0.1,
        "max_tokens": 2000,
        "system_prompt": "你是Lex，广告法合规专家。请严格审核内容是否符合广告法规定，指出违规风险。"
    },
    "memo": {
        "name": "Memo 小蔓",
        "desc": "行政管理汇总",
        "model": "gemma-4-12b-it-Q4_K_M.gguf",
        "temperature": 0.2,
        "max_tokens": 1500,
        "system_prompt": "你是Memo，负责行政管理和汇总。请整理工作成果，生成规范的报告。"
    }
}

# 工作流定义
WORKFLOWS = {
    "content_review": {
        "name": "内容审核流程",
        "desc": "搜集情报 → 内容创作 → 合规审核",
        "steps": ["scout", "nova", "lex"],
        "parallel_groups": [["scout"], ["nova"], ["lex"]]  # 顺序执行
    },
    "risk_analysis": {
        "name": "风险分析流程",
        "desc": "搜集情报 → 数据分析 → 合规审核",
        "steps": ["scout", "digit", "lex"],
        "parallel_groups": [["scout"], ["digit"], ["lex"]]  # 顺序执行
    },
    "full_workflow": {
        "name": "完整工作流",
        "desc": "搜集 ‖ 分析 → 创作 → 审核 → 汇总",
        "steps": ["scout", "digit", "nova", "lex", "memo"],
        "parallel_groups": [["scout", "digit"], ["nova"], ["lex"], ["memo"]]  # Scout和Digit并行
    }
}


class TaskScheduler:
    def __init__(self):
        self.task_log = []

    def call_llm(self, agent_id, user_message, context=""):
        """调用LLM执行任务"""
        agent = AGENTS[agent_id]
        model = agent["model"]

        # 构建消息
        messages = [
            {"role": "system", "content": agent["system_prompt"]}
        ]
        if context:
            messages.append({"role": "user", "content": f"前置信息：\n{context}"})
        messages.append({"role": "user", "content": user_message})

        # 调用 API
        try:
            resp = requests.post(
                f"http://{NODES['master']['ip']}:{NODES['master']['port']}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": agent["max_tokens"],
                    "temperature": agent["temperature"]
                },
                timeout=1200  # 20分钟超时
            )
            result = resp.json()
            content = result["choices"][0]["message"].get("content", "")
            reasoning = result["choices"][0]["message"].get("reasoning_content", "")
            return {
                "success": True,
                "agent": agent["name"],
                "content": content,
                "reasoning": reasoning,
                "tokens": result.get("usage", {})
            }
        except Exception as e:
            return {
                "success": False,
                "agent": agent["name"],
                "error": str(e)
            }

    def run_workflow(self, workflow_id, topic, max_workers=2):
        """执行工作流（支持并行）"""
        workflow = WORKFLOWS[workflow_id]
        results = []
        context_map = {}  # 每个 agent 的输出
        parallel_groups = workflow.get("parallel_groups", [workflow["steps"]])

        print(f"\n{'='*50}")
        print(f"工作流: {workflow['name']}")
        print(f"主题: {topic}")
        print(f"步骤: {' → '.join(AGENTS[s]['name'] for s in workflow['steps'])}")
        print(f"最大并发: {max_workers}")
        print(f"{'='*50}\n")

        for group_idx, group in enumerate(parallel_groups):
            if len(group) > 1:
                print(f"[并行组 {group_idx+1}] {', '.join(AGENTS[s]['name'] for s in group)}")

                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = {}
                    for step in group:
                        # 收集前置上下文
                        ctx = "\n\n".join(
                            f"## {AGENTS[s]['name']} 的分析：\n{context_map[s]}"
                            for s in context_map
                        )
                        futures[executor.submit(self.call_llm, step, topic, ctx)] = step

                    for future in as_completed(futures):
                        step = futures[future]
                        result = future.result()
                        results.append(result)
                        if result["success"]:
                            context_map[step] = result["content"]
                            print(f"  ✅ {AGENTS[step]['name']} 完成 ({result['tokens'].get('total_tokens', '?')} tokens)")
                        else:
                            print(f"  ❌ {AGENTS[step]['name']} 失败: {result['error']}")
            else:
                step = group[0]
                agent = AGENTS[step]
                print(f"[{group_idx+1}/{len(parallel_groups)}] {agent['name']} 执行中...")

                ctx = "\n\n".join(
                    f"## {AGENTS[s]['name']} 的分析：\n{context_map[s]}"
                    for s in context_map
                )
                result = self.call_llm(step, topic, ctx)
                results.append(result)

                if result["success"]:
                    context_map[step] = result["content"]
                    print(f"  ✅ 完成 ({result['tokens'].get('total_tokens', '?')} tokens)")
                else:
                    print(f"  ❌ 失败: {result['error']}")

        final_context = "\n\n".join(
            f"## {AGENTS[s]['name']} 的分析：\n{context_map[s]}"
            for s in context_map
        )

        return {
            "workflow": workflow["name"],
            "topic": topic,
            "steps": len(workflow["steps"]),
            "results": results,
            "final_context": final_context
        }

    def run_single_agent(self, agent_id, message):
        """执行单个Agent任务"""
        print(f"\n{AGENTS[agent_id]['name']} 执行中...")
        result = self.call_llm(agent_id, message)
        if result["success"]:
            print(f"✅ 完成")
        else:
            print(f"❌ 失败: {result['error']}")
        return result


# HTTP API
scheduler = TaskScheduler()


class SchedulerHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_html()
        elif self.path == '/api/agents':
            self.send_json({"agents": {k: {"name": v["name"], "desc": v["desc"]} for k, v in AGENTS.items()}})
        elif self.path == '/api/workflows':
            self.send_json({"workflows": {k: {"name": v["name"], "desc": v["desc"], "steps": v["steps"]} for k, v in WORKFLOWS.items()}})
        elif self.path.startswith('/api/run'):
            self.handle_run()
        else:
            super().do_GET()

    def handle_run(self):
        """处理任务执行请求"""
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        workflow_id = params.get("workflow", ["full_workflow"])[0]
        agent_id = params.get("agent", [None])[0]
        topic = params.get("topic", ["测试"])[0]
        max_workers = int(params.get("max_workers", ["2"])[0])

        if agent_id:
            # 执行单个Agent
            result = scheduler.run_single_agent(agent_id, topic)
            self.send_json(result)
        elif workflow_id:
            # 执行工作流
            result = scheduler.run_workflow(workflow_id, topic, max_workers)
            self.send_json(result)

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
<title>驷马说法 - AI任务调度器</title>
<style>
body { font-family: 'Segoe UI', sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; background: #f5f5f5; }
h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
.card { background: white; border-radius: 8px; padding: 20px; margin: 15px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.agent { display: inline-block; background: #e3f2fd; padding: 8px 15px; border-radius: 20px; margin: 5px; }
.btn { background: #4CAF50; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 16px; margin: 5px; }
.btn:hover { background: #45a049; }
.btn:disabled { background: #ccc; }
#result { white-space: pre-wrap; background: #f9f9f9; padding: 15px; border-radius: 6px; min-height: 100px; }
textarea { width: 100%; height: 80px; padding: 10px; border-radius: 6px; border: 1px solid #ddd; }
select { padding: 10px; border-radius: 6px; border: 1px solid #ddd; width: 100%; }
.loading { color: #666; font-style: italic; }
</style>
</head>
<body>
<h1>🐎 驷马说法 - AI任务调度器</h1>

<div class="card">
    <h3>选择工作流</h3>
    <select id="workflow">
        <option value="full_workflow">完整工作流 (搜集‖分析→创作→审核→汇总)</option>
        <option value="content_review">内容审核 (搜集→创作→审核)</option>
        <option value="risk_analysis">风险分析 (搜集→分析→审核)</option>
    </select>
    <div style="margin-top:10px">
        <label>并发数: <select id="max_workers">
            <option value="1">1（顺序执行）</option>
            <option value="2" selected>2（推荐）</option>
        </select></label>
    </div>
</div>

<div class="card">
    <h3>输入主题</h3>
    <textarea id="topic" placeholder="例如：热玛吉医美广告合规分析">热玛吉医美广告合规分析</textarea>
</div>

<div class="card">
    <h3>快速执行单个Agent</h3>
    <button class="btn" onclick="runAgent('scout')">🔍 Scout 情报</button>
    <button class="btn" onclick="runAgent('digit')">📊 Digit 分析</button>
    <button class="btn" onclick="runAgent('nova')">✨ Nova 创作</button>
    <button class="btn" onclick="runAgent('lex')">⚖️ Lex 审核</button>
    <button class="btn" onclick="runAgent('memo')">📝 Memo 汇总</button>
</div>

<div class="card">
    <button class="btn" onclick="runWorkflow()" id="runBtn">▶️ 执行工作流</button>
</div>

<div class="card">
    <h3>执行结果</h3>
    <div id="result">等待执行...</div>
</div>

<script>
async function runWorkflow() {
    const workflow = document.getElementById('workflow').value;
    const topic = document.getElementById('topic').value;
    const maxWorkers = document.getElementById('max_workers').value;
    const btn = document.getElementById('runBtn');
    const result = document.getElementById('result');

    btn.disabled = true;
    result.innerHTML = '<span class="loading">执行中（并发数: ' + maxWorkers + '），请稍候...</span>';

    try {
        const resp = await fetch(`/api/run?workflow=${workflow}&topic=${encodeURIComponent(topic)}&max_workers=${maxWorkers}`);
        const data = await resp.json();

        let html = `<strong>工作流:</strong> ${data.workflow}\\n`;
        html += `<strong>主题:</strong> ${data.topic}\\n`;
        html += `<strong>步骤:</strong> ${data.steps}\\n\\n`;

        data.results.forEach((r, i) => {
            html += `<strong>${r.agent}</strong>`;
            if (r.success) {
                html += ` ✅ (${r.tokens?.total_tokens || '?'} tokens)\\n`;
                html += r.content + '\\n\\n';
            } else {
                html += ` ❌ ${r.error}\\n\\n`;
            }
        });

        result.innerHTML = html;
    } catch (e) {
        result.innerHTML = '执行失败: ' + e.message;
    }
    btn.disabled = false;
}

async function runAgent(agentId) {
    const topic = document.getElementById('topic').value;
    const result = document.getElementById('result');

    result.innerHTML = '<span class="loading">执行中...</span>';

    try {
        const resp = await fetch(`/api/run?agent=${agentId}&topic=${encodeURIComponent(topic)}`);
        const data = await resp.json();

        if (data.success) {
            result.innerHTML = `<strong>${data.agent}</strong> ✅\\n\\n${data.content}`;
        } else {
            result.innerHTML = `<strong>${data.agent}</strong> ❌\\n${data.error}`;
        }
    } catch (e) {
        result.innerHTML = '执行失败: ' + e.message;
    }
}
</script>
</body>
</html>"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())


def main():
    port = 18081
    server = HTTPServer(("0.0.0.0", port), SchedulerHandler)
    print(f"任务调度器启动: http://localhost:{port}")
    print(f"API: http://localhost:{port}/api/run?workflow=full_workflow&topic=测试")
    server.serve_forever()


if __name__ == "__main__":
    main()
