from dataclasses import dataclass
from enum import StrEnum

from langchain_core.tools import BaseTool

from atguigu.agent.harness.tools.read import (
    get_logistics,
    get_order,
    get_product,
    get_product_stock,
    list_after_sales,
    list_orders,
    search_products, search_knowledge
)
from atguigu.agent.harness.tools.skill import load_skill


class ToolCategory(StrEnum):
    """定义工具返回的数据类别"""

    BUSINESS = "BUSINESS"
    KNOWLEDGE = "KNOWLEDGE"
    GUIDANCE = "GUIDANCE"


@dataclass(frozen=True)
class ToolDefinition:
    """组合一个 Agent 工具及其数据类别"""

    tool: BaseTool
    category: ToolCategory


class ToolCatalog:
    """集中保存 Agent 可以使用的工具定义"""

    def __init__(self, definitions: tuple[ToolDefinition, ...]):
        self.definitions = {
            definition.tool.name: definition
            for definition in definitions
        }

    def get_agent_tools(self) -> list[BaseTool]:
        """返回注册到 Agent 的全部工具"""
        return [
            definition.tool
            for definition in self.definitions.values()
        ]

    def get_tool_definition(self, tool_name: str) -> ToolDefinition:
        """根据工具名称返回完整定义"""
        return self.definitions[tool_name]

    def get_tool_category(self, tool_name: str) -> ToolCategory:
        """根据工具名称返回数据类别"""
        definition = self.get_tool_definition(tool_name)
        return definition.category


TOOL_CATALOG = ToolCatalog(
    (
        ToolDefinition(search_products, ToolCategory.BUSINESS),
        ToolDefinition(get_product, ToolCategory.BUSINESS),
        ToolDefinition(get_product_stock, ToolCategory.BUSINESS),
        ToolDefinition(list_orders, ToolCategory.BUSINESS),
        ToolDefinition(get_order, ToolCategory.BUSINESS),
        ToolDefinition(get_logistics, ToolCategory.BUSINESS),
        ToolDefinition(list_after_sales, ToolCategory.BUSINESS),
        ToolDefinition(search_knowledge, ToolCategory.KNOWLEDGE),
        ToolDefinition(load_skill, ToolCategory.GUIDANCE)
    )
)
