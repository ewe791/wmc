from atguigu.agent.harness.knowledge.output import KnowledgeItem


class KnowledgeQueryService:
    """提供 Agent 使用的知识查询能力。"""

    async def search(self, query: str) -> list[KnowledgeItem]:
        """根据查询内容返回知识结果。"""
        # 1. 空查询不返回知识内容
        if not query.strip():
            return []

        # 2. 暂时返回固定数据，后续可以替换为真实知识库查询
        return [
            KnowledgeItem(
                knowledge_id="KNOWLEDGE_AFTER_SALE_001",
                title="七天无理由退货规则",
                content="符合平台七天无理由退货范围的商品，可以在签收后七天内申请退货。商品应保持完好",
                source="平台退货规则"
            ),
            KnowledgeItem(
                knowledge_id="KNOWLEDGE_AFTER_SALE_002",
                title="退款到账规则",
                content="退款申请审核通过后，款项将原路退回支付账户。到账时间受支付机构处理进度影响",
                source="平台退款规则"
            ),
            KnowledgeItem(
                knowledge_id="KNOWLEDGE_AFTER_SALE_003",
                title="退货商品寄回规则",
                content="退货申请审核通过后，请在售后页面规定的时间内寄回商品。退货商品应保持完好，逾期未寄回的申请可能自动关闭。",
                source="平台售后规则"
            )
        ]
