import pytest
from prompt_writing_assistant.code_helper.coder import Paper, ProgramChart
from prompt_writing_assistant.code_helper.coder import CoderHelper
from dotenv import load_dotenv
load_dotenv(".env", override=True)

def test_min_edit():
    x = CoderHelper().min_edit("print(hello world)","写成中文")
    print(x)


def test_free_function():
    """
    result2 = highly_flexible_function(x="帮我计算 1加1")
    print(f"示例2 执行结果: {result2}")

    """
    x = CoderHelper().free_function(
        function="帮我将 日期 2025/12/03 向前回退12天", 
        data_str="2025/12/03", 
        days=12)
    print(x,"result->")

def test_free_function_advanced():
    return "1234"





def test_draw_paper():
    """
    在一个固定画板上编辑文本
    """
    content = """我在凉山州做项目期间，曾替客户背过一次“黑锅”。那次是我们接处警的项目刚刚上线，因为项目是在凉山州做的，所以我们在西昌市驻扎。当地有两个公安局，一个是州公安局，一个是市公安局。上线当天，我们原定在州公安局开新闻发布会，市公安局这边会同步进行。但就在当天早上，我被客户叫到了市公安局，本该去参加发布会的我被临时调动。客户告诉我，市公安局的大领导、局长可能会来问些问题，让我再去给他讲讲我们的系统。于是我直接去了市公安局，没有去参加发布会。\n\n当时叫我去的是客户那边的对接人，一位指挥长。在他们开新闻发布会的时候，我们就在后面聊天，并给他讲一些系统的事情，因为我们关系都比较熟了。发布会结束后，公安局的局长说要让我调一份接警的录音出来。这事儿是因为他们下面有一个派出所警员在接警过程中，对接警员的态度不好，局长比较生气，说要调出证据去处罚他，认为他既然对自己的同志态度都不好，那对待民众的态度肯定会更不好。他只要那份录音文件，让我从我们的系统里导出来。\n\n局长要在他们全市的公安局领导面前播放这份录音，但是他们播放的设备不能直接登录我们的系统，所以我需要把录音文件导出来，再插到他们播放的电脑上去播放。我找到U盘后，因为我在那块待的时间比较长，比较熟，就想把音频文件直接导到他们的电脑上，然后播放出来。"""
    pp = Paper(content)
    pp.talk(' 帮我将上面文字中关于u盘的内容删除')
    print(pp.content)

def test_paper():
    
    # 在一张白纸上作画
    pp = Paper("你好 世界")
    x = pp.talk('你好')
    print(x)







#############
# 1 编写自动化构建web服务
# 2 编写自动化构建框架服务
# 3 编写自动化实现低难度框架
# 4 


#############


from prompt_writing_assistant.utils import super_print
from prompt_writing_assistant.code_helper.web import edit_server
from prompt_writing_assistant.code_helper.web import gener_post_server,gener_post_server_multi,gener_get_server

import pytest


# 格式输出不稳定

def test_edit_server():
    """
    1 uv run python -m temp_web # 搭建起虚拟服务
    2 运行, 写入服务更新, 然后获得curl 命令, 验证是否通行

    优势是: 结合了本地化, 可以同步的测试服务是否可用, 同时生成curl 命令
    缺点是: 冗长, 繁琐, 单一操作
    """
    # uv run python -m temp_web
    ask = '''
# 记忆合并
class Memory_card_list_Request(BaseModel):
    memory_cards: list[str] = Field(..., description="要评分的记忆卡片内容")

@app.post("/memory_card/merge")
async def memory_card_merge_server(request: Memory_card_list_Request):
    """
    记忆卡片质量评分
    接收一个记忆卡片内容字符串，并返回其质量评分。
    """
    result = memory_card_merge(memory_cards=request.memory_cards)
    return {
        "message": "memory card merge successfully",
        "result": result
    }

帮我修改为post方法
'''
    
    out_curl = edit_server(ask,output_py = 'temp_web.py')
    super_print(out_curl,"test_edit_server_curl")




def test_get_server():
    """
    自动生成get 方法

    优点: 可控性强, 靠模板制定函数
    缺点: 人类介入程度高, 单一操作
    """
    code = '''
    def brief(self,memory_cards:list[str])->str:
        """
        数字分身介绍
        """
        return {"title":"我的数字分身标题","content":"我的数字分身简介"}
    '''
    result = gener_get_server(prompt=code)
    super_print(result,'gener_get_server')



def test_post_server():
    """
    自动生成get 方法

    优点: 可控性强, 靠模板制定函数
    缺点: 人类介入程度高, 单一操作
    """
    code = '''
    def brief(self,memory_cards:list[str])->str:
        """
        数字分身介绍
        """
        return {"title":"我的数字分身标题","content":"我的数字分身简介"}
    '''
    result = gener_post_server(prompt=code)
    super_print(result,'post_server')



def test_post_server_multi():
    """
    自动生成get 方法

    优点: 可控性强, 靠模板制定函数, 多数操作, 有格式监控
    缺点: 人类介入程度高
    """
    code = '''
class Memo():
    def __init__(self):
        """
        初始化
        """
        
    def build_from_datas(datas:dict)->None:
        """
        构建数据
        """
        
    def get_info_from_tree(self, prompt:str)-> str:
        """
        获取信息
        """
        
    def eval_(self)-> str:
        """
        这是一个长时间运行的同步操作
        """
        
    async def aeval_(self)-> str:
        """
        这是一个长时间运行的异步操作, 作用同eval_
        """
        
    def get_eval(self)-> str:
        """
        获取eval 的执行结果
        """
    '''
    result = gener_post_server_multi(prompt=code)
    super_print(result,'post_server')


