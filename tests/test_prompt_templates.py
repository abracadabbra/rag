"""
Prompt template contract tests.
"""

from api.services.prompt_templates import (
    ANSWER_PERSPECTIVES,
    SCENE_PROMPT_PROFILES,
    business_prompt_contract_snapshot,
    build_scene_prompt,
    get_scene_prompt_profile,
    infer_answer_perspective,
    resolve_answer_perspective,
)


def test_prompt_profiles_cover_business_and_core_scenes():
    assert set(SCENE_PROMPT_PROFILES) >= {
        "risk_rule",
        "profit",
        "model_card",
        "simulation",
    }
    assert "风控结论" in "".join(SCENE_PROMPT_PROFILES["risk_rule"]["requirements"])
    assert "财务口径" in "".join(SCENE_PROMPT_PROFILES["profit"]["requirements"])
    assert "运营口径" in "".join(SCENE_PROMPT_PROFILES["profit"]["requirements"])
    assert "answer_structure" in SCENE_PROMPT_PROFILES["risk_rule"]
    assert "answer_structure" in SCENE_PROMPT_PROFILES["profit"]
    assert "finance" in ANSWER_PERSPECTIVES["profit"]
    assert "strategy" in ANSWER_PERSPECTIVES["risk_rule"]


def test_business_prompt_contract_snapshot_exports_business_answer_contracts():
    snapshot = business_prompt_contract_snapshot()

    assert set(snapshot) == {"risk_rule", "profit"}
    assert snapshot["profit"]["name"] == "毛利抽成"
    assert "finance" in snapshot["profit"]["answer_perspectives"]
    assert "operations" in snapshot["profit"]["answer_perspectives"]
    assert "technical" in snapshot["profit"]["answer_perspectives"]
    assert snapshot["risk_rule"]["answer_perspectives"]["strategy"]["label"] == "风控策略口径"
    assert any(
        "ignored_result_keys" in rule
        for rule in snapshot["profit"]["safety_contract"]
    )
    assert any(
        "Contract diagnostics" in rule
        for rule in snapshot["risk_rule"]["safety_contract"]
    )


def test_build_profit_scene_prompt_prioritizes_tool_context():
    prompt = build_scene_prompt(
        query="查询订单 ORD88888 的抽成和司机收入",
        context="【文档 1】平台抽成按订单规则计算",
        scene_type="profit",
        tool_context=(
            "订单 ORD88888 平台抽成 19.29 元，司机收入 92.35 元，平台净毛利 2.33 元。\n"
            "链路来源: 接口原生链路\n"
            "毛利公式核对: 平台抽成 - 平台补贴 - 用户优惠 - 渠道费 = 计算净毛利；"
            "计算值 2.33 元，接口净毛利 2.33 元，差异 +0.00 元，状态: 一致"
        ),
    )

    assert "你是一个专业的毛利抽成问答助手" in prompt
    assert "## 系统接口数据" in prompt
    assert "订单 ORD88888 平台抽成 19.29 元" in prompt
    assert "毛利公式核对: 平台抽成 - 平台补贴 - 用户优惠 - 渠道费 = 计算净毛利" in prompt
    assert "计算值 2.33 元，接口净毛利 2.33 元，差异 +0.00 元，状态: 一致" in prompt
    assert "钱流链路" in prompt
    assert "平台抽成" in prompt
    assert "司机收入" in prompt
    assert "财务口径" in prompt
    assert "运营口径" in prompt
    assert "避免把乘客支付直接当作平台收入" in prompt
    assert "## 回答口径" in prompt
    assert "主口径：运营口径" in prompt
    assert "可行动异常" in prompt
    assert "建议输出段落" in prompt
    assert "订单结论：用一句话说明平台净毛利、结算状态和是否异常" in prompt
    assert "为什么调用该接口" in prompt
    assert "如果系统接口数据包含链路来源，明确说明该链路是接口原生返回还是按最小合同自动派生" in prompt
    assert "如果系统接口数据包含工具选择来源、选择依据或置信度，简要说明为什么查询该毛利接口" in prompt
    assert "如果系统接口数据包含链路来源、毛利公式核对、风控证据摘要、合同诊断或其他可验证元信息，回答中要明确引用这些元信息" in prompt
    assert "如果系统接口数据包含毛利公式核对，明确说明计算净毛利与接口净毛利是否一致；不一致时提示复核上游金额字段或接口合同" in prompt
    assert "只引用这些安全诊断说明上游响应合同不匹配" in prompt
    assert "不要推断缺失金额、规则命中或订单结论" in prompt
    assert "未展示字段" in prompt
    assert "展示白名单过滤" in prompt
    assert "不要引用字段值" in prompt
    assert "不要推断缺失金额、抽成或司机收入" in prompt
    assert "钱流链路：按乘客支付、平台抽成、司机收入、补贴、优惠、渠道费、净毛利说明，并交代链路来源（接口原生/自动派生）" in prompt
    assert "财务口径：区分收入、成本、补贴优惠、渠道费和平台净毛利，并引用毛利公式核对状态" in prompt
    assert "信息来源：列出工具选择来源/依据、系统接口、审计ID和文档编号" in prompt


