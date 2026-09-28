from atguigu.agent.harness.errors import AgentOutputValidationError, CorrectableErrorCode

from atguigu.agent.harness.rules.action import ACTION_CATALOG, PageAction

from atguigu.agent.harness.tools.snapshot import ToolCallSnapshot
from atguigu.agent.llm.output import PageActionRequest


class PageActionValidationError(AgentOutputValidationError):
    """表示 Agent 提出的页面动作不符合安全规则"""


class PageActionValidator:
    """校验页面动作编码及其关联的业务对象"""

    def validate(
            self,
            request: PageActionRequest | None,
            tool_calls: tuple[ToolCallSnapshot, ...]
    ) -> PageAction | None:
        """返回经过校验并由服务端生成的页面动作"""

        # 1. 模型没有请求页面动作时直接返回空结果
        if request is None:
            return None

        # 2. 从服务端动作目录读取模型请求的动作定义
        action_code = request.action_code
        definition = ACTION_CATALOG.get_definition(action_code)

        # 3. 不关联具体业务对象的动作可以直接生成
        if definition.resource_type is None:
            return definition.build()

        # 4. 规范需要页面动作引用的业务对象编号
        resource_id = self._normalize_resource_id(request.resource_id)

        # 5. 校验页面动作引用的订单已经被工具确认
        self._require_verified_order(resource_id, tool_calls)

        # 6. 使用服务端固定定义生成可信页面动作
        return definition.build(resource_id)

    def _require_verified_order(
            self,
            resource_id: str,
            tool_calls: tuple[ToolCallSnapshot, ...]
    ):
        """要求当前 Run 成功查询过页面动作引用的订单"""

        # 1. 检查成功订单详情工具的参数是否匹配目标订单
        has_verified_order = any(
            tool_call.tool_name == "get_order"
            and tool_call.success is True
            and self._normalize_resource_id(tool_call.arguments["order_id"]) == resource_id for tool_call in tool_calls
        )
        # 2. 拒绝引用未经过成功工具结果确认的订单
        if not has_verified_order:
            raise PageActionValidationError(
                CorrectableErrorCode.UNVERIFIED_ACTION_RESOURCE,
                f"页面动作引用的订单未经工具确认：{resource_id}"
            )

    @staticmethod
    def _normalize_resource_id(resource_id: str) -> str:
        """统一业务对象编号格式。"""
        # 1. 清理空格、统一大小写并规范编号连接符
        return resource_id.strip().upper().replace("-", "_")
