import asyncio
from .通用 import chacha20单例
from .消息 import 消息, 消息类型
from .心跳 import 心跳


async def 包转数据(包reader: asyncio.StreamReader, writer: asyncio.StreamWriter, _心跳: 心跳):
    try:
        while not writer.is_closing():
            新消息 = await 消息.读一个消息(包reader)
            _心跳.刷新接收()
            if 新消息.类型 == 消息类型.数据:
                writer.write(chacha20单例.加解密(新消息.数据))
    except Exception as e:
        pass


async def 数据转包(数据reader: asyncio.StreamReader, 包writer: asyncio.StreamWriter, _心跳: 心跳):
    try:
        while not 包writer.is_closing():
            data = await 数据reader.read(4096)
            if not data:
                return
            msg = 消息(消息类型.数据, chacha20单例.加解密(data))
            包writer.write(msg.封包())
            _心跳.刷新发送()
    except Exception as e:
        pass