def test_build_risk_scene_prompt_keeps_explainability_contract():
    prompt = build_scene_prompt(
        query="订单 ORD12345 为什么被拦截？",
        context="【文档 1】高风险订单需要二次验证",
        scene_type="risk_rule",
        tool_context=(
            "风控证据摘要: 决策=block，风险分=87，风险等级=high，"
            "命中规则数=1，建议动作=建议保持拦截，命中规则=短时间多次高额交易(RISK-velocity-001)"
        ),
    )

    assert "你是一个专业的风控规则问答助手" in prompt
    assert "## 系统接口数据" in prompt
    assert "风控证据摘要: 决策=block，风险分=87，风险等级=high" in prompt
    assert "风控结论" in prompt
    assert "命中规则/依据" in prompt
    assert "处置建议" in prompt
    assert "风控策略视角" in prompt
    assert "规则阈值" in prompt
    assert "如果系统接口数据包含风控证据摘要，必须引用决策、风险分、风险等级、命中规则数和建议动作" in prompt
    assert "主口径：风控策略口径" in prompt
    assert "建议输出段落" in prompt
    assert "结论：用一句话说明风控决策、风险等级和建议动作" in prompt
    assert "命中依据：优先引用风控证据摘要" in prompt
    assert "如果系统接口数据包含工具选择来源、选择依据或选择置信度，回答中要简要说明为什么调用该接口" in prompt
    assert "如果系统接口数据包含链路来源、毛利公式核对、风控证据摘要、合同诊断或其他可验证元信息，回答中要明确引用这些元信息" in prompt
    assert "如果系统接口数据包含未展示字段或 ignored_result_keys，只说明这些字段已被展示白名单过滤" in prompt
    assert "不要推断规则命中或风险结论" in prompt
    assert "信息来源：列出系统接口、审计ID和文档编号" in prompt


def test_profit_prompt_uses_finance_perspective_for_financial_questions():
    prompt = build_scene_prompt(
        query="从财务口径看订单 ORD88888 的净毛利和成本结构",
        context="【文档 1】毛利口径说明",
        scene_type="profit",
        tool_context="平台净毛利 2.33 元，补贴 8 元，优惠 6 元。",
    )

    assert "主口径：财务口径" in prompt
    assert "区分收入、成本、补贴优惠、渠道费和平台净毛利" in prompt
    assert "避免把乘客支付当作平台收入" in prompt


def test_build_scene_prompt_honors_explicit_answer_perspective():
    prompt = build_scene_prompt(
        query="运营看这个订单 ORD88888 的补贴是否异常",
        context="【文档 1】毛利口径说明",
        scene_type="profit",
        tool_context="平台净毛利 2.33 元，补贴 8 元。",
        answer_perspective="finance",
    )

    assert "主口径：财务口径" in prompt
    assert "重点区分收入、成本、补贴优惠、渠道费和平台净毛利" in prompt


def test_invalid_explicit_answer_perspective_falls_back_to_inference():
    perspective = resolve_answer_perspective(
        query="运营看这个补贴优惠是否异常",
        scene_type="profit",
        answer_perspective="strategy",
    )

    assert perspective["label"] == "运营口径"


