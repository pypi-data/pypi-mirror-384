# coding:utf-8
import asyncio
import base64
import hashlib
import io
import json
import logging
import os
import sys
import tempfile
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse, urlsplit, urlunsplit, quote

import httpx
import webbrowser
from PIL import Image
from volcengine.visual.VisualService import VisualService
from mcp.server.fastmcp import FastMCP


# 配置结构化日志
logging.basicConfig(
    level=logging.INFO if os.getenv('MCP_DEBUG') == '1' else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler() if os.getenv('MCP_DEBUG') == '1' else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)


class MCPImageCutoutConfig:
    """配置管理类"""

    def __init__(self):
        self.volc_access_key = os.getenv('VOLC_ACCESS_KEY')
        self.volc_secret_key = os.getenv('VOLC_SECRET_KEY')
        self.upload_url = os.getenv('MCP_UPLOAD_URL',
                                  'https://www.mcpcn.cc/api/fileUploadAndDownload/uploadMcpFile')
        self.debug_mode = os.getenv('MCP_DEBUG') == '1'
        self.disable_proxies = os.getenv('MCP_DISABLE_PROXIES') == '1'
        self.max_file_size = int(os.getenv('MCP_MAX_FILE_SIZE', '52428800'))  # 50MB
        self.request_timeout = int(os.getenv('MCP_REQUEST_TIMEOUT', '30'))

        # 允许的URL域名白名单
        self.allowed_domains = self._get_allowed_domains()

        self._validate_config()

    def _get_allowed_domains(self) -> List[str]:
        """获取允许的域名白名单"""
        domains = os.getenv('MCP_ALLOWED_DOMAINS', '')
        if domains:
            return [domain.strip() for domain in domains.split(',')]
        return []  # 空列表表示允许所有域名（生产环境应该设置白名单）

    def _validate_config(self):
        """验证配置"""
        if not self.volc_access_key or not self.volc_secret_key:
            logger.warning("火山引擎API密钥未配置，某些功能可能无法使用")

        if self.allowed_domains:
            logger.info(f"已设置域名白名单: {self.allowed_domains}")
        else:
            logger.warning("未设置域名白名单，建议在生产环境中配置 MCP_ALLOWED_DOMAINS")


class MCPImageCutoutError(Exception):
    """自定义异常类"""
    pass


class SecurityError(MCPImageCutoutError):
    """安全相关异常"""
    pass


class APIError(MCPImageCutoutError):
    """API调用异常"""
    pass


