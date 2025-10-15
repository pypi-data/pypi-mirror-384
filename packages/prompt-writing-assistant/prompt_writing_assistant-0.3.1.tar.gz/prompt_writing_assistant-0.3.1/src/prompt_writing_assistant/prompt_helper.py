# 测试1

from prompt_writing_assistant.utils import extract_
from prompt_writing_assistant.log import Log
from llmada.core import BianXieAdapter, ArkAdapter
from datetime import datetime
from enum import Enum
import functools
import json
import os

from llama_index.core import PromptTemplate

from prompt_writing_assistant.database import Base, Prompt, UseCase
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from prompt_writing_assistant.utils import create_session

from contextlib import contextmanager



logger = Log.logger
editing_log = logger.debug


class IntellectType(Enum):
    train = "train"
    inference = "inference"
    summary = "summary"

class Intel():
    def __init__(self,
                 database_url = "",
                 model_name = "",
                ):
        database_url = database_url or os.getenv("database_url")
        assert database_url
        self.engine = create_engine(database_url, echo=False, # echo=True 仍然会打印所有执行的 SQL 语句
                                    pool_size=10,        # 连接池中保持的连接数
                                    max_overflow=20,     # 当pool_size不够时，允许临时创建的额外连接数
                                    pool_recycle=3600,   # 每小时回收一次连接
                                    pool_pre_ping=True,  # 使用前检查连接活性
                                    pool_timeout=30      # 等待连接池中连接的最长时间（秒）
                                    ) 
        Base.metadata.create_all(self.engine)
        if model_name in ["gemini-2.5-flash-preview-05-20-nothinking",]:
            self.llm = BianXieAdapter(model_name = model_name)
        elif model_name in ["doubao-1-5-pro-256k-250115",]:
            self.llm = ArkAdapter(model_name = model_name)
        else:
            print('error Intel.model_name params')
            self.llm = BianXieAdapter()
            
        
    def _get_latest_prompt_version(self,target_prompt_id,session):
        """
        获取指定 prompt_id 的最新版本数据，通过创建时间判断。
        """
        
        result = session.query(Prompt).filter(
            Prompt.prompt_id == target_prompt_id
        ).order_by(
            Prompt.timestamp.desc(),
            Prompt.version.desc()
        ).first()

        if result:
            editing_log(f"找到 prompt_id '{target_prompt_id}' 的最新版本 (基于时间): {result.version}")
        else:
            editing_log(f"未找到 prompt_id '{target_prompt_id}' 的任何版本。")
        return result

    def _get_specific_prompt_version(self,target_prompt_id, target_version,session):
        """
        获取指定 prompt_id 和特定版本的数据。

        Args:
            target_prompt_id (str): 目标提示词的唯一标识符。
            target_version (int): 目标提示词的版本号。
            table_name (str): 存储提示词数据的数据库表名。
            db_manager (DBManager): 数据库管理器的实例，用于执行查询。

        Returns:
            dict or None: 如果找到，返回包含 id, prompt_id, version, timestamp, prompt 字段的字典；
                        否则返回 None。
        """

        result = session.query(Prompt).filter(
            Prompt.prompt_id == target_prompt_id,
            Prompt.version == target_version
        ).first() # 因为 (prompt_id, version) 是唯一的，所以 first() 足够
        if result:
            editing_log(f"找到 prompt_id '{target_prompt_id}', 版本 '{target_version}' 的提示词数据。")
        else:
            editing_log(f"未找到 prompt_id '{target_prompt_id}', 版本 '{target_version}' 的提示词数据。")
        return result

    def get_prompts_from_sql(self,
                             prompt_id: str,
                             version = None,
                             return_use_case = False) -> tuple[str, int, str]:
        """
        从sql获取提示词
        """
        with create_session(self.engine) as session:
            # 查看是否已经存在
            if version:
                user_by_id_1 = self._get_specific_prompt_version(prompt_id,version,session=session)
                if user_by_id_1:
                    # 如果存在获得
                    # prompt = user_by_id_1.get("prompt")
                    prompt = user_by_id_1.prompt
                    status = 1
                else:
                    # 否则提示warning 然后调用最新的
                    user_by_id_1 = self._get_latest_prompt_version(prompt_id,session = session)
                    if user_by_id_1:
                        # 打印正在使用什么版本
                        # prompt = user_by_id_1.get("prompt")
                        prompt = user_by_id_1.prompt
                        status = 1
                    else:
                        # 打印, 没有找到 warning 
                        # 如果没有则返回空
                        prompt = ""
                        status = 0
                    status = 1

            else:
                user_by_id_1 = self._get_latest_prompt_version(prompt_id,session = session)
                if user_by_id_1:
                    # 如果存在获得
                    # prompt = user_by_id_1.get("prompt")
                    prompt = user_by_id_1.prompt

                    status = 1
                else:
                    # 如果没有则返回空
                    prompt = ""
                    status = 0

            
            if not return_use_case:
                return prompt, status
            else:
                if user_by_id_1:
                    editing_log(user_by_id_1)
                    return prompt, status, user_by_id_1.use_case #user_by_id_1.get('use_case',' 空 ')
                else:
                    return prompt, status, ' 空 '


    def save_prompt_by_sql(self,
                           prompt_id: str,
                           new_prompt: str,
                           input_data:str = ""):
        """
        从sql保存提示词
        input_data 指的是输入用例, 可以为空
        """
        # 查看是否已经存在
        with create_session(self.engine) as session:
            user_by_id_1 = self._get_latest_prompt_version(prompt_id,session = session)
            
            if user_by_id_1:
                # 如果存在版本加1
                version_ori = user_by_id_1.version
                _, version = version_ori.split(".")
                version = int(version)
                version += 1
                version_ = f"1.{version}"

            else:
                # 如果不存在版本为1.0
                version_ = '1.0'
            
            prompt1 = Prompt(prompt_id=prompt_id, 
                            version=version_,
                            timestamp=datetime.now(),
                            prompt = new_prompt,
                            use_case = input_data,
                            action_type = "inference",
                            demand = ""
                            )

            session.add(prompt1)
            session.commit() # 提交事务，将数据写入数据库


    def save_use_case_by_sql(self,
                             prompt_id: str,
                             use_case:str = "",
                             output = "",
                             solution: str = ""
                            ):
        """
        从sql保存提示词
        """
        with create_session(self.engine) as session:
            use_case = UseCase(prompt_id=prompt_id, 
                           use_case = use_case,
                           output = output,
                           solution = solution,
                           )

            session.add(use_case)
            session.commit() # 提交事务，将数据写入数据库

    def push_train_order(self,demand : str,prompt_id: str,
                         action_type = 'train'):

        """
        从sql保存提示词
        推一个train 状态到指定的位置

        将打算修改的状态推上数据库 # 1
        """
        # 查看是否已经存在
        with create_session(self.engine) as session:
            
            latest_prompt = self._get_latest_prompt_version(prompt_id,session = session)
            if latest_prompt:
                latest_prompt.action_type = action_type
                latest_prompt.demand = demand
                
                session.commit() # 提交事务，将数据写入数据库
                return "success"
            else:
                return "未找到"

    def intellect_remove_warp(self,prompt_id: str):
        def outer_packing(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 修改逻辑
                assert kwargs.get('input_data') # 要求一定要有data入参
                input_data = kwargs.get('input_data')
                assert kwargs.get('output_format') # 要求一定要有data入参
                output_format = kwargs.get('output_format')

                if isinstance(input_data,dict):
                    input_ = output_ = json.dumps(input_data,ensure_ascii=False)
                elif isinstance(input_data,str):
                    input_ = output_ = input_data

                output_ = self.intellect_remove(
                        input_data = input_data,
                        output_format = output_format,
                        prompt_id = prompt_id
                )

                #######
                kwargs.update({"input_data":output_})
                result = func(*args, **kwargs)
                return result
            return wrapper
        return outer_packing

    def intellect_remove(self,
                    input_data: dict | str,
                    output_format: str,
                    prompt_id: str,
                    version: str = None,
                    inference_save_case = True,
                    ):
        if isinstance(input_data,dict):
            input_ = json.dumps(input_data,ensure_ascii=False)
        elif isinstance(input_data,str):
            input_ = input_data


        # 查数据库, 获取最新提示词对象
        with create_session(self.engine) as session:

            result_obj = self._get_latest_prompt_version(prompt_id,session=session)

            print(result_obj.version,"version")
            prompt = result_obj.prompt
            if result_obj.action_type == "inference":
                # 直接推理即可
                ai_result = self.llm.product(prompt + "\n-----input----\n" +  input_)
                if inference_save_case:
                    self.save_use_case_by_sql(prompt_id,
                                        use_case = input_,
                                        output = ai_result,
                                        solution = "备注/理想回复"
                                        )


            elif result_obj.action_type == "train":
                assert result_obj.demand # 如果type = train 且 demand 是空 则报错
                # 则训练推广

                # 新版本 默人修改会 inference 状态
                chat_history = prompt
                before_input = result_obj.use_case
                demand = result_obj.demand
            

                assert demand
                # 注意, 这里的调整要求使用最初的那个输入, 最好一口气调整好
                chat_history = prompt
                if input_ == before_input: # 输入没变, 说明还是针对同一个输入进行讨论
                    # input_prompt = chat_history + "\nuser:" + demand
                    input_prompt = chat_history + "\nuser:" + demand + output_format 
                else:
                    # input_prompt = chat_history + "\nuser:" + demand + "\n-----input----\n" + input_
                    input_prompt = chat_history + "\nuser:" + demand + output_format  + "\n-----input----\n" + input_
            
                ai_result = self.llm.product(input_prompt)
                chat_history = input_prompt + "\nassistant:\n" + ai_result # 用聊天记录作为完整提示词
                self.save_prompt_by_sql(prompt_id, chat_history,
                                input_data = input_)
                
            elif result_obj.action_type == "summary":

                system_prompt_created_prompt,status_2 = self.get_prompts_from_sql(prompt_id = "intel_summary",version = None)
                assert status_2 == 1

                system_result = self.llm.product(prompt + system_prompt_created_prompt)
                s_prompt = extract_(system_result,pattern_key=r"prompt")
                chat_history = s_prompt or system_result
                self.save_prompt_by_sql(prompt_id, chat_history,
                                input_data = " summary ")
                ai_result = "总结完成"

        return ai_result

    # 异步
    async def aintellect_remove(self,
                    input_data: dict | str,
                    output_format: str,
                    prompt_id: str,
                    version: str = None,
                    inference_save_case = True,
                    ):
        if isinstance(input_data,dict):
            input_ = json.dumps(input_data,ensure_ascii=False)
        elif isinstance(input_data,str):
            input_ = input_data


        # 查数据库, 获取最新提示词对象
        with create_session(self.engine) as session:

            result_obj = self._get_latest_prompt_version(prompt_id,session=session)

            print(result_obj.version,"version")
            prompt = result_obj.prompt
            if result_obj.action_type == "inference":
                # 直接推理即可
                ai_result = await self.llm.aproduct(prompt + "\n-----input----\n" +  input_)
                if inference_save_case:
                    self.save_use_case_by_sql(prompt_id,
                                        use_case = input_,
                                        output = ai_result,
                                        solution = "备注/理想回复"
                                        )
                    
            elif result_obj.action_type == "train":
                assert result_obj.demand # 如果type = train 且 demand 是空 则报错
                # 则训练推广

                # 新版本 默人修改会 inference 状态
                chat_history = prompt
                before_input = result_obj.use_case
                demand = result_obj.demand
            

                assert demand
                # 注意, 这里的调整要求使用最初的那个输入, 最好一口气调整好
                chat_history = prompt
                if input_ == before_input: # 输入没变, 说明还是针对同一个输入进行讨论
                    # input_prompt = chat_history + "\nuser:" + demand
                    input_prompt = chat_history + "\nuser:" + demand + output_format 
                else:
                    # input_prompt = chat_history + "\nuser:" + demand + "\n-----input----\n" + input_
                    input_prompt = chat_history + "\nuser:" + demand + output_format  + "\n-----input----\n" + input_
            
                ai_result = await self.llm.aproduct(input_prompt)
                chat_history = input_prompt + "\nassistant:\n" + ai_result # 用聊天记录作为完整提示词
                self.save_prompt_by_sql(prompt_id, chat_history,
                                input_data = input_)
                
            elif result_obj.action_type == "summary":
                system_prompt_created_prompt,status_2 = self.get_prompts_from_sql(prompt_id = "intel_summary",version = None)
                assert status_2 == 1

                system_result = await self.llm.aproduct(prompt + system_prompt_created_prompt)
                s_prompt = extract_(system_result,pattern_key=r"prompt")
                chat_history = s_prompt or system_result
                self.save_prompt_by_sql(prompt_id, chat_history,
                                input_data = " summary ")
                ai_result = "总结完成"

        return ai_result
    
    # 异步流式
    async def aintellect_stream_remove(self,
                    input_data: dict | str,
                    output_format: str,
                    prompt_id: str,
                    version: str = None,
                    inference_save_case = True,
                    ):
        if isinstance(input_data,dict):
            input_ = json.dumps(input_data,ensure_ascii=False)
        elif isinstance(input_data,str):
            input_ = input_data


        # 查数据库, 获取最新提示词对象
        with create_session(self.engine) as session:

            result_obj = self._get_latest_prompt_version(prompt_id,session=session)

            print(result_obj.version,"version")
            prompt = result_obj.prompt
            if result_obj.action_type == "inference":
                # 直接推理即可
                ai_generate_result = self.llm.aproduct_stream(prompt + "\n-----input----\n" +  input_)

                ai_result = ""
                async for word in ai_generate_result:
                    ai_result += word
                    yield word

                if inference_save_case:
                    self.save_use_case_by_sql(prompt_id,
                                        use_case = input_,
                                        output = ai_result,
                                        solution = "备注/理想回复"
                                        )

            elif result_obj.action_type == "train":
                assert result_obj.demand # 如果type = train 且 demand 是空 则报错
                # 则训练推广

                # 新版本 默人修改会 inference 状态
                chat_history = prompt
                before_input = result_obj.use_case
                demand = result_obj.demand
            

                assert demand
                # 注意, 这里的调整要求使用最初的那个输入, 最好一口气调整好
                chat_history = prompt
                if input_ == before_input: # 输入没变, 说明还是针对同一个输入进行讨论
                    # input_prompt = chat_history + "\nuser:" + demand
                    input_prompt = chat_history + "\nuser:" + demand + output_format 
                else:
                    # input_prompt = chat_history + "\nuser:" + demand + "\n-----input----\n" + input_
                    input_prompt = chat_history + "\nuser:" + demand + output_format  + "\n-----input----\n" + input_
            
                ai_generate_result = self.llm.aproduct_stream(input_prompt)
                ai_result = ""
                async for word in ai_generate_result:
                    ai_result += word
                    yield word

                chat_history = input_prompt + "\nassistant:\n" + ai_result # 用聊天记录作为完整提示词
                self.save_prompt_by_sql(prompt_id, chat_history,
                                input_data = input_)
                
            elif result_obj.action_type == "summary":
                system_prompt_created_prompt,status_2 = self.get_prompts_from_sql(prompt_id = "intel_summary",version = None)
                assert status_2 == 1

                system_result = await self.llm.aproduct(prompt + system_prompt_created_prompt)
                s_prompt = extract_(system_result,pattern_key=r"prompt")
                chat_history = s_prompt or system_result
                self.save_prompt_by_sql(prompt_id, chat_history,
                                input_data = " summary ")
                
                chat_history
                for word in chat_history:
                    yield word



    def prompt_finetune_to_sql(
            self,
            prompt_id:str,
            version = None,
            demand: str = "",
        ):
        """
        让大模型微调已经存在的 system_prompt
        """
        change_by_opinion_prompt = """
你是一个资深AI提示词工程师，具备卓越的Prompt设计与优化能力。
我将为你提供一段现有System Prompt。你的核心任务是基于这段Prompt进行修改，以实现我提出的特定目标和功能需求。
请你绝对严格地遵循以下原则：
 极端最小化修改原则（核心）：
 在满足所有功能需求的前提下，只进行我明确要求的修改。
 即使你认为有更“优化”、“清晰”或“简洁”的表达方式，只要我没有明确要求，也绝不允许进行任何未经指令的修改。
 目的就是尽可能地保留原有Prompt的字符和结构不变，除非我的功能要求必须改变。
 例如，如果我只要求你修改一个词，你就不应该修改整句话的结构。
 严格遵循我的指令：
 你必须精确地执行我提出的所有具体任务和要求。
 绝不允许自行添加任何超出指令范围的说明、角色扮演、约束条件或任何非我指令要求的内容。
 保持原有Prompt的风格和语调：
 尽可能地与现有Prompt的语言风格、正式程度和语调保持一致。
 不要改变不相关的句子或其表达方式。
 只提供修改后的Prompt：
 直接输出修改后的完整System Prompt文本。
 不要包含任何解释、说明或额外对话。
 在你开始之前，请务必确认你已理解并能绝对严格地遵守这些原则。任何未经明确指令的改动都将视为未能完成任务。

现有System Prompt:
{old_system_prompt}

功能需求:
{opinion}
"""

        prompt, _ = self.get_prompts_from_sql(prompt_id = prompt_id,version = version)
        if demand:
            new_prompt = self.llm.product(
                change_by_opinion_prompt.format(old_system_prompt=prompt, opinion=demand)
            )
        else:
            new_prompt = prompt
        self.save_prompt_by_sql(prompt_id = prompt_id,
                            new_prompt = new_prompt,
                            input_data = " ")
        print('success')



############evals##############


class Base_Evals():
    def __init__(self):
        """
        # TODO 2 自动优化prompt 并提升稳定性, 并测试
        通过重写继承来使用它
        """
        self.MIN_SUCCESS_RATE = 00.0 # 这里定义通过阈值, 高于该比例则通过


    def _assert_eval_function(self,params):
        #这里定义函数的评价体系
        print(params,'params')

    def get_success_rate(self,test_cases:list[tuple]):
        """
                # 这里定义数据

        """

        successful_assertions = 0
        total_assertions = len(test_cases)
        failed_cases = []

        for i, params in enumerate(test_cases):
            try:
                # 这里将参数传入
                self._assert_eval_function(params)
                successful_assertions += 1
            except AssertionError as e:
                failed_cases.append(f"Case {i+1} ({params}): FAILED. Expected {params},. Error: {e}")
            except Exception as e: # 捕获其他可能的错误
                failed_cases.append(f"Case {i+1} ({params}): ERROR. Input {params} Error: {e}")
                print(f"Case {i+1} ({params}): ERROR. Error: {e}")

        success_rate = (successful_assertions / total_assertions) * 100
        print(f"\n--- Aggregated Results ---")
        print(f"Total test cases: {total_assertions}")
        print(f"Successful cases: {successful_assertions}")
        print(f"Failed cases count: {len(failed_cases)}")
        print(f"Success Rate: {success_rate:.2f}%")

        assert success_rate >= self.MIN_SUCCESS_RATE, \
            f"Test failed: Success rate {success_rate:.2f}% is below required {self.MIN_SUCCESS_RATE:.2f}%." + \
            f"\nFailed cases details:\n" + "\n".join(failed_cases)

    def get_success_rate_for_auto(self,test_cases:list[tuple]):
        """
                # 这里定义数据

        """

        successful_assertions = 0
        total_assertions = len(test_cases)
        result_cases = []

        for i, params in enumerate(test_cases):
            try:
                # 这里将参数传入
                self._assert_eval_function(params)
                successful_assertions += 1
                result_cases.append({"type":"Successful","params":params,"remark":f"满足要求"})
            except AssertionError as e:
                print(e,'ddd')
                result_cases.append({"type":"FAILED","params":params,"remark":f"ERROR {e}"})
            except Exception as e: # 捕获其他可能的错误
                print(e,'eee')
                result_cases.append({"type":"FAILED","params":params,"remark":f"ERROR {e}"})


        success_rate = (successful_assertions / total_assertions) * 100
        print(f"\n--- Aggregated Results ---")
        print(f"Total test cases: {total_assertions}")
        print(f"Successful cases: {successful_assertions}")
        print(f"Success Rate: {success_rate:.2f}%")

        if success_rate >= self.MIN_SUCCESS_RATE:
            return "pass",result_cases
        else:
            return "nopass",result_cases


    def llm_evals(
        self,
        _input: list[str],
        llm_output: list[str],
        person_output: list[str],
        rule: str,
        pass_if: str,
    ) -> "eval_result-str, eval_reason-str":
        pass
        # result = bx.product(
        #     evals_prompt.format(
        #         评分规则=rule,
        #         输入案例=_input,
        #         大模型生成内容=llm_output,
        #         人类基准=person_output,
        #         通过条件=pass_if,
        #     )
        # )
        # #  eval_result,eval_reason
        # # TODO
        # """
        # "passes": "<是否通过, True or False>",
        # "reason": "<如果不通过, 基于驳回理由>",
        # "suggestions_on_revision": 
        # """
        # result = json.loads(extract_(result,pattern_key=r"json"))
        # return result.get("passes"), result.get("suggestions_on_revision")

    def person_evals(self,params:list,output,real_output):

        print(f"input: ")
        print(params)
        print("=="*20)
        print(f"output: ")
        print(output)
        print("=="*20)
        print(f"real_output: ")
        print(real_output)
        print("=="*20)

        input_ = input("True or False")

        assert input_ == "True"


        # 人类评价

    def rule_evals(self,output,real_output):
        # 规则评价
        assert output == real_output

    def global_evals():
        pass





