#!/usr/bin/env python3
"""AI集群管理器 - Web UI版"""

import os
import sys
import json
import socket
import subprocess
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import webbrowser

# 常量
PORT = 18080
RPC_PORT = 50051
API_PORT = 8080
BROADCAST_PORT = 50053
VERSION = "1.0.0"

class ClusterManager:
    def __init__(self):
        self.nodes = {}  # {ip: {status, name, last_seen, role}}
        self.master_ip = self.get_local_ip()
        self.is_running = False
        self.rpc_process = None
        self.api_process = None

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

    def start_broadcast(self):
        """启动UDP广播，让Worker发现Master"""
        def broadcast_loop():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            message = json.dumps({
                "type": "master_announce",
                "ip": self.master_ip,
                "name": socket.gethostname(),
                "port": RPC_PORT,
                "timestamp": time.time()
            }).encode()

            while self.is_running:
                try:
                    sock.sendto(message, ('<broadcast>', BROADCAST_PORT))
                    time.sleep(5)
                except:
                    pass
            sock.close()

        threading.Thread(target=broadcast_loop, daemon=True).start()

    def start_listener(self):
        """监听Worker的注册请求"""
        def listener_loop():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('0.0.0.0', BROADCAST_PORT))

            while self.is_running:
                try:
                    data, addr = sock.recvfrom(1024)
                    message = json.loads(data.decode())

                    if message.get("type") == "worker_register":
                        ip = message.get("ip", addr[0])
                        name = message.get("name", "Unknown")
                        self.nodes[ip] = {
                            "status": "online",
                            "name": name,
                            "last_seen": time.time(),
                            "role": "worker"
                        }
                        print(f"[发现] Worker节点: {name} ({ip})")
                except:
                    pass
            sock.close()

        threading.Thread(target=listener_loop, daemon=True).start()

    def check_nodes(self):
        """定期检查节点状态"""
        def check_loop():
            while self.is_running:
                current_time = time.time()
                for ip in list(self.nodes.keys()):
                    if current_time - self.nodes[ip]["last_seen"] > 30:
                        self.nodes[ip]["status"] = "offline"
                        print(f"[离线] 节点: {self.nodes[ip]['name']} ({ip})")
                time.sleep(10)

        threading.Thread(target=check_loop, daemon=True).start()

    def start_rpc_server(self):
        """启动RPC服务器"""
        rpc_path = Path(__file__).parent.parent / "bin" / "rpc-server.exe"
        if not rpc_path.exists():
            print(f"[错误] RPC服务器不存在: {rpc_path}")
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

    def start_api_server(self, model_path, ngl=99):
        """启动API服务器"""
        server_path = Path(__file__).parent.parent / "bin" / "llama-server.exe"
        if not server_path.exists():
            print(f"[错误] API服务器不存在: {server_path}")
            return False

        # 收集所有Worker节点
        rpc_args = []
        for ip, node in self.nodes.items():
            if node["status"] == "online" and ip != "127.0.0.1":
                rpc_args.extend(["--rpc", f"{ip}:{RPC_PORT}"])

        try:
            cmd = [
                str(server_path),
                "-m", str(model_path),
                "--host", "0.0.0.0",
                "--port", str(API_PORT),
                "-ngl", str(ngl),
                "--parallel", "2"
            ] + rpc_args

            self.api_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print(f"[启动] API服务器 - 端口 {API_PORT}")
            print(f"[模型] {model_path}")
            print(f"[节点] {len(rpc_args)//2} 个Worker")
            return True
        except Exception as e:
            print(f"[错误] 启动API服务器失败: {e}")
            return False

    def start(self):
        """启动集群管理器"""
        self.is_running = True
        self.start_broadcast()
        self.start_listener()
        self.check_nodes()
        print(f"[启动] 集群管理器 - Master IP: {self.master_ip}")

    def stop(self):
        """停止集群管理器"""
        self.is_running = False
        if self.rpc_process:
            self.rpc_process.terminate()
        if self.api_process:
            self.api_process.terminate()
        print("[停止] 集群管理器")


# 全局实例
cluster = ClusterManager()


