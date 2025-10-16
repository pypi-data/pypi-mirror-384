"""
Harmony内容检测模块
负责检测文件中的Harmony相关内容，包括依赖、代码块、条件判断等
"""
import re
import json
from typing import List, Dict, Any


class HarmonyDetector:
    """Harmony内容检测器"""

    # Harmony相关的模式
    harmony_patterns = [
            r'harmony',
            r'Harmony',
        ]
    
    # Harmony依赖的模式
    harmony_dependency_patterns = [
        r'harmony',
        r'auto-adapt-harmony',
        r'@locallife/auto-adapt-harmony'
    ]
    
    
    def containsHarmonyContent(self, content: str) -> bool:
        """检查内容是否包含Harmony相关内容"""
        if not content:
            return False
        
        for pattern in self.harmony_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def isHarmonyDependency(self, depName: str, depVersion: str = "") -> bool:
        """检查依赖是否是Harmony相关的"""
        full_dep = f"{depName} {depVersion}".lower()
        
        for pattern in self.harmony_dependency_patterns:
            if re.search(pattern, full_dep, re.IGNORECASE):
                return True
        return False
    
    def extractHarmonyDependencies(self, package_json_content: str) -> Dict[str, Any]:
        """从package.json中提取Harmony相关的依赖"""
        try:
            package_data = json.loads(package_json_content)
        except json.JSONDecodeError:
            return {}
        
        harmonyConfig = {
            'dependencies': {},
            'devDependencies': {},
            'resolutions': {}
        }
        
        # 检查dependencies
        dependencies = package_data.get('dependencies', {})
        for depName, depVersion in dependencies.items():
            if self.isHarmonyDependency(depName, str(depVersion)):
                harmonyConfig['dependencies'][depName] = depVersion
        
        # 检查devDependencies
        dev_dependencies = package_data.get('devDependencies', {})
        for depName, depVersion in dev_dependencies.items():
            if self.isHarmonyDependency(depName, str(depVersion)):
                harmonyConfig['devDependencies'][depName] = depVersion
        
        # 检查resolutions
        resolutions = package_data.get('resolutions', {})
        for depName, depVersion in resolutions.items():
            if self.isHarmonyDependency(depName, str(depVersion)):
                harmonyConfig['resolutions'][depName] = depVersion
        
        return harmonyConfig

    def findHarmonyConditionalBlocks(self, content: str) -> List[Dict[str, Any]]:
        """查找Harmony条件判断代码块"""
        harmony_blocks = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # 查找Platform.OS相关的条件判断
            if re.search(r'Platform\.OS.*harmony', line, re.IGNORECASE):
                harmony_blocks.append({
                    'line_number': i + 1,
                    'content': line.strip(),
                    'type': 'platform_condition'
                })
            
            # 查找其他Harmony相关的条件判断
            elif re.search(r'harmony.*\?|harmony.*:', line, re.IGNORECASE):
                harmony_blocks.append({
                    'line_number': i + 1,
                    'content': line.strip(),
                    'type': 'ternary_condition'
                })
        
        return harmony_blocks
    
    def extractHarmonyImports(self, content: str) -> List[str]:
        """提取Harmony相关的导入语句"""
        harmony_imports = []
        lines = content.split('\n')
        
        for line in lines:
            if line.strip().startswith('import') and self.containsHarmonyContent(line):
                harmony_imports.append(line.strip())
        
        return harmony_imports
    
    def checkGitDiffForHarmony(self, git_diff: str) -> bool:
        """检查git diff中是否包含Harmony相关的修改"""
        if not git_diff:
            return False
        
        # 检查删除的行（以-开头）是否包含harmony内容
        for line in git_diff.split('\n'):
            if line.startswith('-') and self.containsHarmonyContent(line[1:]):
                return True
        
        return False