class VolcImageCutter:
    """图像抠图处理器 - 改进版"""

    def __init__(self, config: MCPImageCutoutConfig):
        self.config = config
        self._setup_visual_service()
        self._temp_dir = None
        self._http_client = None

    def _setup_visual_service(self):
        """设置火山引擎视觉服务"""
        try:
            self.visual_service = VisualService()
            if self.config.volc_access_key and self.config.volc_secret_key:
                self.visual_service.set_ak(self.config.volc_access_key)
                self.visual_service.set_sk(self.config.volc_secret_key)
                logger.info("火山引擎API凭证已配置")
            else:
                logger.warning("火山引擎API凭证未配置")
        except Exception as e:
            logger.error(f"初始化火山引擎服务失败: {e}")
            raise MCPImageCutoutError(f"初始化火山引擎服务失败: {e}")

    @asynccontextmanager
    async def _get_http_client(self):
        """获取HTTP客户端的上下文管理器"""
        if self._http_client is None:
            timeout = httpx.Timeout(self.config.request_timeout)
            self._http_client = httpx.AsyncClient(
                timeout=timeout,
                trust_env=not self.config.disable_proxies,
                limits=httpx.Limits(max_connections=10)
            )
        try:
            yield self._http_client
        finally:
            pass  # 保持连接复用

    async def _cleanup(self):
        """清理资源"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

        if self._temp_dir and self._temp_dir.exists():
            try:
                import shutil
                shutil.rmtree(self._temp_dir)
                logger.debug(f"已清理临时目录: {self._temp_dir}")
            except Exception as e:
                logger.error(f"清理临时目录失败: {e}")

    def _get_temp_dir(self) -> Path:
        """获取临时目录"""
        if self._temp_dir is None or not self._temp_dir.exists():
            self._temp_dir = Path(tempfile.mkdtemp(prefix="mcp_cutout_"))
            logger.debug(f"创建临时目录: {self._temp_dir}")
        return self._temp_dir

    def _validate_url(self, url: str) -> str:
        """验证和规范化URL"""
        try:
            parsed = urlparse(url)

            # 基本格式验证
            if not parsed.scheme or not parsed.netloc:
                raise SecurityError(f"无效的URL格式: {url}")

            # 协议验证
            if parsed.scheme not in ['http', 'https']:
                raise SecurityError(f"不支持的协议: {parsed.scheme}")

            # 域名白名单检查
            if self.config.allowed_domains:
                if parsed.netloc not in self.config.allowed_domains:
                    raise SecurityError(f"域名 {parsed.netloc} 不在允许的白名单中")

            # URL编码处理
            parts = urlsplit(url)
            encoded_path = quote(parts.path, safe="/-_.~")
            encoded_query = quote(parts.query, safe="=&-_.~")
            encoded_fragment = quote(parts.fragment, safe="-_.~")

            normalized_url = urlunsplit((
                parts.scheme,
                parts.netloc,
                encoded_path,
                encoded_query,
                encoded_fragment
            ))

            logger.debug(f"URL验证通过: {url} -> {normalized_url}")
            return normalized_url

        except SecurityError:
            raise
        except Exception as e:
            raise SecurityError(f"URL验证失败: {url}, 错误: {e}")

    def _generate_secure_filename(self, prefix: str = "cutout", suffix: str = ".png") -> str:
        """生成安全的文件名"""
        timestamp = int(time.time() * 1000)
        random_id = uuid.uuid4().hex[:8]
        return f"{prefix}_{timestamp}_{random_id}{suffix}"

    async def saliency_segmentation(self, image_urls: List[str]) -> List[Path]:
        """
        显著性分割抠图

        Args:
            image_urls: 图像URL列表

        Returns:
            保存的临时文件路径列表

        Raises:
            SecurityError: 安全验证失败
            APIError: API调用失败
            MCPImageCutoutError: 其他处理错误
        """
        if not image_urls:
            raise MCPImageCutoutError("图像URL列表不能为空")

        try:
            # 验证所有URL
            validated_urls = []
            for url in image_urls:
                try:
                    validated_url = self._validate_url(url)
                    validated_urls.append(validated_url)
                except SecurityError as e:
                    logger.error(f"URL验证失败: {url}, {e}")
                    raise

            # 准备API请求
            form = {
                "req_key": "saliency_seg",
                "image_urls": validated_urls,
            }

            # 调用火山引擎API
            try:
                # 临时禁用代理（如果需要）
                proxy_backup = {}
                if self.config.disable_proxies:
                    proxy_keys = ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
                                  "http_proxy", "https_proxy", "all_proxy"]
                    for key in proxy_keys:
                        if key in os.environ:
                            proxy_backup[key] = os.environ.pop(key)

                logger.info(f"开始处理 {len(validated_urls)} 张图片的抠图请求")
                resp = self.visual_service.cv_process(form)

                # 恢复代理设置
                for key, value in proxy_backup.items():
                    os.environ[key] = value

            except Exception as e:
                logger.error(f"火山引擎API调用失败: {e}")
                raise APIError(f"火山引擎API调用失败: {e}")

            # 处理API响应
            if not resp:
                raise APIError("API返回空响应")

            base64_images = self._extract_base64_images(resp)
            if not base64_images:
                logger.error(f"API响应中未找到图像数据: {json.dumps(resp, ensure_ascii=False)}")
                raise APIError("API响应中未找到有效的图像数据")

            # 保存图像到临时文件
            temp_files = []
            temp_dir = self._get_temp_dir()

            for i, base64_data in enumerate(base64_images):
                try:
                    if not base64_data:
                        continue

                    # 解码base64数据
                    image_data = base64.b64decode(base64_data)

                    # 验证图像数据
                    if len(image_data) > self.config.max_file_size:
                        logger.warning(f"图像 {i+1} 大小超过限制 ({len(image_data)} bytes)")
                        continue

                    # 生成安全的文件名
                    filename = self._generate_secure_filename(f"cutout_{i+1}")
                    temp_path = temp_dir / filename

                    # 保存文件
                    temp_path.write_bytes(image_data)
                    temp_files.append(temp_path)
                    logger.debug(f"已保存抠图结果: {temp_path}")

                except Exception as e:
                    logger.error(f"处理第 {i+1} 张图片时出错: {e}")
                    continue

            if not temp_files:
                raise MCPImageCutoutError("所有图片处理失败")

            logger.info(f"成功处理了 {len(temp_files)} 张图片")
            return temp_files

        except (SecurityError, APIError, MCPImageCutoutError):
            raise
        except Exception as e:
            logger.error(f"抠图处理过程中发生未知错误: {e}")
            raise MCPImageCutoutError(f"抠图处理失败: {e}")

    def _extract_base64_images(self, resp: Dict[str, Any]) -> List[str]:
        """从API响应中提取base64图像数据"""
        base64_images = []

        # 定义可能的字段名
        possible_fields = [
            'binary_data_base64', 'base64_images', 'images',
            'result_images', 'image_base64', 'data'
        ]

        # 检查data字段
        if 'data' in resp and isinstance(resp['data'], dict):
            data = resp['data']
            for field in possible_fields[:-1]:  # 排除'data'避免递归
                if field in data:
                    result = data[field]
                    if isinstance(result, list):
                        base64_images.extend([img for img in result if img])
                    elif isinstance(result, str) and result:
                        base64_images.append(result)
                    break

        # 检查顶层字段
        if not base64_images:
            for field in possible_fields[:-1]:  # 排除'data'
                if field in resp:
                    result = resp[field]
                    if isinstance(result, list):
                        base64_images.extend([img for img in result if img])
                    elif isinstance(result, str) and result:
                        base64_images.append(result)
                    break

        return base64_images

    async def upload_image_from_file(self, file_path: Path, filename: str) -> Dict[str, Any]:
        """
        从文件路径上传图片

        Args:
            file_path: 文件路径
            filename: 上传时使用的文件名

        Returns:
            上传结果字典
        """
        if not file_path.exists():
            return {"success": False, "error": f"文件不存在: {file_path}"}

        if file_path.stat().st_size > self.config.max_file_size:
            return {"success": False, "error": f"文件大小超过限制: {self.config.max_file_size}"}

        try:
            # 验证图片文件
            with Image.open(file_path) as img:
                width, height = img.size
                logger.debug(f"图片尺寸: {width}x{height}")
        except Exception as e:
            return {"success": False, "error": f"无效的图片文件: {e}"}

        try:
            async with self._get_http_client() as client:
                with open(file_path, 'rb') as f:
                    files = {'file': (filename, f, 'image/png')}
                    response = await client.post(self.config.upload_url, files=files)

                if response.status_code == 200:
                    result = response.json()
                    if result.get('code') == 0:
                        logger.info(f"文件上传成功: {filename}")
                        return {"success": True, "url": result['data']['url']}
                    else:
                        error_msg = result.get('msg', '未知错误')
                        logger.error(f"上传失败: {error_msg}")
                        return {"success": False, "error": error_msg}
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"上传请求失败: {error_msg}")
                    return {"success": False, "error": error_msg}

        except httpx.TimeoutException:
            return {"success": False, "error": "上传超时"}
        except Exception as e:
            logger.error(f"上传过程中发生错误: {e}")
            return {"success": False, "error": f"上传失败: {e}"}


# 初始化配置和服务
config = MCPImageCutoutConfig()
mcp = FastMCP("AI抠图工具")
cutter = VolcImageCutter(config)


@mcp.tool()
async def image_cutout(image_urls: List[str], open_in_browser: bool = False) -> Dict[str, Any]:
    """
    对图像进行显著性分割抠图。

    Args:
        image_urls: 图像URL列表，支持多张图片。
        open_in_browser: 是否在浏览器中打开结果图片

    Returns:
        处理结果字典，包含success状态、处理结果和详细信息
    
    Raises:
        MCPImageCutoutError: 当处理失败时抛出异常，符合MCP协议规范
    """
    if not image_urls:
        raise MCPImageCutoutError("图像URL列表不能为空")

    try:
        # 进行抠图处理
        temp_files = await cutter.saliency_segmentation(image_urls)

        if not temp_files:
            raise MCPImageCutoutError("抠图处理失败：未获取到有效结果")

        # 上传处理结果
        uploaded_urls = []
        upload_results = []

        for i, temp_file in enumerate(temp_files):
            try:
                # 验证文件
                with Image.open(temp_file) as img:
                    width, height = img.size
                    logger.debug(f"处理结果 {i+1}: {width}x{height}")

                # 上传文件
                filename = f"cutout_{i+1}_{int(time.time())}.png"
                upload_result = await cutter.upload_image_from_file(temp_file, filename)

                if upload_result.get('success'):
                    uploaded_urls.append(upload_result['url'])
                    upload_results.append(f"✅ 第 {i+1} 张: 处理成功")
                    logger.info(f"第 {i+1} 张图片处理完成: {upload_result['url']}")
                else:
                    upload_results.append(f"❌ 第 {i+1} 张: {upload_result.get('error', '未知错误')}")
                    logger.error(f"第 {i+1} 张图片上传失败: {upload_result.get('error')}")

            except Exception as e:
                upload_results.append(f"❌ 第 {i+1} 张: 处理失败 - {str(e)}")
                logger.error(f"处理第 {i+1} 张图片时出错: {e}")
            finally:
                # 清理临时文件
                try:
                    if temp_file.exists():
                        temp_file.unlink()
                        logger.debug(f"已删除临时文件: {temp_file}")
                except Exception as e:
                    logger.error(f"删除临时文件失败: {e}")

        # 在浏览器中打开结果（如果需要）
        if open_in_browser and uploaded_urls:
            try:
                for url in uploaded_urls[:3]:  # 限制最多打开3个标签页
                    webbrowser.open_new_tab(url)
                    await asyncio.sleep(0.5)  # 避免打开过快
                logger.info(f"已在浏览器中打开 {min(len(uploaded_urls), 3)} 个结果")
            except Exception as e:
                logger.error(f"打开浏览器失败: {e}")

        # 返回结果
        if uploaded_urls:
            return {
                "success": True,
                "data": uploaded_urls[0] if len(uploaded_urls) == 1 else uploaded_urls,
                "message": "\n".join(upload_results),
                "processed_count": len(uploaded_urls),
                "total_count": len(temp_files)
            }
        else:
            # 所有图片都处理失败，抛出异常
            error_msg = "所有图片处理失败\n" + "\n".join(upload_results)
            raise MCPImageCutoutError(error_msg)

    except (SecurityError, APIError, MCPImageCutoutError):
        # 直接重新抛出已知异常，让FastMCP框架处理并设置isError: true
        raise
    except Exception as e:
        logger.error(f"处理过程中发生未知错误: {e}")
        raise MCPImageCutoutError(f"处理失败: {e}")


async def cleanup_on_exit():
    """退出时清理资源"""
    try:
        await cutter._cleanup()
        logger.info("资源清理完成")
    except Exception as e:
        logger.error(f"资源清理失败: {e}")


def main():
    """主入口函数"""
    import argparse
    import signal
    import asyncio

    parser = argparse.ArgumentParser(description='MCP AI抠图服务器')
    parser.add_argument('transport', nargs='?', default='stdio',
                        choices=['stdio', 'sse'],
                        help='传输协议类型')
    args = parser.parse_args()

    # 注册清理函数
    def signal_handler(sig, frame):
        logger.info("收到退出信号，正在清理资源...")
        asyncio.create_task(cleanup_on_exit())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        logger.info(f"启动MCP AI抠图服务器 (transport: {args.transport})")

        if args.transport == 'sse':
            mcp.run(transport='sse', sse_host='127.0.0.1', sse_port=8080)
        else:
            mcp.run(transport='stdio')

    except KeyboardInterrupt:
        logger.info("接收到中断信号")
    except Exception as e:
        logger.error(f"服务器运行错误: {e}")
        raise
    finally:
        asyncio.run(cleanup_on_exit())


if __name__ == "__main__":
    main()