class ClusterHandler(SimpleHTTPRequestHandler):
    """HTTP请求处理器"""

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(get_html().encode('utf-8'))

        elif self.path == '/api/status':
            self.send_json({
                "master_ip": cluster.master_ip,
                "is_running": cluster.is_running,
                "nodes": cluster.nodes,
                "node_count": len(cluster.nodes),
                "online_count": len([n for n in cluster.nodes.values() if n["status"] == "online"])
            })

        elif self.path == '/api/nodes':
            self.send_json({"nodes": cluster.nodes})

        elif self.path == '/api/models':
            models_dir = Path(__file__).parent.parent / "models"
            models = []
            if models_dir.exists():
                models = [f.name for f in models_dir.glob("*.gguf")]
            self.send_json({"models": models})

        elif self.path == '/api/start-rpc':
            result = cluster.start_rpc_server()
            self.send_json({"success": result})

        elif self.path.startswith('/api/start-api'):
            import urllib.parse
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            model = params.get('model', [''])[0]
            ngl = int(params.get('ngl', ['99'])[0])

            if not model:
                self.send_json({"error": "请选择模型"}, 400)
                return

            model_path = Path(__file__).parent.parent / "models" / model
            if not model_path.exists():
                self.send_json({"error": f"模型不存在: {model}"}, 400)
                return

            result = cluster.start_api_server(model_path, ngl)
            self.send_json({"success": result})

        elif self.path == '/api/stop':
            cluster.stop()
            self.send_json({"success": True})

        else:
            super().do_GET()

    def send_json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        pass


