from pydantic import BaseModel,Field
from typing import Literal



class KeyChoice(BaseModel):
    data:Literal['key1','key2'] = Field(...,description='使用的秘钥,key1 or key2') # Field(...,description='使用的秘钥,key1 or key2')
