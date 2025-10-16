from l0n0ltcp import 消息
import struct


class NAT消息类型:
    NAT = 2
    创建链接 = 3
    链接完成 = 4


def NAT消息(端口: int, iptype: int = 4):
    return 消息(NAT消息类型.NAT, struct.pack('!II',  端口, iptype))


def 获取地址类型与端口(msg: 消息):
    return struct.unpack('!II', msg.数据)


def 创建链接消息(服务器器ID: int, 链接ID: int):
    return 消息(NAT消息类型.创建链接, struct.pack('!II',  服务器器ID, 链接ID))


def 链接完成消息(服务器器ID: int, 链接ID: int):
    return 消息(NAT消息类型.链接完成, struct.pack('!II',  服务器器ID, 链接ID))


def 获取链接ID(msg: 消息):
    return struct.unpack('!II', msg.数据)
