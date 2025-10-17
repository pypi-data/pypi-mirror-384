import struct
import asyncio


class 消息类型:
    数据 = 0
    心跳 = 1


class 消息:
    消息头格式 = '!BI'
    消息头大小 = struct.calcsize(消息头格式)

    def __init__(self, 类型: int, 数据: bytes = b'') -> None:
        self.类型 = 类型
        self.数据 = 数据

    def 封包(self):
        return struct.pack(self.消息头格式, self.类型, len(self.数据)) + self.数据

    @classmethod
    async def 读一个消息(cls, reader: asyncio.StreamReader):
        头部数据 = await reader.readexactly(cls.消息头大小)
        类型, 长度 = struct.unpack(cls.消息头格式, 头部数据)
        if 长度 > 0:
            数据 = await reader.readexactly(长度)
        else:
            数据 = b''
        return 消息(类型, 数据)
