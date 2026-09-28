import json

from langchain_core.messages import BaseMessage, AIMessage, HumanMessage

from atguigu.app.schemas.run import AgentRunRequest, HistoryMessage, CurrentMessage
from atguigu.common.config import get_settings


class ContextCompiler:

    def __init__(self):
        self.setting = get_settings()

    def compile_messages(self, request: AgentRunRequest) -> list[BaseMessage]:
        """
        职责：构建历史消息和当前用户的消息
        """
        # AIMessage   HumanMessage  SystemMessage

        # 1. 构建历史消息(裁减)

        candidate_history_messages: list[HistoryMessage] = self._bounded_history_message(request.history)

        # 2. 标准化LangChain统一的消息格式
        messages = [
            (
                HumanMessage(content=self._format_message(message))
                if message.role == "user"
                else AIMessage(content=self._format_message(message))
            )
            for message in candidate_history_messages
        ]

        # 3. 构建用户当前消息，追加到标准化LangChain统一的消息格式中
        messages.append(HumanMessage(content=self._build_current_message(request.messages)))

        # 4. 返回
        return messages

    def _bounded_history_message(self, history: list[HistoryMessage]) -> list[HistoryMessage]:
        """
        职责：根据消息条数以及字符以及留下从第一条用户角色的消息开始。
        1. 根据消息条数裁减
        2. 根据字符数做裁减
        3. 从用户角色的消息开始留
        """

        # 1. 根据消息条数裁减
        history_messages = history[-self.setting.history_message_limit:]

        # 2.根据字符数做裁减(倒序)
        used_characters = 0
        messages = []
        for message in reversed(history_messages):

            current_message_len = len(self._format_message(message))

            if current_message_len + used_characters > self.setting.history_character_budget:
                break

            messages.append(message)
            used_characters = used_characters + current_message_len

        # 3. 反转
        messages.reverse()

        # 4. 从用户角色的消息开始留(生成器对象)

        start_user_message_index = next(
            (index for index, message in enumerate(messages) if message.role == "user"),
            len(messages)
        )

        # 5. 从第一条消息角色是用户的开始留
        return messages[start_user_message_index:]

    def _format_message(self, message: CurrentMessage) -> str:
        """
        职责：处理两种格式的消息类型(文本【text】、点击卡片【对象：object】)

        """

        if message.type == "text":
            return str(message.content['text'])

        return "【用户发送的消息是一个对象】\n" + json.dumps(message.content, ensure_ascii=False)

    def _build_current_message(self, current_messages: list[CurrentMessage]) -> str:
        """
         职责：构建用户当前消息 单条[一个轮次] or 多条[一个轮次]
        """
        # 1. 获取到当前消息列表中的内容列表
        current_message_contents = [
            self._format_message(current_message)
            for current_message in current_messages
        ]

        # 2. 判断内容列表的长度
        if len(current_message_contents) == 1:
            return current_message_contents[0]

        # 3. 组装
        # 1. xxxx
        # 2. yyyy

        items = "\n".join(
            f"{index}. {current_content}" for index, current_content in enumerate(current_message_contents, 1))

        return "用户连续输入了多条消息，请作为一个整体理解，并且基于当前最新内容为准: \n" + f"{items}"
