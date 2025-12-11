#coding=utf-8
#!/usr/bin/env python
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.link import Link, TCLink,Intf
from subprocess import Popen, PIPE
from mininet.log import setLogLevel
import os
import select
import socket
import sys
import time

def setup_scheduler_server():
    """创建一个服务器来监听调度器变更请求"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 绑定到所有可用接口，而不是只绑定到localhost
    server.bind(('0.0.0.0', 12345))
    server.listen(1)
    server.setblocking(0)  # 设置为非阻塞
    return server

def handle_scheduler_request(server):
    """处理调度器更改请求"""
    try:
        client, _ = server.accept()
        data = client.recv(1024).decode()
        if data.startswith('scheduler:'):
            scheduler = data.split(':')[1]
            os.system("sysctl -w net.mptcp.mptcp_scheduler=%s" % scheduler)
            print("Changed scheduler to: %s" % scheduler)
        client.close()
    except socket.error:
        pass

if '__main__' == __name__:
    setLogLevel('info')
    net = Mininet(link=TCLink)
    key = "net.mptcp.mptcp_enabled"
    value = 1
    p = Popen("sysctl -w %s=%s" % (key, value), shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    print "stdout=",stdout,"stderr=", stderr

    # 创建主机和路由器
    h1 = net.addHost('h1')
    h2 = net.addHost('h2')
    r1 = net.addHost('r1')
    
    # 链路配置
    linkopt={'bw':10}
    
    # 添加链路
    for _ in range(4):
        net.addLink(h1, r1, cls=TCLink, **linkopt)
    for _ in range(4):
        net.addLink(h2, r1, cls=TCLink, **linkopt)
    
    net.build()
    
    # 等待网络接口准备就绪
    time.sleep(1)
    
    # 清除所有接口的IP配置
    for i in range(4):
        h1.cmd("ifconfig h1-eth%d 0" % i)
        h2.cmd("ifconfig h2-eth%d 0" % i)
    
    for i in range(8):
        r1.cmd("ifconfig r1-eth%d 0" % i)
    
    # 启用路由器的IP转发
    r1.cmd("echo 1 > /proc/sys/net/ipv4/ip_forward")
    
    # 配置路由器接口
    for i in range(4):
        r1.cmd("ifconfig r1-eth%d 10.0.%d.1 netmask 255.255.255.0" % (i, i))      # 连接h1
        r1.cmd("ifconfig r1-eth%d 10.0.%d.1 netmask 255.255.255.0" % (i+4, i+4))  # 连接h2
    
    # 配置主机接口
    for i in range(4):
        h1.cmd("ifconfig h1-eth%d 10.0.%d.2 netmask 255.255.255.0" % (i, i))
        h2.cmd("ifconfig h2-eth%d 10.0.%d.2 netmask 255.255.255.0" % (i, i+4))
    
    # 配置h1的路由表
    for i in range(4):
        h1.cmd("ip rule add from 10.0.%d.2 table %d" % (i, i+1))
        h1.cmd("ip route add 10.0.%d.0/24 dev h1-eth%d scope link table %d" % (i, i, i+1))
        h1.cmd("ip route add default via 10.0.%d.1 dev h1-eth%d table %d" % (i, i, i+1))
    
    # 配置h2的路由表
    for i in range(4):
        h2.cmd("ip rule add from 10.0.%d.2 table %d" % (i+4, i+1))
        h2.cmd("ip route add 10.0.%d.0/24 dev h2-eth%d scope link table %d" % (i+4, i, i+1))
        h2.cmd("ip route add default via 10.0.%d.1 dev h2-eth%d table %d" % (i+4, i, i+1))
    
    # 配置默认路由
    h1.cmd("ip route add default scope global nexthop via 10.0.0.1 dev h1-eth0")
    h2.cmd("ip route add default scope global nexthop via 10.0.4.1 dev h2-eth0")
    
    # 在配置网络之后，添加NAT规则
    r1.cmd("iptables -t nat -A POSTROUTING -o r1-eth0 -j MASQUERADE")
    r1.cmd("iptables -A FORWARD -i r1-eth0 -o r1-eth4 -j ACCEPT")
    r1.cmd("iptables -A FORWARD -i r1-eth4 -o r1-eth0 -j ACCEPT")
    
    # 在宿主机上添加到h1的路由
    os.system("ip route add 10.0.0.0/24 via 10.0.0.1")
    
    # 添加防火墙规则
    os.system("iptables -A INPUT -p tcp --dport 12345 -j ACCEPT")
    
    # 设置调度器服务器
    server = setup_scheduler_server()
    
    # 创建一个后台线程来处理调度器请求
    import threading
    def server_thread():
        cmd_file = '/tmp/mptcp_cmd'
        if not os.path.exists(cmd_file):
            os.mkfifo(cmd_file)
            
        while True:
            try:
                with open(cmd_file, 'r') as f:
                    data = f.readline().strip()
                    if data.startswith('scheduler:'):
                        scheduler = data.split(':')[1]
                        os.system("sysctl -w net.mptcp.mptcp_scheduler=%s" % scheduler)
                        print("Changed scheduler to: %s" % scheduler)
            except Exception as e:
                print("Server error:", e)
                time.sleep(0.1)
    
    thread = threading.Thread(target=server_thread)
    thread.daemon = True
    thread.start()
    
    # 使用标准的Mininet CLI
    CLI(net)
    
    # 清理
    server.close()
    net.stop()
