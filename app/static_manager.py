#!/usr/bin/env python3
"""
静态资源管理器 - 本地化所有远程资源
"""

import os
import requests
import hashlib
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class StaticResourceManager:
    """静态资源管理器"""
    
    def __init__(self, static_dir: str = "static"):
        self.static_dir = Path(static_dir)
        self.static_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        (self.static_dir / "css").mkdir(exist_ok=True)
        (self.static_dir / "js").mkdir(exist_ok=True)
        (self.static_dir / "fonts").mkdir(exist_ok=True)
        (self.static_dir / "images").mkdir(exist_ok=True)
        (self.static_dir / "icons").mkdir(exist_ok=True)
        
        # 常用CDN资源映射
        self.cdn_resources = {
            # CSS框架
            "bootstrap_css": {
                "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css",
                "local_path": "css/bootstrap.min.css"
            },
            "fontawesome_css": {
                "url": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
                "local_path": "css/fontawesome.min.css"
            },
            
            # JavaScript库
            "bootstrap_js": {
                "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js",
                "local_path": "js/bootstrap.bundle.min.js"
            },
            "jquery": {
                "url": "https://code.jquery.com/jquery-3.6.0.min.js",
                "local_path": "js/jquery.min.js"
            },
            "plotly_js": {
                "url": "https://cdn.plot.ly/plotly-latest.min.js",
                "local_path": "js/plotly.min.js"
            },
            
            # 字体文件
            "chinese_font": {
                "url": "https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap",
                "local_path": "fonts/noto-sans-sc.css"
            }
        }
    
    def download_resource(self, url: str, local_path: str, force: bool = False) -> bool:
        """下载远程资源到本地"""
        full_path = self.static_dir / local_path
        
        # 如果文件已存在且不强制更新，跳过
        if full_path.exists() and not force:
            logger.info(f"资源已存在: {local_path}")
            return True
        
        try:
            logger.info(f"下载资源: {url} -> {local_path}")
            
            # 创建目录
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 下载文件
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # 保存文件
            with open(full_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"下载成功: {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"下载失败 {url}: {str(e)}")
            return False
    
    def download_all_resources(self, force: bool = False) -> Dict[str, bool]:
        """下载所有CDN资源"""
        results = {}
        
        for name, resource in self.cdn_resources.items():
            success = self.download_resource(
                resource["url"], 
                resource["local_path"], 
                force
            )
            results[name] = success
        
        return results
    
    def get_local_url(self, resource_name: str) -> Optional[str]:
        """获取本地资源URL"""
        if resource_name not in self.cdn_resources:
            return None
        
        local_path = self.cdn_resources[resource_name]["local_path"]
        full_path = self.static_dir / local_path
        
        if full_path.exists():
            return f"/static/{local_path}"
        else:
            # 如果本地文件不存在，返回CDN URL作为备选
            return self.cdn_resources[resource_name]["url"]
    
    def create_local_css(self) -> str:
        """创建本地CSS文件路径"""
        css_content = """
        /* Gordon Wang 股票预测系统 - 本地化CSS */
        
        /* 中文字体优化 */
        @font-face {
            font-family: 'Chinese Font';
            src: local('Microsoft YaHei'), local('SimHei'), local('SimSun');
            font-display: swap;
        }
        
        body {
            font-family: 'Chinese Font', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* 确保中文字符正确显示 */
        .chinese-text {
            font-family: 'Chinese Font', sans-serif;
            font-weight: 400;
        }
        
        /* 本地化图标 */
        .icon-local {
            display: inline-block;
            width: 1em;
            height: 1em;
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
        }
        
        .icon-chart {
            background-image: url('/static/icons/chart.svg');
        }
        
        .icon-settings {
            background-image: url('/static/icons/settings.svg');
        }
        
        .icon-download {
            background-image: url('/static/icons/download.svg');
        }
        """
        
        css_path = self.static_dir / "css" / "local.css"
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(css_content)
        
        return str(css_path)
    
    def create_local_icons(self):
        """创建本地SVG图标"""
        icons = {
            "chart.svg": """
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M3 13h2v8H3v-8zm4-6h2v14H7V7zm4-4h2v18h-2V3zm4 9h2v9h-2v-9zm4-3h2v12h-2V9z"/>
            </svg>
            """,
            "settings.svg": """
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm8.94 3c-.46-4.17-3.77-7.48-7.94-7.94V1h-2v2.06C6.83 3.52 3.52 6.83 3.06 11H1v2h2.06c.46 4.17 3.77 7.48 7.94 7.94V23h2v-2.06c4.17-.46 7.48-3.77 7.94-7.94H23v-2h-2.06zM12 19c-3.87 0-7-3.13-7-7s3.13-7 7-7 7 3.13 7 7-3.13 7-7 7z"/>
            </svg>
            """,
            "download.svg": """
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
            </svg>
            """
        }
        
        for filename, svg_content in icons.items():
            icon_path = self.static_dir / "icons" / filename
            with open(icon_path, 'w', encoding='utf-8') as f:
                f.write(svg_content.strip())
    
    def generate_resource_manifest(self) -> Dict:
        """生成资源清单"""
        manifest = {
            "version": "1.0.0",
            "generated_at": str(Path.cwd()),
            "resources": {}
        }
        
        for name, resource in self.cdn_resources.items():
            local_path = self.static_dir / resource["local_path"]
            manifest["resources"][name] = {
                "original_url": resource["url"],
                "local_path": resource["local_path"],
                "exists": local_path.exists(),
                "size": local_path.stat().st_size if local_path.exists() else 0
            }
        
        return manifest
    
    def check_resources(self) -> Dict[str, bool]:
        """检查所有资源是否存在"""
        status = {}
        
        for name, resource in self.cdn_resources.items():
            local_path = self.static_dir / resource["local_path"]
            status[name] = local_path.exists()
        
        return status

def setup_static_resources():
    """设置静态资源"""
    manager = StaticResourceManager()
    
    print("🔧 设置本地静态资源...")
    
    # 创建本地CSS
    manager.create_local_css()
    print("✅ 本地CSS创建完成")
    
    # 创建本地图标
    manager.create_local_icons()
    print("✅ 本地图标创建完成")
    
    # 下载CDN资源
    print("📥 下载CDN资源...")
    results = manager.download_all_resources()
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"📊 下载结果: {success_count}/{total_count} 成功")
    
    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {name}")
    
    # 生成资源清单
    manifest = manager.generate_resource_manifest()
    manifest_path = manager.static_dir / "manifest.json"
    
    import json
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"📋 资源清单已生成: {manifest_path}")
    
    return manager

if __name__ == "__main__":
    setup_static_resources()