def test_business_prompt_uses_technical_perspective_for_debug_questions():
    profit_prompt = build_scene_prompt(
        query="这个毛利接口报错了，按审计ID帮我排查字段问题",
        context="【文档 1】接口排查说明",
        scene_type="profit",
        tool_context="状态: error\n审计ID: bt-error123",
    )
    risk_prompt = build_scene_prompt(
        query="风控接口失败，按 audit id 排查字段缺失",
        context="【文档 1】风控接口排查说明",
        scene_type="risk_rule",
        tool_context="状态: error\n审计ID: bt-riskerror",
    )

    assert "主口径：技术排查口径" in profit_prompt
    assert "合同诊断码" in profit_prompt
    assert "链路节点缺失" in profit_prompt
    assert "主口径：技术排查口径" in risk_prompt
    assert "合同诊断码" in risk_prompt
    assert "字段缺失或异常" in risk_prompt


def test_business_perspective_keyword_contracts():
    cases = [
        ("risk_rule", "给运营一个用户解释和处置口径", "运营解释口径"),
        ("risk_rule", "按风控策略阈值复核这个命中规则", "风控策略口径"),
        ("risk_rule", "风控接口失败，按审计ID排查字段", "技术排查口径"),
        ("profit", "从财务口径看净毛利和成本", "财务口径"),
        ("profit", "运营看这个补贴优惠是否异常", "运营口径"),
        ("profit", "毛利接口失败，按审计ID排查字段", "技术排查口径"),
        ("profit", "查询订单 ORD88888 的整体钱流", "综合毛利分析口径"),
    ]

    for scene_type, query, expected_label in cases:
        assert infer_answer_perspective(query, scene_type)["label"] == expected_label


def test_risk_prompt_uses_operations_perspective_for_user_explanations():
    prompt = build_scene_prompt(
        query="给运营一个用户解释和处置口径，说明订单 ORD12345 为什么需要补充验证",
        context="【文档 1】风控处置说明",
        scene_type="risk_rule",
        tool_context="订单 ORD12345 风控决策为 block，风险分 87。",
    )

    assert "主口径：运营解释口径" in prompt
    assert "可对运营或用户说明的原因" in prompt
    assert "补充验证动作" in prompt
    assert "处置建议" in prompt


def test_infer_answer_perspective_uses_balanced_fallback():
    perspective = infer_answer_perspective(
        query="查询订单 ORD88888 的整体情况",
        scene_type="profit",
    )

    assert perspective["label"] == "综合毛利分析口径"


def test_build_scene_prompt_handles_business_tool_error_degradation():
    prompt = build_scene_prompt(
        query="查询订单 ORD88888 的毛利链路",
        context="【文档 1】毛利口径说明",
        scene_type="profit",
        tool_context=(
            "【工具 1】订单毛利链路\n"
            "状态: error\n"
            "审计ID: bt-error123\n"
            "合同诊断码: missing_required_fields\n"
            "缺失字段: ['platform_net_profit']\n"
            "摘要: 订单毛利链路调用失败，请稍后重试或联系系统管理员。"
        ),
    )

    assert "状态: error" in prompt
    assert "合同诊断码: missing_required_fields" in prompt
    assert "缺失字段: ['platform_net_profit']" in prompt
    assert "只引用这些安全诊断说明上游响应合同不匹配" in prompt
    assert "不要推断缺失金额、规则命中或订单结论" in prompt
    assert "如果系统接口数据包含未展示字段或 ignored_result_keys" in prompt
    assert "实时接口未成功返回数据" in prompt
    assert "不要编造订单实时结论" in prompt
    assert "审计ID" in prompt
    assert "稍后重试" in prompt


def test_unknown_scene_uses_safe_default_profile():
    profile = get_scene_prompt_profile("ops")
    prompt = build_scene_prompt(
        query="这个问题怎么处理？",
        context="【文档 1】处理步骤",
        scene_type="ops",
    )

    assert profile["name"] == "ops"
    assert "你是一个专业的ops问答助手" in prompt
    assert "先回答用户的核心问题" in prompt
    assert "引用可验证的文档或系统接口依据" in prompt
    assert "建议输出段落" in prompt
    assert "结论：先回答用户的核心问题" in prompt
    assert "限制：说明缺失信息和不确定性" in prompt
