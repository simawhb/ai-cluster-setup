#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用多Agent协作框架 - 支持任意场景
用法: python universal_crew.py "任务描述" --scene query/code/novel/custom
"""

import json
import time
import requests
import argparse
from dataclasses import dataclass
from typing import List, Optional, Callable, Dict, Set
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class LLMConfig:
    """LLM配置"""
    base_url: str = "http://192.168.31.202:8080"
    model: str = "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf"
    temperature: float = 0.7
    max_tokens: int = 1000


class Agent:
    """通用AI Agent"""
    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        llm: Optional[LLMConfig] = None,
        verbose: bool = True
    ):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.llm = llm or LLMConfig()
        self.verbose = verbose

    def execute(self, task_description: str, context: str = "") -> str:
        """执行任务"""
        system_prompt = f"""你是{self.role}。

## 你的目标
{self.goal}

## 你的背景
{self.backstory}

## 工作要求
- 用中文回答
- 输出结构化、有条理
- 基于事实，不编造信息
- 如果有前置信息，请参考"""

        messages = [
            {"role": "system", "content": system_prompt}
        ]
        if context:
            messages.append({"role": "user", "content": f"## 前置信息\n{context}\n\n## 当前任务\n{task_description}"})
        else:
            messages.append({"role": "user", "content": task_description})

        try:
            resp = requests.post(
                f"{self.llm.base_url}/v1/chat/completions",
                json={
                    "model": self.llm.model,
                    "messages": messages,
                    "max_tokens": self.llm.max_tokens,
                    "temperature": self.llm.temperature
                },
                timeout=1200
            )
            result = resp.json()
            content = result["choices"][0]["message"].get("content", "")

            if self.verbose:
                tokens = result.get("usage", {})
                print(f"  [{self.role}] 完成 ({tokens.get('total_tokens', '?')} tokens)")

            return content

        except Exception as e:
            if self.verbose:
                print(f"  [{self.role}] 错误: {e}")
            return f"[错误] {e}"


class Task:
    """任务"""
    def __init__(self, description: str, agent: Agent, context_from: Optional[List['Task']] = None):
        self.description = description
        self.agent = agent
        self.context_from = context_from or []
        self._id = id(self)


class Crew:
    """团队 - 管理多个Agent和Task"""
    def __init__(self, agents: List[Agent], tasks: List[Task], verbose: bool = True):
        self.agents = agents
        self.tasks = tasks
        self.verbose = verbose
        self.results = {}

    def _execute_task(self, task: Task, inputs: dict = None) -> tuple:
        """执行单个任务"""
        context = ""
        if task.context_from:
            for dep_task in task.context_from:
                if dep_task._id in self.results:
                    context += f"\n\n## {dep_task.agent.role} 的输出:\n{self.results[dep_task._id]}"

        desc = task.description
        if inputs:
            for key, value in inputs.items():
                desc = desc.replace(f"{{{key}}}", str(value))

        result = task.agent.execute(desc, context)
        self.results[task._id] = result
        return task, result

    def kickoff(self, inputs: dict = None, max_workers: int = 2) -> dict:
        """执行工作流（支持并行）"""
        start_time = time.time()

        if self.verbose:
            print("\n" + "="*60)
            print("🐎 通用多Agent协作工作流")
            print("="*60)
            print(f"Agent: {', '.join(a.role for a in self.agents)}")
            print(f"并发数: {max_workers}")
            print("="*60 + "\n")

        completed: Set[int] = set()
        remaining = list(self.tasks)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while remaining:
                ready = []
                not_ready = []
                for task in remaining:
                    deps = {dep._id for dep in task.context_from}
                    if deps.issubset(completed):
                        ready.append(task)
                    else:
                        not_ready.append(task)

                if not ready:
                    break

                if self.verbose:
                    names = [t.agent.role for t in ready]
                    print(f"[并行执行] {', '.join(names)}")

                futures = {
                    executor.submit(self._execute_task, task, inputs): task
                    for task in ready
                }

                for future in as_completed(futures):
                    task, result = future.result()
                    completed.add(task._id)
                    if self.verbose:
                        print(f"  ✅ {task.agent.role} 完成")

                remaining = not_ready

        final_output = ""
        for task in self.tasks:
            final_output += f"\n\n## {task.agent.role}\n{self.results[task._id]}"

        elapsed = time.time() - start_time

        if self.verbose:
            print("\n" + "="*60)
            print(f"✅ 完成! 耗时: {elapsed:.1f}秒")
            print("="*60)

        return {
            "success": True,
            "elapsed": elapsed,
            "results": {task.agent.role: self.results[task._id] for task in self.tasks},
            "final_output": final_output.strip()
        }


# ========== 场景模板 ==========

def create_query_crew(topic: str) -> Crew:
    """查询场景: 研究员 → 分析师 → 总结"""
    researcher = Agent(
        role="研究员 🔍",
        goal="深入调研主题，收集全面信息",
        backstory="你是资深研究员，擅长信息搜集、资料整理、多角度分析。",
        llm=LLMConfig(temperature=0.3, max_tokens=2000)
    )
    analyst = Agent(
        role="分析师 📊",
        goal="分析信息，提炼关键洞察",
        backstory="你是数据分析师，擅长从复杂信息中提取关键观点和趋势。",
        llm=LLMConfig(temperature=0.3, max_tokens=1500)
    )
    writer = Agent(
        role="总结者 📝",
        goal="生成清晰、有条理的总结报告",
        backstory="你是专业写手，擅长将复杂内容转化为易懂的报告。",
        llm=LLMConfig(temperature=0.5, max_tokens=2000)
    )

    t1 = Task(description=f"深入调研「{topic}」，收集全面信息", agent=researcher)
    t2 = Task(description=f"分析调研结果，提炼关键洞察", agent=analyst, context_from=[t1])
    t3 = Task(description=f"生成总结报告", agent=writer, context_from=[t2])

    return Crew(agents=[researcher, analyst, writer], tasks=[t1, t2, t3])


def create_code_crew(topic: str) -> Crew:
    """编程场景: 架构师 → 程序员 → 审查员"""
    architect = Agent(
        role="架构师 🏗️",
        goal="设计代码架构和实现方案",
        backstory="你是资深架构师，擅长系统设计、技术选型、模块划分。",
        llm=LLMConfig(temperature=0.3, max_tokens=2000)
    )
    programmer = Agent(
        role="程序员 💻",
        goal="编写高质量代码",
        backstory="你是全栈程序员，精通Python/JS/Bash，擅长实现各种功能。",
        llm=LLMConfig(temperature=0.5, max_tokens=3000)
    )
    reviewer = Agent(
        role="审查员 🔎",
        goal="审查代码质量和潜在问题",
        backstory="你是代码审查专家，擅长发现bug、安全漏洞、性能问题。",
        llm=LLMConfig(temperature=0.2, max_tokens=1500)
    )

    t1 = Task(description=f"设计「{topic}」的实现方案", agent=architect)
    t2 = Task(description=f"根据方案编写代码", agent=programmer, context_from=[t1])
    t3 = Task(description=f"审查代码，指出问题和改进建议", agent=reviewer, context_from=[t2])

    return Crew(agents=[architect, programmer, reviewer], tasks=[t1, t2, t3])


def create_novel_crew(topic: str) -> Crew:
    """创作场景: 大纲师 → 作家 → 编辑"""
    outliner = Agent(
        role="大纲师 📋",
        goal="设计故事大纲和人物设定",
        backstory="你是创意策划师，擅长构思故事框架、人物关系、情节走向。",
        llm=LLMConfig(temperature=0.8, max_tokens=2000)
    )
    writer = Agent(
        role="作家 ✍️",
        goal="创作生动的故事内容",
        backstory="你是小说家，擅长描写场景、对话、心理活动，文笔优美。",
        llm=LLMConfig(temperature=0.9, max_tokens=4000)
    )
    editor = Agent(
        role="编辑 📖",
        goal="优化文字表达和故事节奏",
        backstory="你是资深编辑，擅长润色文字、调整节奏、提升可读性。",
        llm=LLMConfig(temperature=0.4, max_tokens=2000)
    )

    t1 = Task(description=f"设计「{topic}」的故事大纲和人物", agent=outliner)
    t2 = Task(description=f"根据大纲创作故事内容", agent=writer, context_from=[t1])
    t3 = Task(description=f"编辑润色，优化表达", agent=editor, context_from=[t2])

    return Crew(agents=[outliner, writer, editor], tasks=[t1, t2, t3])


def create_custom_crew(roles: List[Dict], topic: str) -> Crew:
    """自定义场景: 用户定义Agent角色"""
    agents = []
    tasks = []

    for i, role_config in enumerate(roles):
        agent = Agent(
            role=role_config["role"],
            goal=role_config["goal"],
            backstory=role_config.get("backstory", "你是专业助手。"),
            llm=LLMConfig(
                temperature=role_config.get("temperature", 0.7),
                max_tokens=role_config.get("max_tokens", 1500)
            )
        )
        agents.append(agent)

        # 第一个任务无依赖，后续任务依赖前一个
        if i == 0:
            task = Task(description=role_config["task"].format(topic=topic), agent=agent)
        else:
            task = Task(description=role_config["task"].format(topic=topic), agent=agent, context_from=[tasks[-1]])
        tasks.append(task)

    return Crew(agents=agents, tasks=tasks)


# ========== 场景注册表 ==========

SCENES = {
    "query": {
        "name": "查询调研",
        "desc": "研究员 → 分析师 → 总结",
        "factory": create_query_crew,
        "example": "量子计算的最新进展"
    },
    "code": {
        "name": "编程开发",
        "desc": "架构师 → 程序员 → 审查员",
        "factory": create_code_crew,
        "example": "Python爬虫抓取网页数据"
    },
    "novel": {
        "name": "小说创作",
        "desc": "大纲师 → 作家 → 编辑",
        "factory": create_novel_crew,
        "example": "一个程序员穿越到古代的故事"
    },
    "law": {
        "name": "法律合规",
        "desc": "Scout → Nova → Lex",
        "factory": lambda topic: __import__('crew').create_content_review_crew(topic),
        "example": "广告法禁止使用绝对化用语"
    },
    "full": {
        "name": "完整工作流",
        "desc": "Scout ‖ Digit → Nova → Lex → Memo",
        "factory": lambda topic: __import__('crew').create_full_workflow_crew(topic),
        "example": "热玛吉医美广告合规"
    }
}


# ========== CLI 入口 ==========

def main():
    parser = argparse.ArgumentParser(description="通用多Agent协作框架")
    parser.add_argument("topic", help="任务主题")
    parser.add_argument("--scene", "-s", default="query", choices=list(SCENES.keys()),
                        help="场景类型 (default: query)")
    parser.add_argument("--workers", "-w", type=int, default=2, help="并发数 (default: 2)")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有场景")

    args = parser.parse_args()

    if args.list:
        print("\n可用场景:")
        print("-" * 50)
        for key, scene in SCENES.items():
            print(f"  {key:10} | {scene['name']} | {scene['desc']}")
            print(f"             | 示例: {scene['example']}")
        print()
        return

    scene = SCENES[args.scene]
    print(f"\n场景: {scene['name']}")
    print(f"主题: {args.topic}")
    print(f"并发数: {args.workers}\n")

    crew = scene["factory"](args.topic)
    result = crew.kickoff(max_workers=args.workers)

    # 保存结果
    output_file = args.output or f"outputs/{args.scene}_{int(time.time())}.txt"
    Path(output_file).parent.mkdir(exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"场景: {scene['name']}\n")
        f.write(f"主题: {args.topic}\n")
        f.write(f"耗时: {result['elapsed']:.1f}秒\n")
        f.write("="*60 + "\n")
        f.write(result["final_output"])

    print(f"\n结果已保存: {output_file}")


if __name__ == "__main__":
    main()
