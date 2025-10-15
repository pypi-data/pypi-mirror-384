# 定义model
from pydantic import BaseModel


#
class InstructionRequestBase(BaseModel):
    # 时间
    event_time: int
    # 任务id
    task_id: str
    # 指令id
    instruction_id: str


class InstructionResponseBase(BaseModel):
    # 时间
    event_time: int
