from l0n0ltcp.TCP转发服务器 import main
from l0n0ltcp.通用 import 服务信息
import asyncio
服务信息.监听端口 = 11224
服务信息.服务端口 = 8888

asyncio.run(main())