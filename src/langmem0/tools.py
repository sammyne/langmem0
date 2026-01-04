from typing import Type

from langchain.tools import ToolRuntime
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field,ConfigDict


# 1. 定义输入参数模型
class MultiplyInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    a: int = Field(description="第一个乘数")
    b: int = Field(description="第二个乘数")
    
    runtime: ToolRuntime
    """ToolRuntime 对象，用于访问工具运行时的上下文信息。
   
    ref: https://forum.langchain.com/t/cannot-access-toolruntime-in-basetool-subclass/2635/2 
    ref: https://forum.langchain.com/t/how-to-access-tool-call-id-using-runtime/2166
    """


# 2. 创建自定义工具类，在 _run 方法中通过 ToolRuntime 获取 store
class ManageMemoryTool(BaseTool):
    name: str = "AdvancedMultiplier"
    description: str = "一个高级的乘法工具，用于精确计算两个整数的乘积。"
    args_schema: Type[BaseModel] = MultiplyInput
    return_direct: bool = False

    def _run(self, a: int, b: int, runtime: ToolRuntime) -> int:
        """同步执行工具的核心逻辑，并访问 store。

        注意：runtime 参数是可选的，由 LangChain 在运行时自动注入。
        用户不需要提供这个参数。
        """

        # print(f'keys = {kwargs.keys()}')
        print(f"runtime = {runtime.__dict__.keys()}")

        return a * b

    async def _arun(self, a: int, b: int, **kwargs) -> int:
        """异步执行逻辑。"""
        # return self._run(a, b, runtime, **kwargs)
        return 0
