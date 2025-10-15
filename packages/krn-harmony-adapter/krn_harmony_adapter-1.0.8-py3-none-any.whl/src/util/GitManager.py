"""
Git操作管理模块
负责所有Git相关的操作，包括分支切换、文件检出、状态检查等
"""
import subprocess
from typing import Tuple, List, Optional


class GitManager:
    """Git操作管理器"""
    
    def __init__(self, basePath: str = "."):
        self.basePath = basePath
    
    def runCommand(self, command: str, cwd: Optional[str] = None) -> Tuple[bool, str]:
        """执行命令并返回结果"""
        try:
            if cwd is None:
                cwd = self.basePath
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                cwd=cwd
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)
    
    def getCurrentBranch(self) -> str:
        """获取当前分支名"""
        success, output = self.runCommand("git branch --show-current")
        if success:
            return output.strip()
        return "unknown"
    
    def branchExists(self, branchName: str) -> bool:
        """检查分支是否存在"""
        success, _ = self.runCommand(f"git show-ref --verify --quiet refs/heads/{branchName}")
        if not success:
            # 检查远程分支
            success, _ = self.runCommand(f"git show-ref --verify --quiet refs/remotes/origin/{branchName}")
        return success
    
    def checkoutFileFromBranch(self, branchName: str, filePath: str) -> Tuple[bool, str]:
        """从指定分支检出文件"""
        command = f"git checkout {branchName} -- {filePath}"
        return self.runCommand(command)
    
    def checkoutModuleFromBranch(self, branchName: str, moduleName: str) -> Tuple[bool, str]:
        """从指定分支检出整个模块"""
        if self.branchExists(branchName.replace("origin/", "")):
            command = f"git checkout {branchName} -- {moduleName}"
            success, output = self.runCommand(command)
            if success:
                return True, f"成功从 {branchName} 检出模块 {moduleName}"      
        return False, f"请确保 {branchName} 分支存在"
    
    def getFileContentFromBranch(self, branchName: str, filePath: str) -> Optional[str]:
        """从指定分支获取文件内容"""
        command = f"git show {branchName}:{filePath}"
        success, output = self.runCommand(command)
        if success:
            return output
        return None
    
    def getGitStatus(self, path: str = ".") -> Tuple[bool, str]:
        """获取Git状态"""
        return self.runCommand("git status --porcelain", cwd=path)
    
    def getGitDiff(self, filePath: str, staged: bool = False) -> str:
        """获取文件的git diff"""
        command = f"git diff {'--cached' if staged else ''} {filePath}"
        success, output = self.runCommand(command)
        return output if success else ""
    
    def addFile(self, filePath: str) -> Tuple[bool, str]:
        """添加文件到暂存区"""
        return self.runCommand(f"git add {filePath}")
    
    def commitChanges(self, message: str) -> Tuple[bool, str]:
        """提交更改"""
        return self.runCommand(f'git commit -m "{message}"')
    
    def resetFile(self, filePath: str, hard: bool = False) -> Tuple[bool, str]:
        """重置文件"""
        if hard:
            return self.runCommand(f"git checkout HEAD -- {filePath}")
        else:
            return self.runCommand(f"git restore {filePath}")
    
    def resetModule(self, modulePath: str) -> Tuple[bool, str]:
        """重置整个模块"""
        return self.runCommand(f"git checkout HEAD -- {modulePath}")
    
    def getModifiedFiles(self, path: str = ".") -> List[str]:
        """获取修改的文件列表"""
        success, output = self.getGitStatus(path)
        if not success:
            return []
        
        modified_files = []
        for line in output.strip().split('\n'):
            if line.strip():
                # 解析git status输出格式
                status = line[:2]
                filePath = line[3:]
                if 'M' in status or 'A' in status or 'D' in status:
                    modified_files.append(filePath)
        
        return modified_files
    
    def hasUncommittedChanges(self, path: str = ".") -> bool:
        """检查是否有未提交的更改"""
        success, output = self.getGitStatus(path)
        return success and output.strip() != ""
    
    def getFileDiffWithBranch(self, filePath: str, branchName: str) -> str:
        """获取文件与指定分支的差异"""
        command = f"git diff {branchName} -- {filePath}"
        success, output = self.runCommand(command)
        return output if success else ""
    
    def listModulesInBranch(self, branchName: str) -> List[str]:
        """列出指定分支中的模块"""
        command = f"git ls-tree -d --name-only {branchName}"
        success, output = self.runCommand(command)
        if success:
            return [line.strip() for line in output.strip().split('\n') if line.strip()]
        return []
    
    def getBranchCommitHash(self, branchName: str) -> Optional[str]:
        """获取分支的最新提交哈希"""
        command = f"git rev-parse {branchName}"
        success, output = self.runCommand(command)
        if success:
            return output.strip()
        return None

    def getLatestDevBranch(self) -> str:
        """
        获取指定远程仓库上，名称以 'dev' 开头的最新（最后提交）的分支。
        """
        print(f"正在从远程获取最新信息...")
        # 1. 更新本地的远程分支列表，并清理掉远程已删除的分支
        self.runCommand(f'git fetch origin --prune')
        
        print("正在获取所有远程分支列表...")
        # 2. 获取所有远程分支的引用名称
        # 使用 --format 来获取干净的输出，避免处理 'HEAD -> ...' 等无关信息
        success, output = self.runCommand(
            f"git branch -r --format='%(refname:short)'"
        )

        # 3. 筛选出所有以 'dev' 开头的分支
        dev_branch_prefix = f"origin/dev"
        dev_branches = [
            branch for branch in output.splitlines() if branch.startswith(dev_branch_prefix)
        ]
        
        if not dev_branches:
            print("未找到任何以 'dev' 开头的远程分支。")
            return "master"
            
        print(f"找到 {len(dev_branches)} 个 dev 分支: {dev_branches}")

        # 4. 遍历 dev 分支，找出最后提交时间戳最新的那个
        latest_timestamp = -1
        latest_dev_branch = None

        print("正在检查每个 dev 分支的最后提交时间...")
        for branch in dev_branches:
            # 使用 git log 获取该分支最后一次提交的 committer date 的 UNIX 时间戳 (%ct)
            success, timestamp_str = self.runCommand(f'git log -1 --format=%ct {branch}')
            try:
                timestamp = int(timestamp_str)
                if timestamp > latest_timestamp:
                    latest_timestamp = timestamp
                    latest_dev_branch = branch
            except Exception as e:
                print(f"警告: 无法解析分支 '{branch}' 的时间戳: '{timestamp_str}', {e}")
                continue
                
        if latest_dev_branch:
            # 移除远程名前缀，例如从 'origin/dev/my-feature' 变为 'dev/my-feature'
            return latest_dev_branch.replace(f"origin/", "", 1)
        
        return "master"