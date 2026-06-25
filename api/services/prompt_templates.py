"""
Scene-specific prompt templates for RAG answer generation.

Keep answer-shaping contracts here so retrieval, business tool execution, and
prompt wording can evolve independently.
"""

from typing import Any, Dict, List, Tuple, Union


PromptProfileValue = Union[List[str], str]
PromptProfile = Dict[str, PromptProfileValue]
AnswerPerspective = Dict[str, str]
BUSINESS_PROMPT_SCENES = ("risk_rule", "profit")


SCENE_PROMPT_PROFILES: Dict[str, PromptProfile] = {
    "risk_rule": {
        "name": "风控规则",
        "focus": "风险事件、规则命中、处置建议和可解释口径",
        "requirements": [
            "先给出风控结论，说明是否建议拦截、放行、复核或补充验证",
            "列出命中规则/依据，区分工具选择依据、系统接口数据和文档依据",
            "解释关键证据字段，例如风险分、命中规则、交易上下文和用户上下文",
            "给出处置建议，并补充面向运营或用户的可解释口径",
            "补充风控策略视角，说明规则阈值、证据强弱和是否建议复核策略配置",
            "如果系统接口数据包含风控证据摘要，必须引用决策、风险分、风险等级、命中规则数和建议动作",
            "如果证据不足，明确说明缺失字段，不要推断用户意图或风险事实",
            "如果系统接口返回合同诊断码、缺失字段或异常字段，只按安全诊断说明上游响应合同不匹配，不要推断规则命中或风险结论",
            "如果系统接口或样例校验上下文包含未展示字段，只说明这些字段已被展示白名单过滤，不要引用或推断字段值",
        ],
        "answer_structure": [
            "结论：用一句话说明风控决策、风险等级和建议动作",
            "命中依据：优先引用风控证据摘要，再列出工具选择来源/依据、系统接口命中规则、风险分和文档依据，明确来源",
            "处置建议：说明拦截、放行、复核或补充验证动作及原因",
            "口径说明：给出面向策略、运营或技术排查的解释边界",
            "信息来源：列出系统接口、审计ID和文档编号",
        ],
    },
    "profit": {
        "name": "毛利抽成",
        "focus": "订单毛利、钱流链路、平台抽成、司机收入和净毛利",
        "requirements": [
            "先给出订单毛利结论，说明平台净毛利、结算状态和是否存在异常",
            "按钱流链路解释乘客支付、平台抽成、司机收入、补贴、优惠、渠道成本和净毛利",
            "如果系统接口数据包含链路来源，明确说明该链路是接口原生返回还是按最小合同自动派生",
            "明确平台抽成和司机收入的金额或比例，避免只给笼统描述",
            "说明补贴、优惠、渠道成本等对净毛利的影响",
            "如果系统接口数据包含毛利公式核对，明确说明计算净毛利与接口净毛利是否一致；不一致时提示复核上游金额字段或接口合同",
            "补充财务口径，区分收入、成本、补贴优惠和平台净毛利，避免把乘客支付直接当作平台收入",
            "补充运营口径，指出可行动的异常点，例如补贴偏高、优惠侵蚀毛利或司机收入异常",
            "如果链路数据不完整，指出缺失节点，并只基于已有字段回答",
            "如果系统接口数据包含工具选择来源、选择依据或置信度，简要说明为什么查询该毛利接口",
            "如果系统接口返回合同诊断码、缺失字段或异常字段，只按安全诊断说明上游响应合同不匹配，不要推断缺失金额、抽成或司机收入",
            "如果系统接口或样例校验上下文包含未展示字段，只说明这些字段已被展示白名单过滤，不要引用或推断字段值",
        ],
        "answer_structure": [
            "订单结论：用一句话说明平台净毛利、结算状态和是否异常",
            "钱流链路：按乘客支付、平台抽成、司机收入、补贴、优惠、渠道费、净毛利说明，并交代链路来源（接口原生/自动派生）",
            "财务口径：区分收入、成本、补贴优惠、渠道费和平台净毛利，并引用毛利公式核对状态",
            "运营关注点：指出补贴、优惠、司机收入或渠道费的可行动异常",
            "信息来源：列出工具选择来源/依据、系统接口、审计ID和文档编号",
        ],
    },
    "model_card": {
        "name": "模型卡片",
        "focus": "模型用途、版本、特征、指标、部署状态和使用边界",
        "requirements": [
            "先说明模型用途和适用场景",
            "列出版本、负责人、上线状态、核心指标或监控指标",
            "说明输入特征、输出含义和使用限制",
            "如果缺少模型元数据，明确指出缺失项",
        ],
        "answer_structure": [
            "模型概览：说明模型用途、版本、负责人和上线状态",
            "指标与特征：列出核心指标、监控指标、输入特征和输出含义",
            "使用边界：说明适用场景、限制和缺失元数据",
            "信息来源：列出文档编号或系统数据来源",
        ],
    },
    "simulation": {
        "name": "仿真结果",
        "focus": "仿真方案、指标变化、异常解释和后续分析动作",
        "requirements": [
            "先给出仿真结论和关键指标变化",
            "解释影响范围、异常指标和可能原因",
            "区分已验证结果和需要进一步实验的假设",
            "给出下一步分析或上线前检查建议",
        ],
        "answer_structure": [
            "仿真结论：说明核心指标变化和整体判断",
            "指标拆解：解释影响范围、异常指标和可能原因",
            "假设边界：区分已验证结果和待验证假设",
            "下一步：给出继续分析或上线前检查动作",
            "信息来源：列出文档编号或系统数据来源",
        ],
    },
}

