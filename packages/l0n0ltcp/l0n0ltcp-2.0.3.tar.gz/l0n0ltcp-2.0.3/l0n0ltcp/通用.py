from .ChaCha20 import ChaCha20
import argparse


class 转发服务器身份:
    客户端 = 0
    服务器 = 1


class 服务信息:
    监听地址 = '0.0.0.0'
    监听端口 = 11223
    服务地址 = '127.0.0.1'
    服务端口 = 11224
    身份 = 转发服务器身份.客户端
    密码 = '123'
    心跳时间 = 1.0


def 读取参数(功能):
    parser = argparse.ArgumentParser(description=功能)
    parser.add_argument("监听地址", help="本地监听地址")
    parser.add_argument("监听端口", type=int, help="本地监听端口")
    parser.add_argument("服务器地址", help="远程服务器地址")
    parser.add_argument("服务器端口", type=int, help="远程服务器端口")
    parser.add_argument("密码", help="通信密码")
    args = parser.parse_args()

    服务信息.监听地址 = args.监听地址
    服务信息.监听端口 = args.监听端口
    服务信息.服务地址 = args.服务器地址
    服务信息.服务端口 = args.服务器端口
    服务信息.密码 = args.密码


def 使用uvloop():
    try:
        import uvloop  # type: ignore
        uvloop.install()
        print('正在使用uvloop')
    except:
        pass


class chacha20单例:
    chacha20 = None

    @classmethod
    def 加解密(cls, data):
        if cls.chacha20 is None:
            cls.chacha20 = ChaCha20(服务信息.密码)
        return cls.chacha20(data)
