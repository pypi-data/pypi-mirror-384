#!/usr/bin/env python3
"""
重构后的鸿蒙适配器主文件
采用模块化架构，功能清晰分离
"""
import concurrent.futures
import sys
import os
from typing import Dict, Any, List, Optional


# 添加模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.check.Check import Check
from modules.adapt.Adapter import Adapter
from modules.sync.Sync import Sync
from modules.doc.UrlDetector import UrlDetector
from modules.doc.DocGenerator import DocGenerator


"""鸿蒙适配器主类"""
class Main:
    
    def __init__(self, basePath: str = "."):
        self.basePath = basePath
        
        # 初始化各个模块
        self.syncer = Sync()
        self.checker = Check()
        self.adapter = Adapter()
        self.urlDetetor = UrlDetector()
        self.docGenerator = DocGenerator()
    
    def syncMissingModules(self):
        """功能1: 自动同步master分支有，但是当前分支没有的模块"""
        self.syncer.syncMissingModules()
    
    def checkAllModulesAdaptation(self) -> Dict[str, Any]:
        """功能2: 自动识别哪些模块没有适配鸿蒙"""
        return self.checker.checkAllModulesAdaptation()

    def adaptSingleModule(self, moduleName: str, aiType: str):
        """功能3: 按照规定一键适配指定模块"""
        print(f"🔧 适配模块 - {moduleName}")
        print("=" * 50)
        self.adapter.adaptSingleModule(moduleName, aiType)
        self.urlDetetor.checkModuleUrl(moduleName)
    
    def adaptBatchModules(self, moduleType: str = "all", aiType: str = ""):
        """功能4：批量适配模块"""
        print(f"🔧 批量适配 - {moduleType}")
        self.adapter.adaptBatchModules(moduleType, aiType)
    
    def checkUrlRegisteryStatus(self,
                                      domain: Optional[str] = 'harmonyos-lbs.kwailocallife.com', 
                                      paths: Optional[List[str]] = None):
        """功能6：检测接口注册状态"""
        print(f"🔧 检查接口注册状态")
        self.urlDetetor.checkUrlRegisteryStatus(domain, paths)
    
    def generateDocumentation(self) -> bool:
        """功能7：生成文档"""
        return self.docGenerator.generateAllDocs()
    
    def interactive_menu(self) -> None:
        """交互式菜单"""
        while True:
            print("\n" + "=" * 60)
            print("🚀 鸿蒙适配器")
            print("=" * 60)
            print("1. 同步缺失模块")
            print("2. 检查所有模块适配状态")
            print("3. 适配指定模块")
            print("4. 批量适配模块")
            print("5. 检查接口注册状态")
            print("6. 生成文档")
            print("0. 退出")
            print("=" * 60)
            
            try:
                choice = input("请选择功能 (0-6): ").strip()
                
                if choice == '0':
                    print("👋 再见!")
                    break
                elif choice == '1':
                    self.syncMissingModules()
                elif choice == '2':
                    self.checkAllModulesAdaptation()
                elif choice == '3':
                    moduleName = input("请输入模块名: ").strip()
                    aiType = input("请输入AI类型 (可选, kwaipilot/openai): ").strip()
                    if moduleName:
                        self.adaptSingleModule(moduleName, aiType)
                elif choice == '4':
                    print("批量适配选项:")
                    print("1. 所有未适配模块")
                    print("2. 仅直播Bundle")
                    print("3. 仅非直播Bundle")
                    batch_choice = input("请选择 (1-3): ").strip()
                    aiType = input("请输入AI类型 (可选, kwaipilot/openai): ").strip()
                    
                    if batch_choice == '1':
                        self.adaptBatchModules("all", aiType)
                    elif batch_choice == '2':
                        self.adaptBatchModules("live", aiType)
                    elif batch_choice == '3':
                        self.adaptBatchModules("non_live", aiType)
                elif choice == '5':
                    self.checkUrlRegisteryStatus()
                elif choice == '6':
                    self.generateDocumentation()
                else:
                    print("❌ 无效选择，请重新输入")
                    
            except KeyboardInterrupt:
                print("\n👋 再见!")
                break
            except Exception as e:
                print(f"❌ 操作失败: {e}")


def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 命令行模式
        adapter = Main()
        command = sys.argv[1]
        
        if command == "sync":
            adapter.syncMissingModules()
        elif command == "check":
            adapter.checkAllModulesAdaptation()
        elif command == "adapt" and len(sys.argv) > 2:
            for m in sys.argv[2:]:
                adapter.adaptSingleModule(m, "")
        elif command == "batch":
            moduleType = sys.argv[2] if len(sys.argv) > 2 else "all"
            aiType = sys.argv[3] if len(sys.argv) > 3 else ""
            adapter.adaptBatchModules(moduleType, aiType)
        elif command == "url":
            if (len(sys.argv) >= 2):
                if (sys.argv[2].startswith('/')):
                    adapter.checkUrlRegisteryStatus('harmonyos-lbs.kwailocallife.com', sys.argv[2:])
                else:
                    adapter.checkUrlRegisteryStatus(sys.argv[2], sys.argv[3:])
            else:
                adapter.checkUrlRegisteryStatus()
        elif command == "doc":
            adapter.generateDocumentation()
        else:
            print("用法: python harmony_adapter_refactored.py [sync|check|adapt <module>|batch [all|live|non_live]|doc|url]")
    else:
        # 交互式模式
        adapter = Main()
        adapter.interactive_menu()


if __name__ == "__main__":
    main()