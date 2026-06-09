#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量级多Agent协作框架 - 驷马说法专用
参考 CrewAI 设计，适配本地 llama-server 集群
"""

import json
import time
import logging
import requests
from dataclasses import dataclass
from typing import List, Optional, Callable, Dict, Set
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_llm_base_url, DEFAULT_MODEL, LLM_TIMEOUT, OUTPUTS_DIR

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM配置"""
    base_url: str = None
    model: str = None
    temperature: float = 0.7
    max_tokens: int = 500

    def __post_init__(self):
        if self.base_url is None:
            self.base_url = get_llm_base_url()
        if self.model is None:
            self.model = DEFAULT_MODEL


class Agent:
    """AI Agent"""
    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        llm: Optional[LLMConfig] = None,
        tools: Optional[List[Callable]] = None,
        verbose: bool = True
    ):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.llm = llm or LLMConfig()
        self.tools = tools or []
        self.verbose = verbose

    def execute(self, task_description: str, context: str = "") -> str:
        """执行任务"""
        # 构建系统提示
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

        # 构建消息
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        if context:
            messages.append({"role": "user", "content": f"## 前置信息\n{context}\n\n## 当前任务\n{task_description}"})
        else:
            messages.append({"role": "user", "content": task_description})

        # 调用 LLM
        try:
            resp = requests.post(
                f"{self.llm.base_url}/v1/chat/completions",
                json={
                    "model": self.llm.model,
                    "messages": messages,
                    "max_tokens": self.llm.max_tokens,
                    "temperature": self.llm.temperature
                },
                timeout=LLM_TIMEOUT
            )
            result = resp.json()
            content = result["choices"][0]["message"].get("content", "")

            if self.verbose:
                tokens = result.get("usage", {})
                logger.info(f"  [{self.role}] 完成 ({tokens.get('total_tokens', '?')} tokens)")

            return content

        except Exception as e:
            if self.verbose:
                logger.error(f"  [{self.role}] 错误: {e}")
            return f"[错误] {e}"


class Task:
    """任务"""
    def __init__(self, description: str, agent: Agent, expected_output: str = "", context_from: Optional[List['Task']] = None):
        self.description = description
        self.agent = agent
        self.expected_output = expected_output
        self.context_from = context_from or []
        self._id = id(self)  # 用于字典键