DEFAULT_SCENE_PROMPT_PROFILE = {
    "name": "{scene_type}",
    "focus": "用户问题、文档依据和可验证结论",
    "requirements": [
        "先回答用户的核心问题",
        "引用可验证的文档或系统接口依据",
        "如果证据不足，明确说明缺失信息",
    ],
    "answer_structure": [
        "结论：先回答用户的核心问题",
        "依据：列出可验证的文档或系统接口依据",
        "限制：说明缺失信息和不确定性",
        "信息来源：列出文档编号或系统数据来源",
    ],
}

ANSWER_PERSPECTIVES: Dict[str, Dict[str, AnswerPerspective]] = {
    "risk_rule": {
        "strategy": {
            "label": "风控策略口径",
            "instruction": (
                "重点解释规则阈值、命中依据、证据强弱、误杀风险和是否建议复核策略配置。"
            ),
        },
        "operations": {
            "label": "运营解释口径",
            "instruction": (
                "重点给出可对运营或用户说明的原因、处置建议、补充验证动作和沟通边界。"
            ),
        },
        "technical": {
            "label": "技术排查口径",
            "instruction": (
                "重点说明接口状态、审计ID、合同诊断码、字段缺失或异常、可复现线索和下一步排查动作。"
            ),
        },
        "balanced": {
            "label": "综合风控解释口径",
            "instruction": "先给结论，再按命中规则、证据字段和处置建议解释。",
        },
    },
    "profit": {
        "finance": {
            "label": "财务口径",
            "instruction": (
                "重点区分收入、成本、补贴优惠、渠道费和平台净毛利，避免把乘客支付当作平台收入。"
            ),
        },
        "operations": {
            "label": "运营口径",
            "instruction": (
                "重点指出可行动异常，例如补贴偏高、优惠侵蚀毛利、司机收入异常或渠道成本偏高。"
            ),
        },
        "technical": {
            "label": "技术排查口径",
            "instruction": (
                "重点说明接口状态、审计ID、合同诊断码、链路节点缺失、字段类型异常和复查建议。"
            ),
        },
        "balanced": {
            "label": "综合毛利分析口径",
            "instruction": "先给净毛利结论，再解释钱流链路、抽成、司机收入和主要成本项。",
        },
    },
}

PERSPECTIVE_KEYWORDS: Dict[str, List[Tuple[str, Tuple[str, ...]]]] = {
    "risk_rule": [
        ("technical", ("排查", "接口", "报错", "审计", "audit", "字段", "失败")),
        ("strategy", ("策略", "阈值", "规则", "误杀", "复核", "命中", "拦截")),
        ("operations", ("运营", "用户", "解释", "处置", "沟通", "验证")),
    ],
    "profit": [
        ("technical", ("排查", "接口", "报错", "审计", "audit", "字段", "失败", "链路缺失")),
        ("operations", ("运营", "补贴", "优惠", "活动", "司机", "渠道", "异常")),
        ("finance", ("财务", "净毛利", "利润", "成本", "收入", "结算", "口径")),
    ],
}


def get_scene_prompt_profile(scene_type: str) -> PromptProfile:
    """Return a scene prompt profile with a safe default fallback."""
    profile = SCENE_PROMPT_PROFILES.get(scene_type)
    if profile is not None:
        return profile
    return {
        **DEFAULT_SCENE_PROMPT_PROFILE,
        "name": DEFAULT_SCENE_PROMPT_PROFILE["name"].format(scene_type=scene_type),
    }


def infer_answer_perspective(query: str, scene_type: str) -> AnswerPerspective:
    """Infer the primary answer perspective from scene and user wording."""
    return resolve_answer_perspective(
        query=query,
        scene_type=scene_type,
        answer_perspective=None,
    )


