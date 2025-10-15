import concurrent
from datetime import datetime
import os
import requests

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config.Config import Config

class UrlDetector(Config):
    DEFAULT_DOMAIN = 'harmonyos-lbs.kwailocallife.com'

    def checkUrlRegisteryStatus(self, domain: Optional[str] = DEFAULT_DOMAIN, paths: Optional[List[str]] = None):
        self.generateUrlReport(domain, paths)
        
    def generateUrlReport(self, domain: Optional[str] = DEFAULT_DOMAIN, paths: Optional[List[str]] = None):
        """
        遍历 basePath 下的所有模块，检查未注册的接口，并生成一份 Markdown 报告。
        """
        print("🚀 开始生成接口注册状态报告...")

        targetDomain = domain if domain is not None else self.DEFAULT_DOMAIN
        sanitizedDomain = targetDomain.rstrip('/')
        pathPrefix = f"https://{sanitizedDomain}"
        
        reportFile = self.docPath / '鸿蒙接口注册检查报告.md'

        if paths is not None and isinstance(paths, list):
            print("ℹ️  模式: 使用用户提供的路径列表进行检查。")
            print(f"ℹ️  模式: 精准测试。正在检查 {len(paths)} 个您提供的接口路径...")
            if not paths:
                print("✅ 提供的路径列表为空，无需检查。")
                return

            urlsToCheck = [f"{pathPrefix}{path}" for path in paths]
            unregistered = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futureToUrl = {executor.submit(self._checkSingleUrl, url): url for url in urlsToCheck}
                for future in concurrent.futures.as_completed(futureToUrl):
                    url, statusCode, reason = future.result()
                    if statusCode == 404:
                        unregistered.append(url.replace(pathPrefix, ""))
            
            # --- 生成简化版报告 ---
            if not unregistered:
                print("所有接口均已注册。")
            else:
                print(f"🔴 **发现 {len(unregistered)} 个未注册 (404) 的接口：**")
                for url in sorted(unregistered):
                    print(f"{url}")
        else:
            print(f"ℹ️  模式: 全量扫描。正在扫描 '{self.basePath.resolve()}' 下的所有模块...")
            self.moduleManager.discoverModules()
            allModules: List[Path] = [p.parent for p in self.basePath.rglob('**/src') if p.is_dir()]

            if not allModules:
                print("❌ 在当前目录下未找到任何包含 'src' 文件夹的模块。")
                return
            
            print(f"✅ 发现 {len(allModules)} 个模块，准备开始扫描...")

            liveModules: Dict[str, List[str]] = {}
            otherModules: Dict[str, List[str]] = {}

            for modulePath in allModules:
                moduleName = modulePath.name
                print(f"\n--- 正在处理模块: {moduleName} ---")
                urlPaths = self.moduleManager.findAllUrl(modulePath)
                if not urlPaths:
                    print("未找到接口，跳过。")
                    continue
                
                print(f"找到 {len(urlPaths)} 个接口，开始并发检查...")
                urlsToCheck = [f"{pathPrefix}{path}" for path in urlPaths]
                unregisteredUrls = []

                with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
                    futureToUrl = {executor.submit(self._checkSingleUrl, url): url for url in urlsToCheck}
                    for future in concurrent.futures.as_completed(futureToUrl):
                        url, statusCode, reason = future.result()
                        if statusCode == 404:
                            unregisteredUrls.append(url.replace(pathPrefix, ""))
                
                if unregisteredUrls:
                    print(f"发现 {len(unregisteredUrls)} 个未注册接口。")
                    if 'live' in moduleName.lower():
                        liveModules[moduleName] = sorted(unregisteredUrls)
                    else:
                        otherModules[moduleName] = sorted(unregisteredUrls)
                else:
                    print("所有接口均已注册。")

            with open(reportFile, 'w', encoding='utf-8') as f:
                f.write(f"# 接口注册状态检查报告 (全量扫描模式)\n\n")
                f.write(f"**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**检查域名:** `{sanitizedDomain}`\n\n---\n\n")
                if not liveModules and not otherModules:
                    f.write("🎉 **恭喜！在所有扫描的模块中，未发现任何未注册 (404) 的接口。**\n")
                if liveModules:
                    f.write("## 🟢 直播模块\n\n")
                    for name, urls in liveModules.items():
                        f.write(f"### 模块: `{name}`\n\n")
                        f.write(f"发现 **{len(urls)}** 个未注册接口：\n")
                        for url in urls: f.write(f"- `{url}`\n")
                        f.write("\n")
                if otherModules:
                    f.write("## 🔵 其他模块\n\n")
                    for name, urls in otherModules.items():
                        f.write(f"### 模块: `{name}`\n\n")
                        f.write(f"发现 **{len(urls)}** 个未注册接口：\n")
                        for url in urls: f.write(f"- `{url}`\n")
                        f.write("\n")
        
        print("\n✅ 报告生成完毕！")
        
    def _checkSingleUrl(self, url: str) -> Tuple[str, Optional[int], str]:
        """使用 HEAD 请求检查单个 URL 的状态。"""
        try:
            # 设置合理的超时时间 (例如10秒)
            # allow_redirects=True 可以处理重定向（例如 HTTP -> HTTPS）
            print(f"_checkSingleUrl {url}")
            response = requests.head(url, timeout=10, allow_redirects=True)
            # 如果服务器不支持 HEAD 方法 (返回 405)，则尝试用 GET 请求
            if response.status_code == 405:
                # 使用 stream=True，这样我们只获取响应头，不会下载整个响应体，效率更高
                response = requests.get(url, timeout=10, stream=True)
            
            return (url, response.status_code, response.reason)
        except requests.exceptions.Timeout:
            return (url, None, "请求超时 (Timeout)")
        except requests.exceptions.ConnectionError:
            return (url, None, "连接错误 (Connection Error)")
        except requests.exceptions.RequestException as e:
            return (url, None, f"请求异常: {e}")

    def checkModuleUrl(self, moduleName: str):
        print("--- 正在检查接口注册情况 ---")
        modulePath = self.basePath / moduleName
        urlPaths = self.moduleManager.findAllUrl(modulePath)
        if not urlPaths:
            print("未找到接口，跳过。")
            return
        sanitizedDomain = self.DEFAULT_DOMAIN
        pathPrefix = f"https://{sanitizedDomain}"
        urlsToCheck = [f"{pathPrefix}{path}" for path in urlPaths]
        unregistered = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futureToUrl = {executor.submit(self._checkSingleUrl, url): url for url in urlsToCheck}
            for future in concurrent.futures.as_completed(futureToUrl):
                url, statusCode, reason = future.result()
                if statusCode == 404:
                    unregistered.append(url.replace(pathPrefix, ""))
        
        if not unregistered:
            print("所有接口均已注册。")
        else:
            print(f"🔴 **发现 {len(unregistered)} 个未注册 (404) 的接口：**")
            for url in sorted(unregistered):
                print(f"{url}")