class Crew:
    """团队 - 管理多个Agent和Task"""
    def __init__(
        self,
        agents: List[Agent],
        tasks: List[Task],
        verbose: bool = True
    ):
        self.agents = agents
        self.tasks = tasks
        self.verbose = verbose
        self.results = {}

    def _execute_task(self, task: Task, inputs: dict = None) -> tuple:
        """执行单个任务（供并行调用）"""
        # 收集前置任务的输出作为上下文
        context = ""
        if task.context_from:
            for dep_task in task.context_from:
                if dep_task._id in self.results:
                    context += f"\n\n## {dep_task.agent.role} 的输出:\n{self.results[dep_task._id]}"

        # 替换输入变量
        desc = task.description
        if inputs:
            for key, value in inputs.items():
                desc = desc.replace(f"{{{key}}}", str(value))

        # 执行任务
        result = task.agent.execute(desc, context)
        self.results[task._id] = result
        return task, result

    def kickoff(self, inputs: dict = None, max_workers: int = 2) -> dict:
        """执行工作流（支持并行）"""
        start_time = time.time()

        if self.verbose:
            logger.info("="*60)
            logger.info("🐎 驷马说法 - 多Agent协作工作流（并行模式）")
            logger.info("="*60)
            logger.info(f"Agent数量: {len(self.agents)}")
            logger.info(f"任务数量: {len(self.tasks)}")
            logger.info(f"最大并发: {max_workers}")
            logger.info(f"执行顺序: {' → '.join(t.agent.role for t in self.tasks)}")
            logger.info("="*60)

        # 构建依赖图
        task_map = {t._id: t for t in self.tasks}
        completed: Set[int] = set()
        remaining = list(self.tasks)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while remaining:
                # 找出所有依赖已满足的任务
                ready = []
                not_ready = []
                for task in remaining:
                    deps = {dep._id for dep in task.context_from}
                    if deps.issubset(completed):
                        ready.append(task)
                    else:
                        not_ready.append(task)

                if not ready:
                    # 没有可执行的任务（可能有循环依赖）
                    if self.verbose:
                        logger.warning("无可用任务，可能存在循环依赖")
                    break

                if self.verbose:
                    names = [t.agent.role for t in ready]
                    logger.info(f"[并行执行] {', '.join(names)}")

                # 并行提交所有就绪任务
                futures = {
                    executor.submit(self._execute_task, task, inputs): task
                    for task in ready
                }

                # 等待所有就绪任务完成
                for future in as_completed(futures):
                    task, result = future.result()
                    completed.add(task._id)
                    if self.verbose:
                        logger.info(f"  ✅ {task.agent.role} 完成")

                remaining = not_ready

        # 汇总结果
        final_output = ""
        for task in self.tasks:
            final_output += f"\n\n## {task.agent.role}\n{self.results[task._id]}"

        elapsed = time.time() - start_time

        if self.verbose:
            logger.info("="*60)
            logger.info(f"✅ 工作流完成! 耗时: {elapsed:.1f}秒")
            logger.info("="*60)

        return {
            "success": True,
            "elapsed": elapsed,
            "results": {task.agent.role: self.results[task._id] for task in self.tasks},
            "final_output": final_output.strip()
        }


# ========== 预定义的驷马说法 Agent ==========

def create_scout_agent() -> Agent:
    """创建 Scout 司徒特 - 市场监管情报收集"""
    return Agent(
        role="Scout 司徒特 🔍",
        goal="搜集市场监管、广告合规相关的最新情报和案例",
        backstory="""你是资深的市场监管研究员，擅长：
- 追踪市场监管总局的最新政策和处罚公告
- 分析广告违规案例
- 整理行业合规动态
- 提供及时准确的情报支持""",
        llm=LLMConfig(temperature=0.3, max_tokens=2000)
    )


def create_digit_agent() -> Agent:
    """创建 Digit 迪哥 - 数据分析"""
    return Agent(
        role="Digit 迪哥 📊",
        goal="分析数据，评估风险，提供数据驱动的洞察",
        backstory="""你是数据分析专家，擅长：
- 数据整理和可视化
- 风险评估和预警
- 趋势分析和预测
- 用数据说话，提供客观分析""",
        llm=LLMConfig(temperature=0.3, max_tokens=1500)
    )


def create_nova_agent() -> Agent:
    """创建 Nova 娜娜 - 内容创作"""
    return Agent(
        role="Nova 娜娜 ✨",
        goal="创作优质的抖音短视频内容",
        backstory="""你是抖音爆款内容创作专家，擅长：
- 撰写吸引人的短视频文案
- 把握热点和用户心理
- 创作有传播力的内容
- 符合平台规范和法律法规""",
        llm=LLMConfig(temperature=0.7, max_tokens=3000)
    )


def create_lex_agent() -> Agent:
    """创建 Lex 雷虎 - 合规审核"""
    return Agent(
        role="Lex 雷虎 ⚖️",
        goal="审核内容是否符合广告法和相关法规",
        backstory="""你是广告法合规审核专家，精通：
- 《广告法》各条款
- 《互联网广告管理办法》
- 市场监管处罚标准
- 常见违规案例和判例
严格把关，确保内容合规。""",
        llm=LLMConfig(temperature=0.1, max_tokens=2000)
    )