def resolve_answer_perspective(
    *,
    query: str,
    scene_type: str,
    answer_perspective: str = None,
) -> AnswerPerspective:
    """Resolve an explicit answer perspective, falling back to keyword inference."""
    perspectives = ANSWER_PERSPECTIVES.get(scene_type, {})
    fallback = perspectives.get("balanced") or {
        "label": "综合问答口径",
        "instruction": "先回答核心问题，再补充依据、限制和下一步建议。",
    }
    if answer_perspective and answer_perspective in perspectives:
        return perspectives[answer_perspective]
    lowered_query = (query or "").lower()
    for perspective_key, keywords in PERSPECTIVE_KEYWORDS.get(scene_type, []):
        if any(keyword in lowered_query or keyword in query for keyword in keywords):
            return perspectives.get(perspective_key, fallback)
    return fallback


def business_prompt_contract_snapshot() -> Dict[str, Dict[str, Any]]:
    """Return machine-readable prompt contracts for business scenes."""
    snapshot: Dict[str, Dict[str, PromptProfileValue]] = {}
    for scene_type in BUSINESS_PROMPT_SCENES:
        profile = get_scene_prompt_profile(scene_type)
        perspectives = ANSWER_PERSPECTIVES.get(scene_type, {})
        snapshot[scene_type] = {
            "name": profile["name"],
            "focus": profile["focus"],
            "requirements": list(profile["requirements"]),
            "answer_structure": list(profile["answer_structure"]),
            "answer_perspectives": {
                key: {
                    "label": value["label"],
                    "instruction": value["instruction"],
                }
                for key, value in sorted(perspectives.items())
            },
            "safety_contract": [
                "Business tool data is injected as verified 系统接口数据 and should be prioritized for order-level conclusions.",
                "Filtered fields and ignored_result_keys may be mentioned only as allowlist-filtered field names, never as values or business facts.",
                "Contract diagnostics may be cited only as safe upstream response-shape diagnostics.",
                "Runtime or transport failures must not be turned into fabricated order conclusions.",
            ],
        }
    return snapshot


def build_scene_prompt(
    *,
    query: str,
    context: str,
    scene_type: str,
    tool_context: str = "",
    answer_perspective: str = None,
) -> str:
    """Build the final RAG prompt for one scene."""
    profile = get_scene_prompt_profile(scene_type)
    perspective = resolve_answer_perspective(
        query=query,
        scene_type=scene_type,
        answer_perspective=answer_perspective,
    )
    scene_requirements = "\n".join(
        f"{index}. {requirement}"
        for index, requirement in enumerate(profile["requirements"], start=1)
    )
    answer_structure = "\n".join(
        f"{index}. {section}"
        for index, section in enumerate(profile["answer_structure"], start=1)
    )

    tool_section = ""
    if tool_context:
        tool_section = f"""
## 系统接口数据

以下数据来自业务系统工具调用，优先用于回答订单、链路、收入、拦截、命中规则等实时业务问题：

{tool_context}
"""

    return f"""你是一个专业的{profile["name"]}问答助手。请基于以下文档内容和系统接口数据回答用户的问题。
你的重点是：{profile["focus"]}。

## 文档内容

{context}
{tool_section}

## 回答口径

主口径：{perspective["label"]}
{perspective["instruction"]}

## 用户问题

{query}

## 回答要求

通用要求：
1. 准确引用文档和系统接口数据，不要编造内容
2. 如果文档和系统接口数据都没有相关信息，明确告知用户
3. 如果存在系统接口数据，请先给出业务结论，再解释关键字段和计算/判断链路
4. 如果系统接口数据包含工具选择来源、选择依据或选择置信度，回答中要简要说明为什么调用该接口
5. 如果系统接口数据包含链路来源、毛利公式核对、风控证据摘要、合同诊断或其他可验证元信息，回答中要明确引用这些元信息
6. 如果系统接口数据包含合同诊断码、缺失字段或异常字段，只引用这些安全诊断说明上游响应合同不匹配；不要推断缺失金额、规则命中或订单结论
7. 如果系统接口数据包含未展示字段或 ignored_result_keys，只说明这些字段已被展示白名单过滤；不要引用字段值，不要把未展示字段作为业务结论依据
8. 如果系统接口状态为 error，说明实时接口未成功返回数据，不要编造订单实时结论；改用文档解释可验证口径，并提示用户稍后重试或提供审计ID排查
9. 回答要简洁明了，重点突出
10. 如果涉及多个规则、文档或链路节点，请分点说明
11. 在回答末尾注明信息来源（文档编号或系统接口数据）

场景回答结构：
{scene_requirements}

建议输出段落：
{answer_structure}

请开始回答："""
