"""
备份管理模块
负责备份和恢复Harmony相关的文件和配置
"""
from collections.abc import Set
import os
import json
import shutil
import re
import textwrap
from typing import Any, Dict, Set, List, Tuple

from util.GitManager import GitManager
from util.HarmonyDetector import HarmonyDetector
from util.merge.CodeMerger import CodeMerger

"""备份管理器"""
class BackupManager(GitManager, HarmonyDetector):
    
    def __init__(self, basePath = "."):
        super().__init__(basePath = basePath)
        self.backupDir = ".harmony_backup"
        self.codeMerger = CodeMerger()
    
    def create_backup_directory(self, module_path: str) -> str:
        """创建备份目录"""
        backup_path = os.path.join(module_path, self.backupDir)
        os.makedirs(backup_path, exist_ok=True)
        return backup_path
    
    def backup_harmony_content(self, module_path: str, from_branch: str = None) -> Dict[str, Any]:
        """备份Harmony相关内容"""
        backup_info = {
            'package_json': {},
            'babel_config': {},
            'harmony_files': {},
            'backup_path': ""
        }
        
        backup_path = self.create_backup_directory(module_path)
        backup_info['backup_path'] = backup_path
        
        if from_branch:
            # 从指定分支备份
            backup_info = self._backup_from_branch(module_path, from_branch, backup_info)
        else:
            # 从当前工作区备份
            backup_info = self._backup_from_current(module_path, backup_info)
        
        return backup_info
    
    def _backup_from_branch(self, module_path: str, branch_name: str, backup_info: Dict[str, Any]) -> Dict[str, Any]:
        """从指定分支备份Harmony内容"""
        print(f"📍 从{branch_name}分支备份Harmony内容...")
        
        # 备份package.json
        package_json_path = os.path.join(module_path, "package.json").removeprefix(os.path.abspath(self.basePath) + "/")
        print("📍 备份package.json配置...")
        if os.path.exists(package_json_path):
            branch_content = self.getFileContentFromBranch(branch_name, package_json_path)
            if branch_content:
                harmonyConfig = self.extractHarmonyDependencies(branch_content)
                if harmonyConfig['dependencies'] or harmonyConfig['devDependencies'] or harmonyConfig['resolutions']:
                    backup_info['package_json'] = harmonyConfig
                    print(f"✅ 备份package.json配置: {len(harmonyConfig['dependencies'])}个依赖")
        
        # 备份babel.config.js
        babel_config_path = os.path.join(module_path, "babel.config.js").removeprefix(os.path.abspath(self.basePath) + "/")
        if os.path.exists(babel_config_path):
            branch_content = self.getFileContentFromBranch(branch_name, babel_config_path)
            if branch_content and self.containsHarmonyContent(branch_content):
                backup_file_path = os.path.join(backup_info['backup_path'], "babel.config.js")
                with open(backup_file_path, 'w', encoding='utf-8') as f:
                    f.write(branch_content)
                backup_info['babel_config']['backed_up'] = True
                print(f"✅ 备份babel.config.js配置")
        
        # 备份Harmony相关的代码文件
        harmony_files = self._find_harmony_files_in_branch(module_path, branch_name)
        print(f"📍 准备从{branch_name}分支备份harmony文件: {len(harmony_files)}个文件")
        for file_path in harmony_files:
            branch_content = self.getFileContentFromBranch(branch_name, file_path)
            if branch_content and self.containsHarmonyContent(branch_content):
                backup_file_path = os.path.join(backup_info['backup_path'], os.path.basename(file_path))
                with open(backup_file_path, 'w', encoding='utf-8') as f:
                    f.write(branch_content)
                backup_info['harmony_files'][file_path] = backup_file_path
                print(f"📍 从{branch_name}分支备份harmony文件: {file_path}")
        
        return backup_info
    
    def _backup_from_current(self, module_path: str, backup_info: Dict[str, Any]) -> Dict[str, Any]:
        """从当前工作区备份Harmony内容"""
        print(f"📍 从当前工作区备份Harmony内容...")
        
        # 备份package.json
        package_json_path = os.path.join(module_path, "package.json")
        if os.path.exists(package_json_path):
            with open(package_json_path, 'r', encoding='utf-8') as f:
                content = f.read()
            harmonyConfig = self.extractHarmonyDependencies(content)
            if harmonyConfig['dependencies'] or harmonyConfig['devDependencies'] or harmonyConfig['resolutions']:
                backup_info['package_json'] = harmonyConfig
                print(f"✅ 备份package.json配置: {len(harmonyConfig['dependencies'])}个依赖")
        
        # 备份babel.config.js
        babel_config_path = os.path.join(module_path, "babel.config.js")
        if os.path.exists(babel_config_path):
            with open(babel_config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if self.containsHarmonyContent(content):
                backup_file_path = os.path.join(backup_info['backup_path'], "babel.config.js")
                shutil.copy2(babel_config_path, backup_file_path)
                backup_info['babel_config']['backed_up'] = True
                print(f"✅ 备份babel.config.js配置")
        
        # 备份Harmony相关的代码文件
        harmony_files = self._find_harmony_files_in_current(module_path)
        for file_path in harmony_files:
            full_path = os.path.join(module_path, file_path)
            if os.path.exists(full_path):
                backup_file_path = os.path.join(backup_info['backup_path'], os.path.basename(file_path))
                shutil.copy2(full_path, backup_file_path)
                backup_info['harmony_files'][file_path] = backup_file_path
                print(f"📍 备份harmony文件: {file_path}")
        
        return backup_info
    
    def _find_harmony_files_in_branch(self, module_path: str, branch_name: str) -> List[str]:
        """在指定分支中查找Harmony相关文件"""
        harmony_files = []
        
        # 获取分支中的所有文件
        command = f"git ls-tree -r --name-only {branch_name} -- {module_path}"
        success, output = self.runCommand(command)
        
        if success:
            files = output.strip().split('\n')
            for file_path in files:
                if file_path.strip() and (file_path.endswith('.ts') or file_path.endswith('.tsx') or 
                                        file_path.endswith('.js') or file_path.endswith('.jsx')):
                    # 检查文件内容是否包含Harmony相关内容
                    content = self.getFileContentFromBranch(branch_name, file_path)
                    print(f"检查文件: {file_path}, 包含Harmony: {self.containsHarmonyContent(content)}")
                    if content and (self.containsHarmonyContent(content) or 
                                  self.checkGitDiffForHarmony(
                                      self.getFileDiffWithBranch(file_path, branch_name))):
                        harmony_files.append(file_path)
        
        return harmony_files
    
    def _find_harmony_files_in_current(self, module_path: str) -> List[str]:
        """在当前工作区中查找Harmony相关文件"""
        harmony_files = []
        
        for root, dirs, files in os.walk(module_path):
            # 跳过备份目录和node_modules
            dirs[:] = [d for d in dirs if d not in [self.backupDir, 'node_modules', '.git']]
            
            for file in files:
                if file.endswith(('.ts', '.tsx', '.js', '.jsx')):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, module_path)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 检查文件内容或git diff是否包含Harmony相关内容
                        if (self.containsHarmonyContent(content) or 
                            self.checkGitDiffForHarmony(
                                self.getGitDiff(rel_path))):
                            harmony_files.append(rel_path)
                    except Exception as e:
                        print(f"⚠️  读取文件失败 {file_path}: {e}")
        
        return harmony_files
    
    def restore_harmony_content(self, module_path: str, backup_info: Dict[str, Any]) -> bool:
        """恢复Harmony相关内容"""
        success = True
        
        try:
            # 恢复package.json
            if backup_info.get('package_json'):
                success &= self._restore_package_json(module_path, backup_info['package_json'])
            
            # 恢复babel.config.js
            if backup_info.get('babel_config', {}).get('backed_up'):
                success &= self._restore_babel_config(module_path, backup_info['backup_path'])
            
            # 恢复Harmony代码文件
            if backup_info.get('harmony_files'):
                success &= self._restore_harmony_files(module_path, backup_info['harmony_files'])
            
        except Exception as e:
            print(f"❌ 恢复Harmony内容时出错: {e}")
            success = False
        
        return success
    
    def _restore_package_json(self, module_path: str, harmonyConfig: Dict[str, Any]) -> bool:
        """恢复package.json中的Harmony配置"""
        package_json_path = os.path.join(module_path, "package.json")
        
        try:
            # 读取当前package.json
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            # 恢复dependencies
            if harmonyConfig.get('dependencies'):
                if 'dependencies' not in package_data:
                    package_data['dependencies'] = {}
                package_data['dependencies'].update(harmonyConfig['dependencies'])
            
            # 恢复devDependencies
            if harmonyConfig.get('devDependencies'):
                if 'devDependencies' not in package_data:
                    package_data['devDependencies'] = {}
                package_data['devDependencies'].update(harmonyConfig['devDependencies'])
            
            # 恢复resolutions
            if harmonyConfig.get('resolutions'):
                if 'resolutions' not in package_data:
                    package_data['resolutions'] = {}
                package_data['resolutions'].update(harmonyConfig['resolutions'])
            
            # 写回文件
            with open(package_json_path, 'w', encoding='utf-8') as f:
                json.dump(package_data, f, indent=4, ensure_ascii=False)
            
            print("✅ 恢复package.json配置")
            return True
            
        except Exception as e:
            print(f"❌ 恢复package.json失败: {e}")
            return False
    
    def _restore_babel_config(self, module_path: str, backup_path: str) -> bool:
        """恢复babel.config.js配置（只恢复harmony相关的配置）"""
        babel_config_path = os.path.join(module_path, "babel.config.js")
        backup_babel_path = os.path.join(backup_path, "babel.config.js")
        
        try:
            if os.path.exists(backup_babel_path) and os.path.exists(babel_config_path):
                # 读取当前文件和备份文件
                with open(babel_config_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
                
                with open(backup_babel_path, 'r', encoding='utf-8') as f:
                    backup_content = f.read()
                
                # 智能合并harmony相关的配置
                merged_content = self._merge_babel_config_intelligently(current_content, backup_content)
                
                # 写回文件
                with open(babel_config_path, 'w', encoding='utf-8') as f:
                    f.write(merged_content)
                
                print("✅ 恢复babel.config.js配置（只恢复harmony相关部分）")
                return True
        except Exception as e:
            print(f"❌ 恢复babel.config.js失败: {e}")
        
        return False
    
    def _restore_harmony_files(self, module_path: str, harmony_files: Dict[str, str]) -> bool:
        """恢复Harmony代码文件（只恢复harmony相关的代码块和import）"""
        success = True
        module_name = os.path.basename(module_path)
        
        for original_path, backup_path in harmony_files.items():
            try:
                # 处理路径：如果original_path已经包含模块名，需要去掉
                if original_path.startswith(module_name + '/'):
                    # 去掉模块名前缀
                    relative_path = original_path[len(module_name) + 1:]
                    full_original_path = os.path.join(module_path, relative_path)
                else:
                    # 如果不包含模块名，直接使用
                    full_original_path = os.path.join(module_path, original_path)
                
                if os.path.exists(backup_path) and os.path.exists(full_original_path):
                    # 读取当前文件和备份文件
                    with open(full_original_path, 'r', encoding='utf-8') as f:
                        current_content = f.read()
                    
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        backup_content = f.read()
                    
                    # 智能合并harmony相关的代码块和import
                    merged_content = self.codeMerger.merge_code(current_content, backup_content)
                    
                    # 写回文件
                    with open(full_original_path, 'w', encoding='utf-8') as f:
                        f.write(merged_content)
                    
                    print(f"✅ 智能恢复harmony内容: {os.path.relpath(full_original_path, module_path)}")
                elif os.path.exists(backup_path):
                    # 如果当前文件不存在，直接复制备份文件
                    os.makedirs(os.path.dirname(full_original_path), exist_ok=True)
                    shutil.copy2(backup_path, full_original_path)
                    print(f"✅ 恢复harmony文件: {original_path} -> {os.path.relpath(full_original_path, module_path)}")
                else:
                    print(f"⚠️  备份文件不存在: {backup_path}")
                    success = False
                    
            except Exception as e:
                print(f"❌ 恢复文件失败 {original_path}: {e}")
                success = False
        
        return success
    
    def cleanup_backup(self, module_path: str) -> bool:
        """清理备份目录"""
        backup_path = os.path.join(module_path, self.backupDir)
        
        try:
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
                print("🧹 清理备份目录")
                return True
        except Exception as e:
            print(f"⚠️  清理备份目录失败: {e}")
        
        return False
    
    def _merge_babel_config_intelligently(self, current_content: str, backup_content: str) -> str:
       # --- 步骤 1: 合并 Aliases ---
        current_aliases = self._extract_aliases(current_content)
        backup_aliases = self._extract_aliases(backup_content)
        kds_aliases_from_backup = {k: v for k, v in backup_aliases.items() if "'@kds" in v or '"@kds' in v}

        final_aliases_map = current_aliases.copy()
        final_aliases_map.update(kds_aliases_from_backup)

        # 查找原始的 alias 块，用于替换和参考格式
        alias_block_start_match = re.search(r"alias\s*:\s*\{", current_content)
        content_after_alias_merge = current_content

        if alias_block_start_match:
            start_pos, level, end_pos = alias_block_start_match.end(), 1, -1
            for i, char in enumerate(current_content[start_pos:]):
                if char == '{':
                    level += 1
                elif char == '}':
                    level -= 1
                if level == 0:
                    end_pos = start_pos + i
                    break

            if end_pos != -1:
                original_alias_block = current_content[alias_block_start_match.start():end_pos + 1]

                line_start_pos = current_content.rfind('\n', 0, alias_block_start_match.start()) + 1
                block_indent = current_content[line_start_pos:alias_block_start_match.start()]
                item_indent = block_indent + "  "

                new_alias_lines = [f"{item_indent}{v}" for k, v in sorted(final_aliases_map.items())]
                new_inner_content = ",\n".join(new_alias_lines)

                new_alias_block = f"alias: {{\n{new_inner_content}\n{block_indent}}}"
                content_after_alias_merge = current_content.replace(original_alias_block, new_alias_block, 1)

        # --- 步骤 2: 合并 Plugins ---
        # [BUG FIX]: 从上一步修改后的 `content_after_alias_merge` 中提取插件，而不是原始的 `current_content`
        current_plugins = self._extract_babel_plugins(content_after_alias_merge)
        backup_plugins = self._extract_babel_plugins(backup_content)
        harmony_plugins = {p for p in backup_plugins if "harmony" in p}

        final_plugins_map = {p.split(',')[0].strip().strip('[').strip("'").strip('"'): p for p in current_plugins}
        for p in harmony_plugins:
            key = p.split(',')[0].strip().strip('[').strip("'").strip('"')
            final_plugins_map[key] = p

        final_plugins = [final_plugins_map[key] for key in sorted(final_plugins_map.keys())]

        plugins_block_start_match = re.search(r"plugins\s*:\s*\[", content_after_alias_merge)
        final_content = content_after_alias_merge

        if plugins_block_start_match:
            start_pos, level, end_pos = plugins_block_start_match.end(), 1, -1
            for i, char in enumerate(content_after_alias_merge[start_pos:]):
                if char == '[':
                    level += 1
                elif char == ']':
                    level -= 1
                if level == 0:
                    end_pos = start_pos + i
                    break

            if end_pos != -1:
                original_plugins_block = content_after_alias_merge[plugins_block_start_match.start():end_pos + 1]

                line_start_pos = content_after_alias_merge.rfind('\n', 0, plugins_block_start_match.start()) + 1
                block_indent = content_after_alias_merge[line_start_pos:plugins_block_start_match.start()]
                item_indent = block_indent + "  "

                new_plugins_lines = []
                for plugin in final_plugins:
                    indented_lines = [f"{item_indent}{line}" for line in plugin.split('\n')]
                    new_plugins_lines.append("\n".join(indented_lines))

                new_inner_content = ",\n".join(new_plugins_lines)
                new_plugins_block = f"plugins: [\n{new_inner_content}\n{block_indent}]"

                final_content = content_after_alias_merge.replace(original_plugins_block, new_plugins_block, 1)

        return final_content

    
    def _extract_babel_plugins(self, content: str) -> List[str]:
        """使用括号计数法来稳健地提取整个 plugins 块。"""
        plugins = []
        match = re.search(r"plugins\s*:\s*\[", content)
        if not match: return []

        start_pos, level, end_pos = match.end(), 1, -1
        for i, char in enumerate(content[start_pos:]):
            if char == '[':
                level += 1
            elif char == ']':
                level -= 1
            if level == 0:
                end_pos = start_pos + i
                break
        if end_pos == -1: return []

        plugins_content = content[start_pos:end_pos].strip()

        item_start, level = 0, 0
        for i, char in enumerate(plugins_content):
            if char in '[{':
                level += 1
            elif char in ']}':
                level -= 1

            if char == ',' and level == 0:
                plugin_str = plugins_content[item_start:i].strip()
                if plugin_str: plugins.append(textwrap.dedent(plugin_str))
                item_start = i + 1

        last_plugin_str = plugins_content[item_start:].strip()
        if last_plugin_str: plugins.append(textwrap.dedent(last_plugin_str))

        return plugins

    def _extract_aliases(self, content: str) -> Dict[str, str]:
        """使用括号计数法来稳健地提取整个 alias 块。"""
        aliases = {}
        match = re.search(r"alias\s*:\s*\{", content)
        if not match: return aliases

        start_pos, level, end_pos = match.end(), 1, -1
        for i, char in enumerate(content[start_pos:]):
            if char == '{':
                level += 1
            elif char == '}':
                level -= 1
            if level == 0:
                end_pos = start_pos + i
                break
        if end_pos == -1: return aliases

        alias_content = content[start_pos:end_pos].strip()

        key_pattern = re.compile(r"(?:(['\"])(.*?)\1|([a-zA-Z_$][\w$]*))\s*:")
        matches = list(key_pattern.finditer(alias_content))
        for i, match in enumerate(matches):
            key = match.group(2) if match.group(2) is not None else match.group(3)
            if key is None: continue
            entry_start_pos = match.start()
            entry_end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(alias_content)
            full_entry = alias_content[entry_start_pos:entry_end_pos].strip()
            if full_entry.endswith(','): full_entry = full_entry[:-1].strip()
            aliases[key] = textwrap.dedent(full_entry).strip()
        return aliases
