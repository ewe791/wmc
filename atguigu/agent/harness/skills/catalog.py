from atguigu.agent.harness.skills.definition import SkillCode, SkillDefinition


class SkillCatalog:
    """集中保存 Agent 可以按需加载的领域技能。"""

    def __init__(
            self,
            definitions: tuple[SkillDefinition, ...]
    ):
        self.definitions = {
            definition.code: definition
            for definition in definitions
        }

    def get_skill(self, skill_code: SkillCode) -> SkillDefinition:
        return self.definitions[skill_code]

    def get_skills(self) -> tuple[SkillDefinition, ...]:
        return tuple(self.definitions.values())

    def render_index(self) -> str:
        """渲染供模型选择的精简技能索引"""
        return "\n".join(
            f"- {skill.code}: {skill.description}"
            for skill in self.definitions.values()
        )


SKILL_CATALOG = SkillCatalog(
    (
        SkillDefinition(
            code=SkillCode.PRODUCT_SERVICE,
            description="商品搜索、商品详情、规格、价格和实时库存",
            guidance=(
                "查询入口：用户没有提供商品编号时，先使用 search_products 搜索商品。",
                "工具选择：商品基础信息使用 get_product，实时库存使用 get_product_stock。",
                "可信依据：商品信息和库存结论只能来自对应工具的成功结果。",
                "边界处理：工具失败或没有结果时不得猜测商品信息。"
            ),
            tools=("search_products", "get_product", "get_product_stock")
        ),
        SkillDefinition(
            code=SkillCode.ORDER_SERVICE,
            description="订单列表、订单详情、订单状态、金额和订单页面引导",
            guidance=(
                "查询入口：用户没有提供订单编号时，先使用 list_orders 查询订单列表。",
                "工具选择：查询具体订单的状态、金额和商品信息时使用 get_order。",
                "可信依据：订单结论和具体订单页面动作必须来自 get_order 的成功结果。",
                "边界处理：只有用户明确要求页面引导或提出必须在页面完成的操作时才能生成订单页面动作；取消订单或修改地址不能声称已经执行。"
            ),
            tools=("list_orders", "get_order")
        ),
        SkillDefinition(
            code=SkillCode.LOGISTICS_SERVICE,
            description="具体订单的发货状态、承运公司、运单号和物流轨迹",
            guidance=(
                "查询入口：用户没有提供订单编号时，先使用 list_orders 查询订单列表。",
                "工具选择：订单基础信息使用 get_order，配送进度和物流轨迹使用 get_logistics。",
                "可信依据：物流公司、运单号、状态和轨迹只能来自 get_logistics 的成功结果。",
                "边界处理：物流工具失败或没有结果时不得猜测配送进度。"
            ),
            tools=("list_orders", "get_order", "get_logistics")
        ),
        SkillDefinition(
            code=SkillCode.POLICY_SERVICE,
            description="七天无理由退货及平台售后规则说明，不查询用户的实际售后记录",
            guidance=(
                "查询入口：用户询问平台规则、服务政策或帮助说明时必须先查询知识内容。",
                "工具选择：使用 search_knowledge 查询与用户问题直接相关的知识。",
                "可信依据：平台规则只能来自 search_knowledge 返回的知识内容。",
                "边界处理：知识内容不用于判断用户实际售后申请状态。"
            ),
            tools=("search_knowledge",)
        ),
        SkillDefinition(
            code=SkillCode.AFTER_SALES_SERVICE,
            description="用户实际售后申请记录、处理状态、进度和售后页面引导，不解释平台售后规则",
            guidance=(
                "查询入口：用户询问实际退款、退货或换货进度时，使用 list_after_sales 查询售后记录。",
                "工具选择：用户提供订单编号时按订单查询；生成具体订单页面动作前使用 get_order 确认订单。",
                "可信依据：售后状态和处理进度只能来自 list_after_sales 的成功结果。",
                "边界处理：售后记录不用于解释平台通用售后规则。"
            ),
            tools=("get_order", "list_after_sales")
        )
    )
)
