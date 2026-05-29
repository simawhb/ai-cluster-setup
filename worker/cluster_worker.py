#!/usr/bin/env python3
"""AI集群Worker - 自动发现Master并注册"""

import os
import sys
import json
import socket
import subprocess
import threading
import time
from pathlib import Path

# 常量
BROADCAST_PORT = 50053
RPC_PORT = 50051
VERSION = "1.0.0"


class ClusterWorker:
    def __init__(self):
        self.master_ip = None
        self.master_port = RPC_PORT
        self.local_ip = self.get_local_ip()
        self.is_running = False
        self.rpc_process = None
        self.hostname = socket.gethostname()

    def get_local_ip(self):
        """获取本机IP"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def discover_master(self):
        """自动发现Master节点"""
        print(f"[发现] 正在搜索Master节点...")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', BROADCAST_PORT))
        sock.settimeout(60)

        while self.is_running and not self.master_ip:
            try:
                data, addr = sock.recvfrom(1024)
                message = json.loads(data.decode())

                if message.get("type") == "master_announce":
                    self.master_ip = message.get("ip", addr[0])
                    self.master_port = message.get("port", RPC_PORT)
                    print(f"[发现] 找到Master: {self.master_ip}:{self.master_port}")
                    break
            except socket.timeout:
                print("[超时] 未发现Master，继续等待...")
            except Exception as e:
                print(f"[错误] {e}")

        sock.close()
        return self.master_ip is not None

    def register_with_master(self):
        """向Master注册"""
        if not self.master_ip:
            return False

        print(f"[注册] 向Master注册...")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        message = json.dumps({
            "type": "worker_register",
            "ip": self.local_ip,
            "name": self.hostname,
            "port": RPC_PORT,
            "timestamp": time.time()
        }).encode()

        try:
            sock.sendto(message, ('<broadcast>', BROADCAST_PORT))
            print(f"[注册] 注册成功: {self.hostname} ({self.local_ip})")
            return True
        except Exception as e:
            print(f"[错误] 注册失败: {e}")
            return False
        finally:
            sock.close()

    def start_rpc_server(self):
        """启动RPC服务器"""
        rpc_path = Path(__file__).parent.parent / "bin" / "rpc-server.exe"
        if not rpc_path.exists():
            print(f"[错误] RPC服务器不存在: {rpc_path}")
            print(f"[提示] 请从 https://github.com/ggerganov/llama.cpp/releases 下载")
            return False

        try:
            self.rpc_process = subprocess.Popen(
                [str(rpc_path), "-H", "0.0.0.0", "-p", str(RPC_PORT), "-c"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print(f"[启动] RPC服务器 - 端口 {RPC_PORT}")
            return True
        except Exception as e:
            print(f"[错误] 启动RPC服务器失败: {e}")
            return False

    def keep_alive(self):
        """保持注册状态"""
        def alive_loop():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            while self.is_running:
                try:
                    message = json.dumps({
                        "type": "worker_register",
                        "ip": self.local_ip,
                        "name": self.hostname,
                        "port": RPC_PORT,
                        "timestamp": time.time()
                    }).encode()
                    sock.sendto(message, ('<broadcast>', BROADCAST_PORT))
                    time.sleep(10)
                except:
                    pass

            sock.close()

        threading.Thread(target=alive_loop, daemon=True).start()

    def start(self):
        """启动Worker"""
        self.is_running = True

        print(f"AI集群Worker v{VERSION}")
        print(f"本机IP: {self.local_ip}")
        print(f"主机名: {self.hostname}")
        print()

        # 1. 启动RPC服务器
        if not self.start_rpc_server():
            print("[警告] RPC服务器启动失败，但继续运行")

        # 2. 发现Master
        if not self.discover_master():
            print("[错误] 无法发现Master，退出")
            return False

        # 3. 注册
        if not self.register_with_master():
            print("[错误] 注册失败，退出")
            return False

        # 4. 保持心跳
        self.keep_alive()

        print()
        print("=" * 50)
        print("Worker已就绪，等待Master分配任务...")
        print("=" * 50)
        print()

        # 保持运行
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n正在停止...")
            self.stop()

        return True

    def stop(self):
        """停止Worker"""
        self.is_running = False
        if self.rpc_process:
            self.rpc_process.terminate()
            print("[停止] RPC服务器已停止")


def main():
    worker = ClusterWorker()

    # 检查命令行参数
    if len(sys.argv) > 1:
        # 手动指定Master IP
        worker.master_ip = sys.argv[1]
        print(f"[手动] 使用Master IP: {worker.master_ip}")

    worker.start()


if __name__ == '__main__':
    main()
