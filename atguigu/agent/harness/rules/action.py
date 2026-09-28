from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import quote

from pydantic import BaseModel


class ActionCode(StrEnum):
    """定义服务端允许生成的页面动作编码"""
    BROWSE_ORDERS = "BROWSE_ORDERS"
    OPEN_ORDER_DETAIL = "OPEN_ORDER_DETAIL"
    CANCEL_ORDER = "CANCEL_ORDER"
    EDIT_ADDRESS = "EDIT_ADDRESS"
    APPLY_AFTER_SALE = "APPLY_AFTER_SALE"
    VIEW_AFTER_SALES = "VIEW_AFTER_SALES"


class PageAction(BaseModel):
    """定义返回给前端的安全页面动作。"""

    label: str
    description: str
    href: str


@dataclass(frozen=True)
class ActionDefinition:
    """定义一个页面动作的展示信息和路径模板。"""

    action_code: ActionCode
    label: str
    description: str
    path_template: str
    resource_type: str | None = None

    def build(
            self,
            resource_id: str | None = None
    ) -> PageAction:
        """使用具体业务对象编号生成页面动作"""

        # 1. 对业务对象编号进行安全的 URL 路径编码
        encoded_resource_id = quote(resource_id or "", safe="")

        # 2. 使用服务端固定文案和路径模板构建页面动作
        return PageAction(
            label=self.label,
            description=self.description,
            href=self.path_template.format(resource_id=encoded_resource_id)
        )


class ActionCatalog:
    """集中保存服务端允许生成的页面动作"""

    def __init__(
            self,
            definitions: tuple[ActionDefinition, ...]
    ):
        self.definitions = {
            definition.action_code: definition
            for definition in definitions
        }

    def get_definition(self, action_code: ActionCode) -> ActionDefinition:
        """根据动作编码返回页面动作定义"""

        return self.definitions[action_code]

    def render_action_index(self) -> str:
        """渲染供模型选择的页面动作索引"""
        return "\n".join(
            f"- {definition.action_code}: {definition.description}"
            for definition in self.definitions.values()
        )

    def build_page_action(
            self,
            action_code: ActionCode,
            resource_id: str | None = None
    ) -> PageAction:
        """根据动作编码和资源编号生成页面动作"""

        # 读取动作定义并使用业务对象编号生成安全动作
        return self.get_definition(action_code).build(resource_id)


ACTION_CATALOG = ActionCatalog(
    (
        ActionDefinition(
            action_code=ActionCode.BROWSE_ORDERS,
            label="查看我的订单",
            description="进入我的订单列表",
            path_template="/me"
        ),
        ActionDefinition(
            action_code=ActionCode.OPEN_ORDER_DETAIL,
            label="查看订单详情",
            description="进入订单详情查看状态与可用操作",
            path_template="/me/orders/{resource_id}",
            resource_type="order"
        ),
        ActionDefinition(
            action_code=ActionCode.CANCEL_ORDER,
            label="前往取消订单",
            description="进入订单页面核对状态并确认取消",
            path_template="/me/orders/{resource_id}/cancel",
            resource_type="order"
        ),
        ActionDefinition(
            action_code=ActionCode.EDIT_ADDRESS,
            label="前往修改地址",
            description="进入订单页面修改收货地址",
            path_template="/me/orders/{resource_id}/address",
            resource_type="order"
        ),
        ActionDefinition(
            action_code=ActionCode.APPLY_AFTER_SALE,
            label="申请售后",
            description="进入订单页面填写售后申请",
            path_template="/me/orders/{resource_id}/after-sale",
            resource_type="order"
        ),
        ActionDefinition(
            action_code=ActionCode.VIEW_AFTER_SALES,
            label="查看售后进度",
            description="进入订单页面查看售后记录",
            path_template="/me/orders/{resource_id}?section=after-sales",
            resource_type="order"
        ),
    )
)
