from langchain.agents.middleware import ModelRequest, dynamic_prompt

from atguigu.agent.harness.rules.action import ACTION_CATALOG
from atguigu.agent.harness.skills.catalog import SKILL_CATALOG
from atguigu.agent.harness.skills.definition import SkillCode
from atguigu.agent.llm.prompt import BASE_PROMPT


def render_skill_prompt(active_skill_code: SkillCode | None) -> str:
    """根据当前状态生成 Skill 提示词"""

    if active_skill_code is None:
        return (
            "【动态 Skill 路由】\n"
            "用户询问商品、订单、物流、售后记录或平台规则时，先调用 load_skill 加载对应领域；普通寒暄可以直接回答。\n"
            "用户同时询问多个领域时，一次只处理一个 Skill；完成当前领域所需查询后，再切换到下一个 Skill。\n"
            f"可用 Skill：\n{SKILL_CATALOG.render_index()}"
        )

    skill = SKILL_CATALOG.get_skill(active_skill_code)
    guidance = "\n".join(f"- {item}" for item in skill.guidance)

    return (
        f"【当前 Skill：{skill.code}】\n"
        f"{guidance}\n"
        "用户同时询问多个领域时，一次只处理一个 Skill；完成当前领域所需查询后，再切换到下一个 Skill。"
    )


def render_support_prompt(active_skill_code: SkillCode | None) -> str:
    """根据当前 Skill 生成完整的客服系统提示词"""

    skill_prompt = render_skill_prompt(active_skill_code)
    action_prompt = f"【白名单页面动作】\n{ACTION_CATALOG.render_action_index()}"

    return f"{BASE_PROMPT}\n\n{skill_prompt}\n\n{action_prompt}"


@dynamic_prompt
def support_prompt(request: ModelRequest) -> str:
    """为每次模型调用生成当前能力范围内的系统提示词"""

    return render_support_prompt(request.state.get("active_skill_code"))
