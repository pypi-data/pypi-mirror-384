"""文件服务"""

import logging
import mimetypes
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import aiohttp

from ..utils.config import Config


class FileService:
    """文件服务类

    提供文件上传、下载等功能，集成uniCloud OSS服务。
    支持从服务端动态获取文件服务密钥。
    """

    def __init__(self, config: Config):
        """初始化文件服务

        Args:
            config: 配置对象
        """
        self.config = config
        self.logger = logging.getLogger("FileService")

        # HTTP会话
        self._session: Optional[aiohttp.ClientSession] = None

        # OSS配置（初始为空，通过 set_oss_config 或 init_from_platform_config 设置）
        self._oss_config: Optional[Dict[str, Any]] = None
        self._oss_config_expires_at: Optional[int] = None

        # OSS客户端（延迟加载）
        self._oss_bucket = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def set_oss_config(self, config: Dict[str, Any], expires_at: Optional[int] = None):
        """手动设置OSS配置

        Args:
            config: OSS配置字典，包含：
                - access_key_id: 访问密钥ID
                - access_key_secret: 访问密钥
                - bucket_name: 桶名称
                - endpoint: 端点
                - base_path: 基础路径（可选）
                - region: 区域（可选）
            expires_at: 配置过期时间戳（可选）
        """
        self._oss_config = {
            "access_key_id": config.get("access_key_id"),
            "access_key_secret": config.get("access_key_secret"),
            "bucket_name": config.get("bucket_name"),
            "endpoint": config.get("endpoint"),
            "base_path": config.get("base_path", "agent-reports"),
            "region": config.get("region", ""),
        }
        self._oss_config_expires_at = expires_at
        self.logger.info(
            f"✅ OSS配置已设置: bucket={self._oss_config['bucket_name']}, endpoint={self._oss_config['endpoint']}"
        )
        if expires_at:
            self.logger.info(f"⏰ 密钥有效期: {expires_at}")

    async def init_from_platform_config(self, file_service_config: Dict[str, Any]):
        """从平台配置初始化文件服务

        Args:
            file_service_config: 来自平台API的文件服务配置
        """
        if not file_service_config:
            raise ValueError("文件服务配置不能为空")

        self.set_oss_config(
            config={
                "access_key_id": file_service_config.get("access_key_id"),
                "access_key_secret": file_service_config.get("access_key_secret"),
                "bucket_name": file_service_config.get("bucket_name"),
                "endpoint": file_service_config.get("endpoint"),
                "base_path": file_service_config.get("base_path", "agent-reports"),
                "region": file_service_config.get("region", ""),
            },
            expires_at=file_service_config.get("expires_at"),
        )
        self.logger.info("✅ 文件服务已从平台配置初始化")

    def _validate_oss_config(self):
        """验证OSS配置是否有效"""
        if self._oss_config is None:
            raise RuntimeError(
                "OSS配置未设置，请先调用 set_oss_config 或 init_from_platform_config"
            )

        required_keys = [
            "access_key_id",
            "access_key_secret",
            "bucket_name",
            "endpoint",
        ]
        for key in required_keys:
            if not self._oss_config.get(key):
                raise RuntimeError(f"OSS配置缺少必要字段: {key}")

        # 检查密钥是否过期
        if self._oss_config_expires_at:
            import time

            if time.time() > self._oss_config_expires_at:
                self.logger.warning("⚠️ OSS密钥已过期，需要重新获取")
                raise RuntimeError("OSS密钥已过期")

    def _get_oss_bucket(self):
        """获取OSS Bucket客户端（延迟加载）"""
        if self._oss_bucket is None:
            try:
                # 验证配置
                self._validate_oss_config()

                import oss2

                auth = oss2.Auth(
                    self._oss_config["access_key_id"],
                    self._oss_config["access_key_secret"],
                )
                self._oss_bucket = oss2.Bucket(
                    auth, self._oss_config["endpoint"], self._oss_config["bucket_name"]
                )
                self.logger.info(
                    f"✅ OSS客户端初始化成功: {self._oss_config['bucket_name']}"
                )
            except ImportError:
                self.logger.error("❌ OSS功能需要安装 oss2 库: pip install oss2")
                raise
            except Exception as e:
                self.logger.error(f"❌ OSS客户端初始化失败: {e}")
                raise
        return self._oss_bucket

    async def close(self):
        """关闭HTTP会话"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def upload_file(
        self,
        file_path: Union[str, Path],
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
        folder: str = "files",
    ) -> Dict[str, Any]:
        """上传文件到OSS

        Args:
            file_path: 本地文件路径
            filename: 指定文件名，默认使用原文件名
            content_type: MIME类型，默认自动检测
            folder: 文件夹名称

        Returns:
            上传结果，包含文件URL等信息
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")

            # 确定文件名和MIME类型
            filename = filename or file_path.name
            if not content_type:
                content_type, _ = mimetypes.guess_type(str(file_path))
                content_type = content_type or "application/octet-stream"

            self.logger.info(f"上传文件到OSS: {filename} ({content_type})")

            # 读取文件内容
            with open(file_path, "rb") as f:
                file_data = f.read()

            # 使用OSS上传
            return await self.upload_bytes_to_oss(
                content=file_data,
                filename=filename,
                content_type=content_type,
                folder=folder,
            )

        except Exception as e:
            self.logger.error(f"上传文件失败: {e}")
            raise

    async def upload_html_to_oss(
        self, html_content: str, filename: Optional[str] = None, folder: str = "reports"
    ) -> Dict[str, Any]:
        """上传HTML内容到OSS，设置正确的预览头

        Args:
            html_content: HTML内容字符串
            filename: 文件名（可选，会自动生成）
            folder: 文件夹名称

        Returns:
            包含上传结果的字典
        """
        try:
            # 生成文件名
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                random_id = str(uuid.uuid4())[:8]
                filename = f"report_{timestamp}_{random_id}.html"

            # 确保文件名以.html结尾
            if not filename.endswith(".html"):
                filename += ".html"

            # 验证配置
            self._validate_oss_config()

            # 生成文件路径
            file_key = f"{self._oss_config['base_path']}/{folder}/{filename}"

            self.logger.info(f"开始上传HTML到OSS: {file_key}")

            # 获取OSS客户端
            bucket = self._get_oss_bucket()

            # 设置HTTP头，确保浏览器预览而非下载
            headers = {
                "Content-Type": "text/html; charset=utf-8",
                "Content-Disposition": 'inline; filename="agent-report.html"',
                "Cache-Control": "max-age=3600",
            }

            # 上传文件
            result = bucket.put_object(
                file_key, html_content.encode("utf-8"), headers=headers
            )

            if result.status == 200:
                # 生成访问URL
                public_url = f"https://{self._oss_config['bucket_name']}.{self._oss_config['endpoint']}/{file_key}"

                # 验证文件是否存在
                if bucket.object_exists(file_key):
                    # 获取文件信息
                    info = bucket.head_object(file_key)

                    self.logger.info(f"HTML报告上传成功: {public_url}")

                    return {
                        "success": True,
                        "file_url": public_url,
                        "url": public_url,  # 兼容现有接口
                        "file_key": file_key,
                        "filename": filename,
                        "size": info.content_length,
                        "content_type": info.content_type,
                        "upload_time": datetime.now().isoformat(),
                    }
                else:
                    raise Exception("文件上传后验证失败")
            else:
                raise Exception(f"上传失败，状态码: {result.status}")

        except Exception as e:
            self.logger.error(f"HTML报告上传失败: {e}")
            return {"success": False, "error": str(e), "file_url": None, "url": None}

    async def upload_bytes_to_oss(
        self,
        content: bytes,
        filename: str,
        content_type: Optional[str] = None,
        folder: str = "files",
    ) -> Dict[str, Any]:
        """上传字节内容到OSS

        Args:
            content: 字节内容
            filename: 文件名
            content_type: 内容类型
            folder: 文件夹名称

        Returns:
            上传结果
        """
        try:
            # 验证配置
            self._validate_oss_config()

            # 检测Content-Type
            if not content_type:
                content_type = self.get_mime_type(filename)

            # 生成文件路径
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_id = str(uuid.uuid4())[:8]
            safe_filename = f"{timestamp}_{random_id}_{filename}"
            file_key = f"{self._oss_config['base_path']}/{folder}/{safe_filename}"

            self.logger.info(f"开始上传文件到OSS: {file_key}")

            # 获取OSS客户端
            bucket = self._get_oss_bucket()

            # 设置HTTP头
            headers = {
                "Content-Type": content_type,
                "Content-Disposition": f'inline; filename="{filename}"',
            }

            # 对于HTML文件，特别设置预览头
            if filename.lower().endswith(".html"):
                headers["Content-Disposition"] = 'inline; filename="agent-report.html"'

            # 上传文件
            result = bucket.put_object(file_key, content, headers=headers)

            if result.status == 200:
                public_url = f"https://{self._oss_config['bucket_name']}.{self._oss_config['endpoint']}/{file_key}"

                return {
                    "success": True,
                    "file_url": public_url,
                    "url": public_url,
                    "file_key": file_key,
                    "filename": safe_filename,
                    "original_filename": filename,
                    "size": len(content),
                    "content_type": content_type,
                    "upload_time": datetime.now().isoformat(),
                }
            else:
                raise Exception(f"上传失败，状态码: {result.status}")

        except Exception as e:
            self.logger.error(f"文件上传失败: {e}")
            return {"success": False, "error": str(e), "file_url": None, "url": None}

    async def download_file(
        self, file_url: str, save_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """下载文件

        Args:
            file_url: 文件URL
            save_path: 保存路径，默认保存到临时目录

        Returns:
            下载文件的本地路径
        """
        try:
            session = await self._get_session()

            self.logger.info(f"下载文件: {file_url}")

            async with session.get(file_url) as resp:
                if resp.status != 200:
                    raise Exception(f"下载失败: HTTP {resp.status}")

                # 确定保存路径
                if save_path is None:
                    filename = os.path.basename(file_url.split("?")[0])
                    save_path = Path.cwd() / "downloads" / filename
                else:
                    save_path = Path(save_path)

                # 创建目录
                save_path.parent.mkdir(parents=True, exist_ok=True)

                # 写入文件
                with open(save_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(8192):
                        f.write(chunk)

                self.logger.info(f"文件已保存到: {save_path}")
                return save_path

        except Exception as e:
            self.logger.error(f"下载文件失败: {e}")
            raise

    async def get_file_info(self, file_url: str) -> Dict[str, Any]:
        """获取文件信息

        Args:
            file_url: 文件URL

        Returns:
            文件信息
        """
        try:
            session = await self._get_session()

            async with session.head(file_url) as resp:
                if resp.status != 200:
                    raise Exception(f"获取文件信息失败: HTTP {resp.status}")

                return {
                    "url": file_url,
                    "content_type": resp.headers.get("Content-Type"),
                    "content_length": int(resp.headers.get("Content-Length", 0)),
                    "last_modified": resp.headers.get("Last-Modified"),
                }

        except Exception as e:
            self.logger.error(f"获取文件信息失败: {e}")
            raise

    def get_mime_type(self, filename: str) -> str:
        """获取文件MIME类型

        Args:
            filename: 文件名

        Returns:
            MIME类型
        """
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"

    def is_image(self, filename: str) -> bool:
        """判断是否为图片文件"""
        mime_type = self.get_mime_type(filename)
        return mime_type.startswith("image/")

    def is_video(self, filename: str) -> bool:
        """判断是否为视频文件"""
        mime_type = self.get_mime_type(filename)
        return mime_type.startswith("video/")

    def is_audio(self, filename: str) -> bool:
        """判断是否为音频文件"""
        mime_type = self.get_mime_type(filename)
        return mime_type.startswith("audio/")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
