from .通用 import 服务信息
from .消息 import 消息, 消息类型
import asyncio


class 心跳:
    def __init__(self, writer: asyncio.StreamWriter) -> None:
        self.writer = writer
        self.刷新发送()
        self.刷新接收()
        self.心跳消息 = 消息(消息类型.心跳).封包()
        self.任务 = None

    def 启动(self):
        self.任务 = asyncio.create_task(self.循环())

    def 关闭(self):
        if self.任务:
            self.任务.cancel()

    def 刷新发送(self):
        self.发送时间戳 = asyncio.get_running_loop().time()

    def 刷新接收(self):
        self.接收时间戳 = asyncio.get_running_loop().time()

    async def 循环(self):
        while not self.writer.is_closing():
            当前时间 = asyncio.get_running_loop().time()
            if 当前时间 - self.发送时间戳 > 服务信息.心跳时间:
                self.writer.write(self.心跳消息)
                self.刷新发送()
            if 当前时间 - self.接收时间戳 > 服务信息.心跳时间 * 2:
                self.writer.close()
                return
            await asyncio.sleep(0.1)
