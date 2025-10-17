def test__():

    # # 1. 导入必要的类和外部 LLM 调用函数
    from llm_councilz.meeting.core import MeetingOrganizer # 暂时使用模拟函数

    # 2. 创建会议组织者
    organizer = MeetingOrganizer()

    # 3. 设置外部 LLM 调用函数 (!!! 重要步骤，连接框架和您的能力)
    # organizer.set_llm_caller(call_your_llm_api) # 在实际使用时，取消注释并替换

    # 4. 添加参与者 (LLM)
    organizer.add_participant(name="专家A", model_name="gpt-4o")
    organizer.add_participant(name="专家B", model_name="gpt-4.1")
    # organizer.add_participant(name="专家C", model_name="model-gamma")

    # 5. 设置会议主题
    topic = "制定一个针对中小型企业的数字化转型方案"
    background = "考虑到成本和实施难度，方案应侧重于易于落地和快速见效。"
    organizer.set_topic(topic, background)

    # 6. 运行一轮简单的会议
    organizer.run_simple_round()

    # 7. 获取讨论历史和简单摘要
    organizer.display_history() # 打印格式化历史

    simple_summary = organizer.get_simple_summary()
    print("\nGenerated Simple Summary:")
    print(simple_summary)