def create_memo_agent() -> Agent:
    """创建 Memo 小蔓 - 行政汇总"""
    return Agent(
        role="Memo 小蔓 📝",
        goal="整理工作成果，生成规范的报告",
        backstory="""你是行政管理专家，擅长：
- 整理会议纪要和工作汇报
- 汇总各方意见
- 生成规范的文档
- 跟踪任务进度""",
        llm=LLMConfig(temperature=0.2, max_tokens=1500)
    )


# ========== 预定义的工作流 ==========

def create_content_review_crew(topic: str) -> Crew:
    """内容审核流程: Scout → Nova → Lex"""
    scout = create_scout_agent()
    nova = create_nova_agent()
    lex = create_lex_agent()

    t1 = Task(description=f"搜集关于「{topic}」的市场监管情报和违规案例", agent=scout)
    t2 = Task(description=f"基于情报，创作关于「{topic}」的抖音科普短视频文案", agent=nova, context_from=[t1])
    t3 = Task(description=f"审核文案是否符合广告法规定，指出违规风险", agent=lex, context_from=[t2])

    return Crew(agents=[scout, nova, lex], tasks=[t1, t2, t3])


def create_risk_analysis_crew(topic: str) -> Crew:
    """风险分析流程: Scout → Digit → Lex"""
    scout = create_scout_agent()
    digit = create_digit_agent()
    lex = create_lex_agent()

    t1 = Task(description=f"搜集关于「{topic}」的市场监管情报", agent=scout)
    t2 = Task(description=f"分析「{topic}」的合规风险和数据趋势", agent=digit, context_from=[t1])
    t3 = Task(description=f"基于分析结果，评估法律风险并给出建议", agent=lex, context_from=[t2])

    return Crew(agents=[scout, digit, lex], tasks=[t1, t2, t3])


def create_full_workflow_crew(topic: str) -> Crew:
    """完整工作流: Scout ‖ Digit → Nova → Lex → Memo（并行优化）"""
    scout = create_scout_agent()
    digit = create_digit_agent()
    nova = create_nova_agent()
    lex = create_lex_agent()
    memo = create_memo_agent()

    # Scout 和 Digit 无依赖，可并行执行
    t1 = Task(description=f"搜集关于「{topic}」的市场监管情报和违规案例", agent=scout)
    t2 = Task(description=f"分析「{topic}」的合规风险和数据趋势", agent=digit)  # 不依赖 Scout
    t3 = Task(description=f"基于情报和分析，创作关于「{topic}」的抖音科普短视频文案", agent=nova, context_from=[t1, t2])
    t4 = Task(description=f"审核文案是否合规", agent=lex, context_from=[t3])
    # Memo 只取 Lex 审核结果（最精简），避免上下文过长导致超时
    t5 = Task(description=f"基于审核结果，生成工作汇报摘要", agent=memo, context_from=[t4])

    return Crew(agents=[scout, digit, nova, lex, memo], tasks=[t1, t2, t3, t4, t5])


# ========== CLI 入口 ==========

if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "热玛吉医美广告合规"
    workflow = sys.argv[2] if len(sys.argv) > 2 else "full"
    max_workers = int(sys.argv[3]) if len(sys.argv) > 3 else 2

    logger.info(f"主题: {topic}")
    logger.info(f"工作流: {workflow}")
    logger.info(f"并发数: {max_workers}")

    if workflow == "content":
        crew = create_content_review_crew(topic)
    elif workflow == "risk":
        crew = create_risk_analysis_crew(topic)
    else:
        crew = create_full_workflow_crew(topic)

    result = crew.kickoff(max_workers=max_workers)

    # 保存结果
    OUTPUTS_DIR.mkdir(exist_ok=True)
    output_file = OUTPUTS_DIR / f"crew_{workflow}_{int(time.time())}.txt"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"主题: {topic}\n")
        f.write(f"工作流: {workflow}\n")
        f.write(f"耗时: {result['elapsed']:.1f}秒\n")
        f.write("="*60 + "\n")
        f.write(result["final_output"])

    logger.info(f"结果已保存: {output_file}")
