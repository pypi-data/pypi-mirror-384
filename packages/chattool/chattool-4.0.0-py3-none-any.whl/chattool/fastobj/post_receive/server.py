import os
import json
import time
import ssl
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from chattool.fastobj.basic import FastAPIManager

class WriteRequest(BaseModel):
    """写入请求模型"""
    file_path: str  # 相对于 data 目录的文件路径
    data: Dict[Any, Any]  # JSON 数据
    mode: str = "a"  # 写入模式：'a' 追加（默认），'w' 覆盖


class ReadRequest(BaseModel):
    """读取请求模型"""
    file_path: str  # 相对于 data 目录的文件路径
    lines: Optional[int] = None  # 读取行数，None 表示读取全部


class FileWriterService:
    """文件写入服务类"""
    
    def __init__(self, workspace_dir: str = "./workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.data_dir = self.workspace_dir / "data"
        self.config_dir = self.workspace_dir / "config"
        self.config_file = self.config_dir / "config.json"
        
        # 初始化目录结构
        self._init_directories()
        
        # 加载配置
        self.config = self._load_config()
        
        # 创建 FastAPI 应用
        self.app = self._create_app()
    
    def _init_directories(self):
        """初始化目录结构"""
        self.workspace_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        
        # 如果配置文件不存在，创建默认配置
        if not self.config_file.exists():
            default_config = {
                "api_key": "your-secret-api-key-here",
                "ssl": {
                    "enabled": False,
                    "cert_file": "cert.pem",
                    "key_file": "key.pem"
                },
                "server": {
                    "host": "0.0.0.0",
                    "port": 8000
                }
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"无法加载配置文件: {e}")
    
    def _create_app(self) -> FastAPI:
        """创建 FastAPI 应用"""
        app = FastAPI(
            title="文件写入服务 API",
            description="支持 SSL 加密和密钥验证的文件写入/读取服务",
            version="1.0.0"
        )
        
        # 安全认证
        security = HTTPBearer()
        
        def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
            """验证 API 密钥"""
            if credentials.credentials != self.config["api_key"]:
                raise HTTPException(status_code=401, detail="无效的 API 密钥")
            return credentials.credentials
        
        @app.put("/write")
        async def write_file(
            request: WriteRequest,
            api_key: str = Depends(verify_api_key)
        ):
            """写入文件接口"""
            try:
                # 构建完整文件路径
                file_path = self.data_dir / request.file_path
                
                # 确保目录存在
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 准备写入的数据（添加时间戳）
                timestamp = datetime.now().isoformat()
                record = {
                    "timestamp": timestamp,
                    "data": request.data
                }
                
                # 写入文件
                mode = "w" if request.mode == "w" else "a"
                with open(file_path, mode, encoding='utf-8') as f:
                    json.dump(record, f, ensure_ascii=False)
                    f.write("\n")  # 每条记录一行
                
                return {
                    "status": "success",
                    "message": f"数据已{'覆盖' if request.mode == 'w' else '追加'}写入文件",
                    "file_path": request.file_path,
                    "timestamp": timestamp,
                    "mode": request.mode
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"写入文件失败: {str(e)}")
        
        @app.get("/read")
        async def read_file(
            file_path: str,
            lines: Optional[int] = None,
            api_key: str = Depends(verify_api_key)
        ):
            """读取文件接口"""
            try:
                # 构建完整文件路径
                full_path = self.data_dir / file_path
                
                if not full_path.exists():
                    raise HTTPException(status_code=404, detail="文件不存在")
                
                # 读取文件内容
                records = []
                with open(full_path, 'r', encoding='utf-8') as f:
                    file_lines = f.readlines()
                    
                    # 如果指定了行数，只读取最后 N 行
                    if lines is not None:
                        file_lines = file_lines[-lines:]
                    
                    for line in file_lines:
                        line = line.strip()
                        if line:
                            try:
                                records.append(json.loads(line))
                            except json.JSONDecodeError:
                                # 跳过无效的 JSON 行
                                continue
                
                return {
                    "status": "success",
                    "file_path": file_path,
                    "total_records": len(records),
                    "records": records
                }
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")
        
        @app.get("/health")
        async def health_check():
            """健康检查接口（无需认证）"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "workspace": str(self.workspace_dir.absolute())
            }
        
        @app.get("/config")
        async def get_config(api_key: str = Depends(verify_api_key)):
            """获取配置信息（隐藏敏感信息）"""
            safe_config = self.config.copy()
            safe_config["api_key"] = "***"  # 隐藏 API 密钥
            return safe_config
        
        return app
    
    def start_server(self):
        """启动服务器"""
        config = self.config["server"]
        ssl_config = self.config["ssl"]
        
        # SSL 配置
        ssl_keyfile = None
        ssl_certfile = None
        
        if ssl_config["enabled"]:
            cert_path = self.config_dir / ssl_config["cert_file"]
            key_path = self.config_dir / ssl_config["key_file"]
            
            if cert_path.exists() and key_path.exists():
                ssl_certfile = str(cert_path)
                ssl_keyfile = str(key_path)
                print(f"🔒 SSL 已启用")
            else:
                print(f"⚠️  SSL 证书文件不存在，使用 HTTP 模式")
        
        # 创建服务管理器
        manager = FastAPIManager(
            app=self.app,
            host=config["host"],
            port=config["port"],
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile
        )
        
        print(f"📁 工作目录: {self.workspace_dir.absolute()}")
        print(f"📂 数据目录: {self.data_dir.absolute()}")
        print(f"⚙️  配置目录: {self.config_dir.absolute()}")
        print(f"🔑 API 密钥: {self.config['api_key'][:8]}...")
        
        manager.start()
        return manager


def create_service(workspace_dir: str = "./workspace") -> FileWriterService:
    """创建文件写入服务实例"""
    return FileWriterService(workspace_dir)


if __name__ == "__main__":
    # 示例用法
    service = create_service()
    manager = service.start_server()
    
    try:
        print("\n服务已启动，按 Ctrl+C 停止...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        manager.stop()