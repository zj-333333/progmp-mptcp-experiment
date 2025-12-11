#!/usr/bin/env python
# coding=utf-8
import os
import time
import sys
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from subprocess import Popen, PIPE

def setup_network():
    net = Mininet(link=TCLink)
    
    # 启用 MPTCP
    os.system("sysctl -w net.mptcp.mptcp_enabled=1")

    # 创建节点
    h1 = net.addHost('h1')
    h2 = net.addHost('h2')
    r1 = net.addHost('r1')
    
    # 链路配置 (带宽 10Mbps)
    linkopt = {'bw': 10}
    
    # h1 <-> r1 (4 links)
    for _ in range(4):
        net.addLink(h1, r1, cls=TCLink, **linkopt)
        
    # h2 <-> r1 (4 links)
    for _ in range(4):
        net.addLink(h2, r1, cls=TCLink, **linkopt)
    
    net.build()
    
    # 配置 IP 和 路由 (参考 mptcp-topo1.py)
    # 此处简化逻辑，直接调用 ifconfig 和 ip route
    
    # 1. 清除旧配置
    for i in range(4):
        h1.cmd("ifconfig h1-eth%d 0" % i)
        h2.cmd("ifconfig h2-eth%d 0" % i)
    for i in range(8):
        r1.cmd("ifconfig r1-eth%d 0" % i)
        
    # 2. Router IP
    r1.cmd("echo 1 > /proc/sys/net/ipv4/ip_forward")
    for i in range(4):
        # h1 side: 10.0.0.1, 10.0.1.1, ...
        r1.cmd("ifconfig r1-eth%d 10.0.%d.1 netmask 255.255.255.0" % (i, i))
        # h2 side: 10.0.4.1, 10.0.5.1, ... (Offset by 4)
        r1.cmd("ifconfig r1-eth%d 10.0.%d.1 netmask 255.255.255.0" % (i+4, i+4))

    # 3. Host IP & Policy Routing
    # h1
    for i in range(4):
        h1.cmd("ifconfig h1-eth%d 10.0.%d.2 netmask 255.255.255.0" % (i, i))
        h1.cmd("ip rule add from 10.0.%d.2 table %d" % (i, i+1))
        h1.cmd("ip route add 10.0.%d.0/24 dev h1-eth%d scope link table %d" % (i, i, i+1))
        h1.cmd("ip route add default via 10.0.%d.1 dev h1-eth%d table %d" % (i, i, i+1))
    h1.cmd("ip route add default scope global nexthop via 10.0.0.1 dev h1-eth0")
    
    # h2
    for i in range(4):
        h2.cmd("ifconfig h2-eth%d 10.0.%d.2 netmask 255.255.255.0" % (i, i+4))
        h2.cmd("ip rule add from 10.0.%d.2 table %d" % (i+4, i+1))
        h2.cmd("ip route add 10.0.%d.0/24 dev h2-eth%d scope link table %d" % (i+4, i, i+1))
        h2.cmd("ip route add default via 10.0.%d.1 dev h2-eth%d table %d" % (i+4, i, i+1))
    h2.cmd("ip route add default scope global nexthop via 10.0.4.1 dev h2-eth0")

    # 4. NAT/Routing fix (needed for return path?)
    # mptcp-topo1.py uses MASQUERADE on r1-eth0? 
    # Let's assume the routing tables above are sufficient for end-to-end connectivity
    # if both use MPTCP.
    
    return net

def run_experiment(net, mode, n, b1, b2):
    h1 = net.get('h1')
    h2 = net.get('h2')
    
    info('*** Starting Receiver on h2\n')
    # Start receiver in background
    h2.cmd('python test_receiver.py --port 5001 > receiver.log 2>&1 &')
    
    time.sleep(1)
    
    info('*** Starting Sender on h1 (Mode=%d, n=%d)\n' % (mode, n))
    # Run sender
    cmd = "python test_sender.py --target 10.0.4.2 --port 5001 --mode %d --n %d --b1 %d --b2 %d --duration 5" % (mode, n, b1, b2)
    result = h1.cmd(cmd)
    print(result)
    
    info('*** Experiment Finished\n')

if __name__ == '__main__':
    setLogLevel('info')
    
    # Parse args for flexibility
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=int, default=0)
    parser.add_argument('--n', type=int, default=2)
    parser.add_argument('--b1', type=int, default=0)
    parser.add_argument('--b2', type=int, default=10000000)
    args = parser.parse_args()
    
    try:
        net = setup_network()
        # Ensure we are in the right directory for scripts
        # We assume scripts are in current dir
        
        run_experiment(net, args.mode, args.n, args.b1, args.b2)
        
    finally:
        if 'net' in locals():
            net.stop()
            os.system("mn -c") # Clean up
