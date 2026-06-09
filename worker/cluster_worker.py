#!/usr/bin/env python3
"""AI集群Worker - 自动发现Master并注册"""

import os
import sys
import json
import socket
import subprocess
import threading
import time
import logging
from pathlib import Path

# 添加父目录到路径，以便导入 config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import BROADCAST_PORT, RPC_PORT, VERSION, HEARTBEAT_INTERVAL

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


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
        except Exception as e:
            logger.warning(f"获取本机IP失败: {e}，使用 127.0.0.1")
            return "127.0.0.1"

    def discover_master(self):
        """自动发现Master节点"""
        logger.info("正在搜索Master节点...")

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
                    logger.info(f"找到Master: {self.master_ip}:{self.master_port}")
                    break
            except socket.timeout:
                logger.warning("未发现Master，继续等待...")
            except json.JSONDecodeError as e:
                logger.warning(f"收到无效JSON数据: {e}")
            except Exception as e:
                logger.error(f"发现Master失败: {e}")

        sock.close()
        return self.master_ip is not None

    def register_with_master(self):
        """向Master注册"""
        if not self.master_ip:
            return False

        logger.info("向Master注册...")

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
            logger.info(f"注册成功: {self.hostname} ({self.local_ip})")
            return True
        except Exception as e:
            logger.error(f"注册失败: {e}")
            return False
        finally:
            sock.close()

    def start_rpc_server(self):
        """启动RPC服务器"""
        rpc_path = Path(__file__).parent.parent / "bin" / "rpc-server.exe"
        if not rpc_path.exists():
            logger.error(f"RPC服务器不存在: {rpc_path}")
            logger.info("请从 https://github.com/ggerganov/llama.cpp/releases 下载")
            return False

        try:
            self.rpc_process = subprocess.Popen(
                [str(rpc_path), "-H", "0.0.0.0", "-p", str(RPC_PORT), "-c"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"RPC服务器启动成功 - 端口 {RPC_PORT}")
            return True
        except Exception as e:
            logger.error(f"启动RPC服务器失败: {e}")
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
                    time.sleep(HEARTBEAT_INTERVAL)
                except Exception as e:
                    logger.warning(f"心跳发送失败: {e}")
                    time.sleep(1)

            sock.close()

        threading.Thread(target=alive_loop, daemon=True).start()

    def start(self):
        """启动Worker"""
        self.is_running = True

        logger.info(f"AI集群Worker v{VERSION}")
        logger.info(f"本机IP: {self.local_ip}")
        logger.info(f"主机名: {self.hostname}")

        # 1. 启动RPC服务器
        if not self.start_rpc_server():
            logger.warning("RPC服务器启动失败，但继续运行")

        # 2. 发现Master
        if not self.discover_master():
            logger.error("无法发现Master，退出")
            return False

        # 3. 注册
        if not self.register_with_master():
            logger.error("注册失败，退出")
            return False

        # 4. 保持心跳
        self.keep_alive()

        logger.info("=" * 50)
        logger.info("Worker已就绪，等待Master分配任务...")
        logger.info("=" * 50)

        # 保持运行
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("正在停止...")
            self.stop()

        return True

    def stop(self):
        """停止Worker"""
        self.is_running = False
        if self.rpc_process:
            self.rpc_process.terminate()
            logger.info("RPC服务器已停止")


def main():
    worker = ClusterWorker()

    # 检查命令行参数
    if len(sys.argv) > 1:
        # 手动指定Master IP
        worker.master_ip = sys.argv[1]
        logger.info(f"手动指定Master IP: {worker.master_ip}")

    worker.start()


if __name__ == '__main__':
    main()
