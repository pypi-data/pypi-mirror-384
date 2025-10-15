# from db_help.mysql import MySQLManagerWithVersionControler
from db_help.qdrant import QdrantManager
from pydantic import BaseModel
from datetime import datetime
from prompt_writing_assistant.utils import get_adler32_hash, embedding_inputs
from prompt_writing_assistant.prompt_helper import Intel, IntellectType
from prompt_writing_assistant.utils import extract_
from enum import Enum
import json

from prompt_writing_assistant.database import Base, Prompt
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from prompt_writing_assistant.utils import create_session
from prompt_writing_assistant.database import Content

import os
intel = Intel(database_url = os.getenv("database_url"))
        
class TextType(Enum):
    Code = 0
    Prompt = 1
    Tips = 2
    Experience = 3

class ContentManager():
    def __init__(self):
        """
        """
        self.table_name = "content"
        self.qdrant = QdrantManager(host = "localhost")
        self.neo = None

    
    @intel.intellect_2(IntellectType.inference,
                    prompt_id = "db_help_001",
                    demand="""
name 后面加一个4位随机数字防止重复
    """)
    def diverter(self,input:dict):
        # 根据需求修改程序框图
        input = json.loads(extract_(input,pattern_key=r"json"))

        class Output(BaseModel):
            name : str
            type : int
            note : str

        Output(**input)
        return input


    def save_content_auto(self,text:str):
        
        output = self.diverter(input = {"text":text})
        print(output,'output')
        self.save_content(text = text,
                          name = output.get("name"),
                          type = output.get("type"),
                          )



    def save_content(self,text:str,name:str,type:int | TextType)->str:
        # 数据库维护版本, 而向量库只保持最新

        # 1 存入到数据库中
        embed_name_id = get_adler32_hash(name)

        vector_list = embedding_inputs([text])
        if isinstance(type,TextType):
            type = type.value

        with create_session(intel.engine) as session:
            cont = Content(name = name,
                    embed_name_id = embed_name_id,
                    timestamp = datetime.now(),
                    content = text,
                    type = type,
                    )
            session.add(cont)
            session.commit() # 提交事务，将数据写入数据库

        # 2 存入到qdrant中
        self.qdrant.update(self.table_name,
                           data_list =[
                               {
                                "id":embed_name_id,
                                "vector":vector_list[0],
                                "payload":{
                                    "name": name, 
                                    'timestamp': datetime.now(),
                                    "content": text,
                                    "type":type}
                                }
                           ])
        
        
        # 考虑使用知识图 + 增加因果联系

    def save_to(self):
        #TODO 尝试另存为
        pass

    def search(self,name:str,version = None):
        with create_session(intel.engine) as session:
            target_content = session.query(Content).filter_by(name = name,
                                             version = version).frist()
        result = target_content.content
        return result
    
    def similarity(self,content: str,limit: int =2):
        vector = embedding_inputs([content])[0]
        result = self.qdrant.select_by_vector(query_vector = vector,
                                collection_name = self.table_name,
                                limit = limit)
        return result
    
