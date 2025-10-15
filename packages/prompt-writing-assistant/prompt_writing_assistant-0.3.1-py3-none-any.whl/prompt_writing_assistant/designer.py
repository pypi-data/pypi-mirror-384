


## 分析编码习惯


class MeetingMessageHistory:
    def __init__(self):
        self._messages: List[Dict[str, Any]] = []

    def add_message(self, role: str, content: str, speaker_name: str = None):
        """添加一条消息到历史记录。"""
        message = {"role": role, "content": content}
        if speaker_name:
            message["speaker"] = speaker_name # 添加发言者元信息
        self._messages.append(message)

    def get_messages(self) -> List[Dict[str, Any]]:
        """获取当前完整的消息历史。"""
        return self._messages

    def clear(self):
        """清空消息历史。"""
        self._messages = []

    def __str__(self) -> str:
         return "\n".join([f"[{msg.get('speaker', msg['role'])}] {msg['content']}" for msg in self._messages])
    
    
# 模拟一个外部 LLM 调用函数，以便在框架中演示
def simulate_external_llm_call(messages: List[Dict[str, Any]], model_name: str = "default") -> str:
     """模拟调用外部 LLM 函数."""
     print(messages[0].get('speaker'),'messages')
     print(model_name,'model_name')

     bx = BianXieAdapter()
     bx.set_model(model_name)
     result = bx.chat(messages)
     simulated_response = f"[{model_name}] Responding to '{result}"
     return simulated_response

class MeetingOrganizer:
    def __init__(self):
        # 存储参会者信息：名称和使用的模型
        self._participants: List[Dict[str, str]] = []
        self._history = MeetingMessageHistory()
        self._topic: str = ""
        self._background: str = ""
        # TODO: 在实际使用时，这里应该引用您真实的 LLM 调用函数
        self._llm_caller = simulate_external_llm_call # 指向您外部的 LLM 调用函数

    def set_llm_caller(self, caller_func):
         """设置外部的 LLM 调用函数."""
         self._llm_caller = caller_func
         print("External LLM caller function set.")


    def add_participant(self, name: str, model_name: str = "default"):
        """添加一个参会者 (LLM) 到会议中。"""
        participant_info = {"name": name, "model": model_name}
        self._participants.append(participant_info)
        print(f"Added participant: {name} (using model: {model_name})")

    def set_topic(self, topic: str, background: str = ""):
        """设置会议主题和背景。"""
        self._topic = topic
        self._background = background
        initial_message = f"Meeting Topic: {topic}\nBackground: {background}"
        # 可以将主题和背景作为用户输入的第一条消息，或者 system 消息
        self._history.add_message("user", initial_message, speaker_name="Meeting Host")
        print(f"Meeting topic set: {topic}")

    def run_simple_round(self):
        """执行一轮简单的会议：每个参会 LLM 基于当前历史回复一次。"""
        if not self._participants:
            print("No participants in the meeting.")
            return

        print("\n--- Running a Simple Meeting Round ---")
        current_history = self._history.get_messages()

        for participant in self._participants:
            participant_name = participant["name"]
            model_to_use = participant["model"]
            try:
                # 调用外部 LLM 函数
                print(current_history,'current_history')
                response_content = self._llm_caller(current_history, model_name=model_to_use)
                # 将回复添加到历史中，并标记发言者
                self._history.add_message("assistant", response_content, speaker_name=participant_name)
                print(f"'{participant_name}' responded.")
            except Exception as e:
                print(f"Error during '{participant_name}' participation: {e}")
                # 在框架阶段，简单的错误打印即可

    def get_discussion_history(self) -> List[Dict[str, Any]]:
        """获取完整的讨论消息历史。"""
        return self._history.get_messages()

    def get_simple_summary(self) -> str:
        """获取简单的讨论摘要（第一阶段：拼接所有 LLM 发言）。"""
        print("\n--- Generating Simple Summary ---")
        summary_parts = []
        for message in self._history.get_messages():
            # 提取 assistant 角色的发言作为摘要内容
            if message.get("role") == "assistant":
                 speaker = message.get("speaker", "Unknown Assistant")
                 summary_parts.append(f"[{speaker}]: {message['content']}")

        return "\n\n".join(summary_parts)

    def display_history(self):
         """打印格式化的讨论历史。"""
         print("\n--- Full Discussion History ---")
         print(self._history)
