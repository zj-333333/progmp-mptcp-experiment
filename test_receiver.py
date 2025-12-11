#!/usr/bin/env python
# coding=utf-8
import socket
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5001)
    args = parser.parse_args()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', args.port))
    s.listen(1)
    print("Receiver listening on port %d..." % args.port)

    conn, addr = s.accept()
    print("Accepted connection from %s" % str(addr))

    total_bytes = 0
    try:
        while True:
            data = conn.recv(1024*1024)
            if not data:
                break
            total_bytes += len(data)
    except Exception as e:
        print("Error: %s" % e)
    
    print("Connection closed. Received %d bytes." % total_bytes)
    conn.close()
    s.close()

if __name__ == "__main__":
    main()
