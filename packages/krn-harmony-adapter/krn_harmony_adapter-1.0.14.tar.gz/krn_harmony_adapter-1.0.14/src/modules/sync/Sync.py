from config.Config import Config

from typing import List, Tuple

"""模块同步器"""
class Sync(Config):

    def syncMissingModules(self) -> bool:
        print("🔄 步骤1: 同步缺失模块")
        print("=" * 50)
        
        currentBranch = self.gitManager.getCurrentBranch()
        print(f"📍 当前分支: {currentBranch}")
        
        # 查找缺失的模块
        missing_modules = self._findMissingModules()
        
        if not missing_modules:
            print("✅ 所有模块都已同步，无需操作")
            return True
        
        print(f"📦 发现 {len(missing_modules)} 个需要同步的模块:")
        for module in missing_modules:
            print(f"  - {module}")
        
        # 询问用户确认
        confirm = input(f"\n是否同步这 {len(missing_modules)} 个模块到当前分支 '{currentBranch}'? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ 用户取消同步操作")
            return False
        
        # 执行同步
        success, synced_modules = self._sync(missing_modules)
        
        if success:
            print(f"✅ 成功同步 {len(synced_modules)} 个模块")
        else:
            print(f"⚠️  部分模块同步失败，成功同步 {len(synced_modules)}/{len(missing_modules)} 个模块")
        
        return success
    
    def _findMissingModules(self) -> List[str]:
        """查找目标分支有但当前分支没有的模块"""
        currentModules = set(self.moduleManager.discoverModules())
        
        # 获取目标分支的模块列表
        targetModules = set()
        
        # 尝试多个可能的master分支名称
        masterBranch = self.gitManager.getLatestDevBranch()
        
        for branch in masterBranch:
            if self.gitManager.branchExists(branch.replace("origin/", "")):
                branch_modules = self.gitManager.listModulesInBranch(branch)
                # 过滤出有效的模块
                for module in branch_modules:
                    if not module.startswith('.') and module not in {'doc', 'rule', 'script', 'scriptForHarmony'}:
                        targetModules.add(module)
                break
        
        # 找出缺失的模块
        missingModules = targetModules - currentModules
        return sorted(list(missingModules))
    
    def _sync(self, missingModules: List[str]) -> Tuple[bool, List[str]]:
        """同步缺失的模块"""
        if not missingModules:
            return True, []
        
        syncedModules = []
        sourceBranch = self.gitManager.getLatestDevBranch()
        
        for moduleName in missingModules:
            print(f"📦 同步模块: {moduleName}")
            
            success, output = self.gitManager.checkoutModuleFromBranch(sourceBranch, moduleName)
            if success:
                syncedModules.append(moduleName)
                print(f"✅ 成功同步模块: {moduleName}")
            else:
                print(f"❌ 同步模块失败: {moduleName} - {output}")
        
        # 提交同步的模块
        if syncedModules:
            self.gitManager.addFile(".")
            commitMessage = f"同步模块: {', '.join(syncedModules)}"
            success, output = self.gitManager.commitChanges(commitMessage)
            if success:
                print(f"✅ 提交同步结果: {len(syncedModules)}个模块")
            else:
                print(f"⚠️ 提交失败: {output}")
        
        return len(syncedModules) == len(missingModules), syncedModules
