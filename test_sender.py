#!/usr/bin/env python
# coding=utf-8
import sys
import socket
import time
import os
import argparse

# 尝试导入 ProgMP API
# 假设 api 文件夹在当前目录或父目录
try:
    from api.progmp import ProgMp
except ImportError:
    # 尝试添加路径
    sys.path.append(os.getcwd())
    try:
        from api.progmp import ProgMp
    except ImportError:
        print("Error: Cannot import api.progmp. Please ensure 'api' folder is available.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='ProgMP mysche Sender')
    parser.add_argument('--target', default='10.0.4.2', help='Target IP (Receiver)')
    parser.add_argument('--port', type=int, default=5001, help='Target Port')
    parser.add_argument('--n', type=int, default=2, help='Number of active subflows (R1)')
    parser.add_argument('--b1', type=int, default=0, help='Min Bandwidth (R2)')
    parser.add_argument('--b2', type=int, default=10000000, help='Max Bandwidth (R3)')
    parser.add_argument('--mode', type=int, default=0, help='Mode: 0=Latency, 1=Bandwidth (R4)')
    parser.add_argument('--scheduler', default='mysche.progmp', help='Path to scheduler file')
    parser.add_argument('--duration', type=int, default=10, help='Sending duration in seconds')
    
    args = parser.parse_args()

    # 1. 读取并加载调度器代码 (System-wide load)
    print("Loading scheduler from %s..." % args.scheduler)
    try:
        with open(args.scheduler, "r") as f:
            sched_code = f.read()
        ProgMp.loadScheduler(sched_code)
    except Exception as e:
        print("Warning: Failed to load scheduler (might be already loaded or permission denied): %s" % e)

    # 2. 创建 Socket 连接
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Connecting to %s:%d..." % (args.target, args.port))
    try:
        s.connect((args.target, args.port))
    except Exception as e:
        print("Connection failed: %s. Ensure receiver is running." % e)
        sys.exit(1)

    # 3. 设置当前 Socket 使用 mysche
    # 获取调度器名称 (从文件内容解析，或者直接假设为 mysche)
    # api.progmp 提供了 getSchedulerName 但我们直接用 "mysche"
    try:
        ProgMp.setScheduler(s, "mysche")
        print("Socket scheduler set to 'mysche'")
    except Exception as e:
        print("Error setting scheduler: %s" % e)

    # 4. 设置寄存器参数
    print("Setting parameters: n=%d, b1=%d, b2=%d, mode=%d" % (args.n, args.b1, args.b2, args.mode))
    try:
        ProgMp.setRegister(s, ProgMp.R1(), args.n)
        ProgMp.setRegister(s, ProgMp.R2(), args.b1)
        ProgMp.setRegister(s, ProgMp.R3(), args.b2)
        ProgMp.setRegister(s, ProgMp.R4(), args.mode)
    except Exception as e:
        print("Error setting registers: %s" % e)

    # 5. 发送数据
    print("Sending data for %d seconds..." % args.duration)
    start_time = time.time()
    data = b'X' * 1024 # 1KB chunk
    bytes_sent = 0
    
    try:
        while time.time() - start_time < args.duration:
            s.send(data)
            bytes_sent += len(data)
    except KeyboardInterrupt:
        print("Interrupted.")
    except Exception as e:
        print("Send error: %s" % e)

    duration = time.time() - start_time
    throughput = (bytes_sent * 8) / duration / 1000000.0 # Mbps
    print("Finished. Sent %.2f MB in %.2f s. Throughput: %.2f Mbps" % (bytes_sent/1024.0/1024.0, duration, throughput))

    s.close()

if __name__ == "__main__":
    main()