def get_html():
    """返回Web UI HTML"""
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI集群管理器</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        .header {
            text-align: center;
            padding: 30px 0;
        }
        .header h1 {
            font-size: 2em;
            background: linear-gradient(135deg, #00d2ff, #3a7bd5);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .header p { color: #888; margin-top: 10px; }
        .card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 20px;
        }
        .card-title {
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
        }
        .status-online { background: #00b894; }
        .status-offline { background: #d63031; }
        .status-master { background: #0984e3; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
        .stat-value {
            font-size: 2.5em;
            font-weight: 700;
            background: linear-gradient(135deg, #00d2ff, #3a7bd5);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .stat-label {
            font-size: 0.9em;
            color: #888;
            margin-top: 5px;
        }
        .node-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .node-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 15px 20px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 10px;
        }
        .node-info { display: flex; align-items: center; gap: 15px; }
        .node-icon {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2em;
        }
        .node-icon.master { background: #0984e3; }
        .node-icon.worker { background: #00b894; }
        .node-name { font-weight: 500; }
        .node-ip { font-size: 0.85em; color: #888; }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #aaa;
        }
        .form-group select, .form-group input {
            width: 100%;
            padding: 12px 15px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 10px;
            color: #fff;
            font-size: 1em;
        }
        .form-group select option { background: #1a1a2e; }
        .btn {
            display: inline-block;
            padding: 12px 24px;
            border: none;
            border-radius: 10px;
            font-size: 1em;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary {
            background: linear-gradient(135deg, #00d2ff, #3a7bd5);
            color: #fff;
        }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(0,210,255,0.3); }
        .btn-danger {
            background: linear-gradient(135deg, #ff6b6b, #ee5a24);
            color: #fff;
        }
        .btn-success {
            background: linear-gradient(135deg, #00b894, #00cec9);
            color: #fff;
        }
        .btn-block { display: block; width: 100%; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .log-area {
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 15px;
            font-family: 'Consolas', monospace;
            font-size: 0.9em;
            color: #00ff00;
            height: 200px;
            overflow-y: auto;
        }
        .flex-row { display: flex; gap: 10px; }
        .flex-1 { flex: 1; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AI集群管理器</h1>
            <p>基于llama.cpp的分布式推理集群</p>
        </div>

        <div class="grid">
            <div class="stat-card">
                <div class="stat-value" id="masterIP">-</div>
                <div class="stat-label">Master IP</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="nodeCount">0</div>
                <div class="stat-label">总节点</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="onlineCount">0</div>
                <div class="stat-label">在线节点</div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">节点列表</div>
            <div class="node-list" id="nodeList">
                <div style="color: #666; text-align: center; padding: 20px;">
                    等待Worker节点连接...
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">启动集群</div>
            <div class="form-group">
                <label>选择模型</label>
                <select id="modelSelect">
                    <option value="">加载中...</option>
                </select>
            </div>
            <div class="form-group">
                <label>GPU层数 (ngl)</label>
                <input type="number" id="nglInput" value="99" min="0" max="99">
            </div>
            <div class="flex-row">
                <button class="btn btn-primary flex-1" onclick="startCluster()">启动集群</button>
                <button class="btn btn-danger" onclick="stopCluster()">停止</button>
            </div>
        </div>

        <div class="card">
            <div class="card-title">日志</div>
            <div class="log-area" id="logArea">等待操作...</div>
        </div>
    </div>

    <script>
        function log(msg) {
            const area = document.getElementById('logArea');
            const time = new Date().toLocaleTimeString('zh-CN');
            area.innerHTML += `<div>[${time}] ${msg}</div>`;
            area.scrollTop = area.scrollHeight;
        }

        async function fetchStatus() {
            try {
                const resp = await fetch('/api/status');
                const data = await resp.json();

                document.getElementById('masterIP').textContent = data.master_ip;
                document.getElementById('nodeCount').textContent = data.node_count;
                document.getElementById('onlineCount').textContent = data.online_count;

                renderNodes(data.nodes);
            } catch (e) {
                console.error('Fetch status error:', e);
            }
        }

        function renderNodes(nodes) {
            const container = document.getElementById('nodeList');
            const entries = Object.entries(nodes);

            if (entries.length === 0) {
                container.innerHTML = '<div style="color: #666; text-align: center; padding: 20px;">等待Worker节点连接...</div>';
                return;
            }

            container.innerHTML = entries.map(([ip, node]) => `
                <div class="node-item">
                    <div class="node-info">
                        <div class="node-icon ${ip === '127.0.0.1' ? 'master' : 'worker'}">
                            ${ip === '127.0.0.1' ? 'M' : 'W'}
                        </div>
                        <div>
                            <div class="node-name">${node.name}</div>
                            <div class="node-ip">${ip} ${ip === '127.0.0.1' ? '(本机)' : ''}</div>
                        </div>
                    </div>
                    <span class="status-badge status-${node.status}">${node.status === 'online' ? '在线' : '离线'}</span>
                </div>
            `).join('');
        }

        async function fetchModels() {
            try {
                const resp = await fetch('/api/models');
                const data = await resp.json();
                const select = document.getElementById('modelSelect');

                if (data.models.length === 0) {
                    select.innerHTML = '<option value="">请将GGUF模型放入models目录</option>';
                } else {
                    select.innerHTML = data.models.map(m =>
                        `<option value="${m}">${m}</option>`
                    ).join('');
                }
            } catch (e) {
                console.error('Fetch models error:', e);
            }
        }

        async function startCluster() {
            const model = document.getElementById('modelSelect').value;
            const ngl = document.getElementById('nglInput').value;

            if (!model) {
                alert('请选择模型');
                return;
            }

            log('正在启动RPC服务器...');
            await fetch('/api/start-rpc');

            log('正在启动API服务器...');
            const resp = await fetch(`/api/start-api?model=${encodeURIComponent(model)}&ngl=${ngl}`);
            const data = await resp.json();

            if (data.success) {
                log('集群启动成功！');
                log('API地址: http://localhost:8080');
            } else {
                log('启动失败: ' + (data.error || '未知错误'));
            }
        }

        async function stopCluster() {
            if (confirm('确定停止集群？')) {
                await fetch('/api/stop');
                log('集群已停止');
            }
        }

        // 定时刷新状态
        setInterval(fetchStatus, 3000);
        fetchStatus();
        fetchModels();
    </script>
</body>
</html>'''


def main():
    print(f"AI集群管理器 v{VERSION}")
    print(f"Master IP: {cluster.master_ip}")
    print(f"Web UI: http://localhost:{PORT}")
    print()

    # 启动集群管理器
    cluster.start()

    # 自动打开浏览器
    threading.Timer(1.5, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()

    # 启动HTTP服务器
    server = HTTPServer(('0.0.0.0', PORT), ClusterHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n正在停止...")
        cluster.stop()
        server.server_close()


if __name__ == '__main__':
    main()
