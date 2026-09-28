from pydantic import BaseModel, Field


class KnowledgeItem(BaseModel):
    """定义知识查询返回的一条可信知识内容。"""

    knowledge_id: str = Field(min_length=1,description="知识内容的稳定编号")
    title: str = Field(min_length=1,description="知识内容标题")
    content: str = Field(min_length=1,description="Agent 可以用于回答的知识正文")
    source: str = Field(min_length=1,description="知识内容的来源说明")
