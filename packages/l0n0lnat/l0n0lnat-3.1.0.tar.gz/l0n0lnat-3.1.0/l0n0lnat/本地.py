import asyncio
import argparse
from l0n0ltcp.心跳 import 心跳
from l0n0ltcp.TCP转发任务 import 数据转包, 包转数据
from l0n0ltcp.通用 import 服务信息
from .消息 import 链接完成消息, NAT消息, 消息, NAT消息类型, 获取链接ID
from .通用 import NAT信息
from l0n0ltcp import 使用uvloop


async def 启动转发客户端(服务器ID: int, 链接ID: int):
    服务器reader, 服务器writer = await asyncio.open_connection(服务信息.服务地址, 服务信息.服务端口)
    本地reader, 本地writer = await asyncio.open_connection(NAT信息.被穿透的服务地址, NAT信息.被穿透的服务端口)
    服务器writer.write(链接完成消息(服务器ID, 链接ID).封包())
    await 服务器writer.drain()
    _心跳 = 心跳(服务器writer)
    done, pending = await asyncio.wait([
        asyncio.create_task(数据转包(本地reader, 服务器writer, _心跳)),
        asyncio.create_task(包转数据(服务器reader, 本地writer, _心跳)),
        asyncio.create_task(_心跳.循环())],
        return_when=asyncio.FIRST_COMPLETED)
    服务器writer.close()
    本地writer.close()
    for task in pending:
        task.cancel()


async def 启动通信客户端():
    while True:
        try:
            print('正在连接服务器...')
            服务器reader, 服务器writer = await asyncio.open_connection(服务信息.服务地址, 服务信息.服务端口)
            print('连接成功')
            服务器writer.write(NAT消息(NAT信息.远端监听端口, NAT信息.远端监听地址类型).封包())
            监听地址 = '0.0.0.0' if NAT信息.远端监听地址类型 == 4 else '::'
            print(f'发送监听{监听地址}:{NAT信息.远端监听端口}命令')
            await 服务器writer.drain()
            _心跳 = 心跳(服务器writer)

            async def 读取任务():
                while not 服务器writer.is_closing():
                    msg = await 消息.读一个消息(服务器reader)
                    _心跳.刷新接收()
                    if msg.类型 == NAT消息类型.创建链接:
                        服务器ID, 链接ID = 获取链接ID(msg)
                        asyncio.create_task(启动转发客户端(服务器ID, 链接ID))
                        
            done, pending = await asyncio.wait([
                asyncio.create_task(读取任务()),
                asyncio.create_task(_心跳.循环())],
                return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            服务器writer.close()
            print('服务器链接断开!')
        except KeyboardInterrupt:
            return


def 读取参数(功能):
    parser = argparse.ArgumentParser(description=功能)
    parser.add_argument("服务器地址", help="远程服务器地址")
    parser.add_argument("服务器端口", type=int, help="远程服务器端口")
    parser.add_argument("远端监听端口", type=int, help="远端监听端口")
    parser.add_argument("被穿透的服务地址", help="被穿透的服务地址")
    parser.add_argument("被穿透的服务端口", help="被穿透的服务端口")
    parser.add_argument("密码", help="通信密码")
    parser.add_argument("-6", "--use-ipv6",
                        action="store_true", help="启用 IPv6")

    args = parser.parse_args()
    # 假设 服务信息 是一个全局对象
    服务信息.服务地址 = args.服务器地址
    服务信息.服务端口 = args.服务器端口
    服务信息.密码 = args.密码
    NAT信息.被穿透的服务地址 = args.被穿透的服务地址
    NAT信息.被穿透的服务端口 = args.被穿透的服务端口
    NAT信息.远端监听端口 = args.远端监听端口
    NAT信息.远端监听地址类型 = 6 if args.use_ipv6 else 4


def main():
    读取参数('启动nat客户端')
    使用uvloop()
    asyncio.run(启动通信客户端())
