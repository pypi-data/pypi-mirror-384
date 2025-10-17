import asyncio
from .心跳 import 心跳
from .TCP转发任务 import 数据转包, 包转数据
from .通用 import 服务信息, 使用uvloop, 读取参数


async def 当有新链接接入(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        clientReader, clientWriter = await asyncio.open_connection(服务信息.服务地址, 服务信息.服务端口)
    except:
        print('连接服务器失败!')
        return
    _心跳 = 心跳(clientWriter)
    done, pending = await asyncio.wait([
        asyncio.create_task(数据转包(reader, clientWriter, _心跳)),
        asyncio.create_task(包转数据(clientReader, writer, _心跳)),
        asyncio.create_task(_心跳.循环())],
        return_when=asyncio.FIRST_COMPLETED)
    writer.close()
    clientWriter.close()
    for task in pending:
        task.cancel()


async def main():
    读取参数('启动TCP加密转发客户端')
    server = await asyncio.start_server(当有新链接接入, 服务信息.监听地址, 服务信息.监听端口)
    async with server:
        await server.serve_forever()


def start():
    try:
        使用uvloop()
        asyncio.run(main())
    except:
        print('关闭')
