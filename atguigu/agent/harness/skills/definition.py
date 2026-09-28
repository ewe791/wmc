from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class SkillCode(StrEnum):
    """定义 Agent 可以加载的技能编码。"""

    PRODUCT_SERVICE = "product-service"
    ORDER_SERVICE = "order-service"
    LOGISTICS_SERVICE = "logistics-service"
    AFTER_SALES_SERVICE = "aftersales-service"
    POLICY_SERVICE = "policy-service"


class SkillDefinition(BaseModel):
    """定义一项技能向 Agent 提供的处理说明。"""

    model_config = ConfigDict(frozen=True)

    code: SkillCode = Field(
        description="技能的稳定编码"
    )
    description: str = Field(
        min_length=1,
        description="技能适用的问题范围"
    )
    guidance: tuple[str, ...] = Field(
        min_length=1,
        description="Agent 使用技能时必须遵守的处理规则"
    )
    tools: tuple[str, ...] = Field(
        min_length=1,
        description="技能允许使用的工具名称"
    )
