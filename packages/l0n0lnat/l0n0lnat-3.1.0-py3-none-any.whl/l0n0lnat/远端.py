import asyncio
from l0n0ltcp.心跳 import 心跳
from l0n0ltcp.TCP转发任务 import 数据转包, 包转数据
from l0n0ltcp.通用 import 服务信息
from l0n0ltcp import 使用uvloop
from .消息 import NAT消息, 消息, NAT消息类型, 获取链接ID, 获取地址类型与端口, 创建链接消息
from .ID生成 import 循环ID生成器
from typing import Dict
from .通用 import NAT信息
import argparse


class NAT服务器:
    ID生成 = 循环ID生成器()

    def __init__(self,  通信writer: asyncio.StreamWriter):
        self.ID = self.__class__.ID生成(nat服务器容器)
        self.通信writer = 通信writer
        self.链接: Dict[int, asyncio.Future] = {}
        self.链接ID生成 = 循环ID生成器()
        self.task = None

    def 关闭(self):
        print('关闭')
        if self.task:
            self.task.cancel()

    def 启动(self, 端口: int, iptype: int):
        self.监听地址 = '0.0.0.0' if iptype == 4 else '::'
        self.端口 = 端口
        self.task = asyncio.create_task(self._启动())

    async def _启动(self):
        server = await asyncio.start_server(self.被连接, self.监听地址, self.端口)
        print('开始监听', (self.监听地址, self.端口))
        async with server:
            await server.serve_forever()

    async def 被连接(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        链接ID = self.链接ID生成()
        self.通信writer.write(创建链接消息(self.ID, 链接ID).封包())
        await self.通信writer.drain()
        future = asyncio.get_running_loop().create_future()
        self.链接[链接ID] = future
        本地reader, 本地writer = await future
        print('nat连通')
        _心跳 = 心跳(本地writer)
        done, pending = await asyncio.wait([
            asyncio.create_task(数据转包(reader, 本地writer, _心跳)),
            asyncio.create_task(包转数据(本地reader, writer, _心跳)),
            asyncio.create_task(_心跳.循环())],
            return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        writer.close()
        本地writer.close()

    def 链接完成(self, 链接ID: int, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        future = self.链接.get(链接ID)
        if not future:
            self.关闭()
            writer.close()
            return
        future.set_result((reader, writer))


nat服务器容器: Dict[int, NAT服务器] = {}


async def 本地客户端连接到了(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    _心跳 = 心跳(writer)

    async def 读取任务():
        需要接收消息 = True
        try:
            while not writer.is_closing():
                if 需要接收消息:
                    try:
                        msg = await 消息.读一个消息(reader)
                    except:
                        break
                    _心跳.刷新接收()
                    if msg.类型 == NAT消息类型.NAT:
                        端口, iptype = 获取地址类型与端口(msg)
                        natServer = NAT服务器(writer)
                        natServer.启动(端口, iptype)
                        nat服务器容器[natServer.ID] = natServer
                    elif msg.类型 == NAT消息类型.链接完成:
                        服务器ID, 链接ID = 获取链接ID(msg)
                        natServer = nat服务器容器.get(服务器ID)
                        if natServer is None:
                            return
                        natServer.链接完成(链接ID, reader, writer)
                        需要接收消息 = False
                else:
                    await asyncio.sleep(0.1)
        finally:
            writer.close()
            print('客户端断开')
            try:
                if 需要接收消息:
                    natServer.关闭()  # type: ignore
            except:
                pass
    done, pending = await asyncio.wait([
        asyncio.create_task(读取任务()),
        asyncio.create_task(_心跳.循环())],
        return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    writer.close()


async def 启动通信服务器():
    server = await asyncio.start_server(本地客户端连接到了, 服务信息.监听地址, 服务信息.监听端口)
    async with server:
        await server.serve_forever()


def 读取参数(功能):
    parser = argparse.ArgumentParser(description=功能)
    parser.add_argument("监听地址", help="服务器监听地址")
    parser.add_argument("监听端口", type=int, help="服务器监听端口")
    parser.add_argument("密码", help="通信密码")
    args = parser.parse_args()
    # 假设 服务信息 是一个全局对象
    服务信息.监听地址 = args.监听地址
    服务信息.监听端口 = args.监听端口
    服务信息.密码 = args.密码


def main():
    读取参数('启动nat客户端')
    使用uvloop()
    try:
        asyncio.run(启动通信服务器())
    except Exception as e:
        print(e)
        
