# 功能: 内网穿透服务器与客户端

# 1. 安装
```bash
pip install l0n0lnat
```
# 2. 服务器命令
```bash
l0n0lnatserver -h
usage: l0n0lnatserver [-h] 监听地址 监听端口 密码

启动nat客户端

positional arguments:
  监听地址        服务器监听地址
  监听端口        服务器监听端口
  密码          通信密码

options:
  -h, --help  show this help message and exit
```

# 3. 客户端命令
```bash
l0n0lnatclient -h
usage: l0n0lnatclient [-h] [-6] 服务器地址 服务器端口 远端监听端口 被穿透的服务地址 被穿透的服务端口 密码

启动nat客户端

positional arguments:
  服务器地址           远程服务器地址
  服务器端口           远程服务器端口
  远端监听端口          远端监听端口
  被穿透的服务地址        被穿透的服务地址
  被穿透的服务端口        被穿透的服务端口
  密码              通信密码

options:
  -h, --help      show this help message and exit
  -6, --use-ipv6  启用 IPv6

```
# 4. 实例
* 被穿透服务: `A(192.168.1.2:80)`
* 服务器: `B(192.168.1.3)`

## 4.1 在`B`上执行
```bash
l0n0lnatserver 0.0.0.0 11223 123
```

## 4.2 在`A`上执行
```bash
l0n0lnatclient 192.168.1.3 11223 8888 127.0.0.1 80 123
```

## 4.3 访问`B:8888`
```bash
curl http://192.168.1.3:8888
```



