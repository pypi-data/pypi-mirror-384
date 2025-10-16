import json
import time
import threading
import requests
from datetime import datetime
from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ClientConfig:
    """客户端配置"""
    endpoint: str  # 服务端地址
    api_key: str  # API 密钥
    interval: float = 5.0  # 默认请求间隔（秒）
    timeout: float = 10.0  # 请求超时时间
    verify_ssl: bool = True  # 是否验证 SSL 证书


class FileWriterClient:
    """文件写入服务客户端"""
    
    def __init__(self, config: ClientConfig, data_function: Callable[[], Dict[Any, Any]]):
        """
        初始化客户端
        
        Args:
            config: 客户端配置
            data_function: 返回 JSON 数据的函数
        """
        self.config = config
        self.data_function = data_function
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # 请求头
        self.headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        # 会话对象，用于连接复用
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _send_write_request(self, file_path: str, data: Dict[Any, Any], mode: str = "a") -> bool:
        """
        发送写入请求到服务端
        
        Args:
            file_path: 文件路径
            data: 要写入的数据
            mode: 写入模式 ('a' 追加, 'w' 覆盖)
            
        Returns:
            bool: 请求是否成功
        """
        try:
            url = f"{self.config.endpoint.rstrip('/')}/write"
            payload = {
                "file_path": file_path,
                "data": data,
                "mode": mode
            }
            
            response = self.session.put(
                url,
                json=payload,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 数据写入成功: {file_path} | {result.get('timestamp', '')}")
                return True
            else:
                print(f"❌ 写入失败 [{response.status_code}]: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"⏰ 请求超时: {url}")
            return False
        except requests.exceptions.ConnectionError:
            print(f"🔌 连接失败: {url}")
            return False
        except Exception as e:
            print(f"💥 请求异常: {str(e)}")
            return False
    
    def _worker_loop(self, file_path: str, mode: str, interval: float):
        """
        工作线程循环
        
        Args:
            file_path: 文件路径
            mode: 写入模式
            interval: 请求间隔
        """
        print(f"🚀 客户端已启动")
        print(f"📁 目标文件: {file_path}")
        print(f"📝 写入模式: {'覆盖' if mode == 'w' else '追加'}")
        print(f"⏱️  请求间隔: {interval} 秒")
        print(f"🌐 服务端点: {self.config.endpoint}")
        
        while not self.stop_event.is_set():
            try:
                # 执行用户提供的函数获取数据
                data = self.data_function()
                
                if data is not None:
                    # 发送写入请求
                    success = self._send_write_request(file_path, data, mode)
                    
                    if not success:
                        print(f"⚠️  写入失败，将在 {interval} 秒后重试")
                else:
                    print(f"⚠️  数据函数返回 None，跳过本次写入")
                
            except Exception as e:
                print(f"💥 执行数据函数时发生异常: {str(e)}")
            
            # 等待指定间隔或停止信号
            if self.stop_event.wait(timeout=interval):
                break
        
        print(f"🛑 客户端已停止")
    
    def start(self, file_path: str, mode: str = "a", interval: Optional[float] = None):
        """
        启动客户端
        
        Args:
            file_path: 目标文件路径（相对于服务端 data 目录）
            mode: 写入模式 ('a' 追加, 'w' 覆盖)
            interval: 请求间隔（秒），如果为 None 则使用配置中的默认值
        """
        if self.is_running:
            print(f"⚠️  客户端已在运行中")
            return
        
        # 使用指定间隔或默认间隔
        actual_interval = interval if interval is not None else self.config.interval
        
        # 验证参数
        if not file_path.strip():
            raise ValueError("文件路径不能为空")
        
        if mode not in ["a", "w"]:
            raise ValueError("写入模式必须是 'a'（追加）或 'w'（覆盖）")
        
        if actual_interval <= 0:
            raise ValueError("请求间隔必须大于 0")
        
        # 测试连接
        if not self._test_connection():
            print(f"❌ 无法连接到服务端，请检查配置")
            return
        
        # 重置停止事件
        self.stop_event.clear()
        
        # 启动工作线程
        self.thread = threading.Thread(
            target=self._worker_loop,
            args=(file_path, mode, actual_interval),
            daemon=True
        )
        self.thread.start()
        self.is_running = True
    
    def stop(self):
        """停止客户端"""
        if not self.is_running:
            print(f"⚠️  客户端未在运行")
            return
        
        print(f"🔄 正在停止客户端...")
        self.stop_event.set()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        self.is_running = False
    
    def _test_connection(self) -> bool:
        """
        测试与服务端的连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            url = f"{self.config.endpoint.rstrip('/')}/health"
            response = self.session.get(
                url,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl
            )
            
            if response.status_code == 200:
                print(f"✅ 服务端连接正常")
                return True
            else:
                print(f"❌ 服务端响应异常 [{response.status_code}]")
                return False
                
        except Exception as e:
            print(f"❌ 连接测试失败: {str(e)}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取客户端状态
        
        Returns:
            Dict: 状态信息
        """
        return {
            "running": self.is_running,
            "endpoint": self.config.endpoint,
            "interval": self.config.interval,
            "thread_alive": self.thread.is_alive() if self.thread else False
        }
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()
        self.session.close()


# 示例数据函数
def sample_data_function() -> Dict[str, Any]:
    """
    示例数据函数 - 返回当前系统信息
    """
    import psutil
    import platform
    
    try:
        return {
            "system": {
                "platform": platform.system(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent
            },
            "timestamp_local": datetime.now().isoformat()
        }
    except ImportError:
        # 如果没有 psutil，返回简单数据
        return {
            "message": "Hello from client",
            "counter": int(time.time()) % 1000,
            "timestamp_local": datetime.now().isoformat()
        }


def simple_data_function() -> Dict[str, Any]:
    """
    简单数据函数 - 返回基本信息
    """
    return {
        "message": "定期数据推送",
        "counter": int(time.time()) % 10000,
        "random_value": hash(str(time.time())) % 100
    }


if __name__ == "__main__":
    # 使用示例
    config = ClientConfig(
        endpoint="http://localhost:8000",  # 或 https://your-server.com
        api_key="your-secret-api-key-here",
        interval=3.0,  # 3秒间隔
        timeout=10.0
    )
    
    # 创建客户端
    with FileWriterClient(config, simple_data_function) as client:
        try:
            # 启动客户端，每2秒写入一次数据到 logs/client.json
            client.start(
                file_path="logs/client.json",
                mode="a",  # 追加模式
                interval=2.0  # 覆盖默认间隔
            )
            
            print("\n客户端正在运行，按 Ctrl+C 停止...")
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n正在停止客户端...")