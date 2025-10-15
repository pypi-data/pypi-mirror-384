import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
import time
from typing import Any, Dict, List
from packaging import version
from importlib import resources as res

from config.Config import Config
from util.ai.AiType import AiType

class Adapter(Config):

    agreeMaster: bool = False

    def __init__(self):
        super().__init__()

    def adaptBatchModules(self, moduleType: str = "all", aiType: str = "") -> bool:
        """批量适配模块"""
        print(f"🔧 批量适配模块 - {moduleType}")
        print("=" * 50)
        
        moduleManager = self.moduleManager
        categorized = moduleManager.categorizeModulesByAdaptation(moduleManager.discoverModules())
        not_adapted = categorized['not_adapted']
        
        if not not_adapted:
            print("✅ 所有模块都已适配")
            return True
        
        # 根据类型筛选模块
        modules_to_adapt = []
        if moduleType == "live":
            modules_to_adapt = [m for m in not_adapted if 'live' in m['moduleName'].lower()]
            print(f"📦 准备适配 {len(modules_to_adapt)} 个直播Bundle")
        elif moduleType == "non_live":
            modules_to_adapt = [m for m in not_adapted if 'live' not in m['moduleName'].lower()]
            print(f"📦 准备适配 {len(modules_to_adapt)} 个非直播Bundle")
        else:
            modules_to_adapt = not_adapted
            print(f"📦 准备适配 {len(modules_to_adapt)} 个模块")
        
        if not modules_to_adapt:
            print(f"✅ 没有需要适配的{moduleType}模块")
            return True
        
        # 显示模块列表
        for module in modules_to_adapt:
            print(f"  - {module['moduleName']}")
        
        # 询问用户确认
        confirm = input(f"\n是否开始批量适配这 {len(modules_to_adapt)} 个模块? (Y/n): ")
        if confirm.lower() == 'n':
            print("❌ 用户取消批量适配")
            return False
        
        # 执行批量适配
        success_count = 0
        for module in modules_to_adapt:
            print(f"\n🔧 适配模块: {module['moduleName']}")
            if self.adaptSingleModule(module['moduleName'], aiType):
                success_count += 1
        
        print(f"\n✅ 批量适配完成: {success_count}/{len(modules_to_adapt)} 个模块适配成功")
        return success_count == len(modules_to_adapt)

    def adaptSingleModule(self, moduleName: str, aiType: str) -> bool:
        status = self.moduleManager.checkModuleAdaptationStatus(moduleName)
        if self.updateModuleCode(moduleName, aiType) == False:
            return;
        if status['is_adapted'] == False:
            self.startAdapt(moduleName)
        
        # 执行yarn命令安装依赖
        self._runYarnInstall(self.basePath / moduleName)

        
    def startAdapt(self, moduleName: str) -> bool:
        print(f"🔧 开始适配模块 {moduleName} 到鸿蒙...")
        
        modulePath = self.basePath / moduleName
        if not modulePath.exists():
            print(f"❌ 模块 {moduleName} 不存在")
            return False
        
        try:
            # 1. 修改package.json
            self._updatePackageJson(modulePath)
            
            # 2. 修改babel.config.js
            self._updateBabelConfig(modulePath)
            
            # 3. 创建harmony目录和文件
            self._createHarmonyDirectory(modulePath)
            
            # 4. 约束7: 修复代码中的charset问题
            self._fixCharsetIssues(modulePath)

            print(f"✅ {moduleName} 鸿蒙适配完成")
            return True
            
        except Exception as e:
            print(f"❌ 适配模块 {moduleName} 失败: {e}")
            return False
    
    def _updatePackageJson(self, modulePath: Path):
        """更新package.json文件"""
        packageJsonPath = modulePath / "package.json"
        
        with open(packageJsonPath, 'r', encoding='utf-8') as f:
            packageData = json.load(f)
        
        # 更新dependencies
        if 'dependencies' not in packageData:
            packageData['dependencies'] = {}
        
        # 更新react-native版本
        packageData['dependencies']['react-native'] = self.harmonyConfig['react_native_version']
        
        # 添加@kds/react-native-linear-gradient
        packageData['dependencies']['@kds/react-native-linear-gradient'] = self.harmonyConfig['linear_gradient_version']
        
        # 添加auto-adapt-harmony依赖
        packageData['dependencies']['@locallife/auto-adapt-harmony'] = self.harmonyConfig['auto_adapt_version']
        
        # 更新devDependencies中的@krn/cli
        if 'devDependencies' not in packageData:
            packageData['devDependencies'] = {}
        packageData['devDependencies']['@krn/cli'] = self.harmonyConfig['krn_cli_version']
        
        # 更新resolutions
        if 'resolutions' not in packageData:
            packageData['resolutions'] = {}
        packageData['resolutions'].update(self.harmonyConfig['resolutions'])
        
        # 约束8: 检查并修复react-redux版本
        self._fixReactReduxVersion(packageData)
        
        # 保存文件
        with open(packageJsonPath, 'w', encoding='utf-8') as f:
            json.dump(packageData, f, indent=4, ensure_ascii=False)
        
        print(f"  ✅ 已更新 {modulePath.name}/package.json")
    
    def _updateBabelConfig(self, modulePath: Path):
        """更新babel.config.js文件"""
        babelConfigPath = modulePath / "babel.config.js"
        
        if not babelConfigPath.exists():
            # 创建基础的babel配置
            babel_content = """module.exports = {
    presets: ['module:metro-react-native-babel-preset'],
    plugins: []
};"""
            with open(babelConfigPath, 'w', encoding='utf-8') as f:
                f.write(babel_content)
        
        with open(babelConfigPath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经包含harmony相关配置
        if '@locallife/auto-adapt-harmony' in content:
            print(f"  ℹ️  {modulePath.name}/babel.config.js 已包含harmony配置")
            return
        
        # 定义需要添加的 alias 配置
        harmonyAliases = {
            'react-native-linear-gradient': '@kds/react-native-linear-gradient',
            'react-native-gesture-handler': '@kds/react-native-gesture-handler',
            'react-native-tab-view': '@kds/react-native-tab-view',
        }
        
        # 定义其他 harmony 插件（除了 module-resolver）
        otherHarmonyPlugins = [
            """[
            '@locallife/auto-adapt-harmony/src/plugin/bridge-replace-plugin.js',
            {
                notSupportBridges: {
                    invoke: [
                        'getShowingPendants',
                        'publishRubas',
                        'setRubasDimension',
                        'setRubasDimensionBatch',
                        'subscribe',
                        'unSubscribe'
                    ],
                },
            },
        ]""",
            """['@locallife/auto-adapt-harmony/src/plugin/error-delete-plugin.js']""",
            """[
            '@locallife/auto-adapt-harmony/src/plugin/file-replace-plugin.js',
            {
                replacements: {
                    '@locallife/utils': {
                        jumpUrl: '/harmony/jumpUrl.ts',
                    },
                },
            },
        ]""",
            """[
                '@locallife/auto-adapt-harmony/src/plugin/transform-kwaimage-children.js'
            ]"""
        ]
        
        # 检查是否已存在 module-resolver 插件
        moduleResolverPattern = r'(\[\s*[\'"]module-resolver[\'"],\s*\{[^}]*?alias:\s*\{)([^}]*?)(\}[^}]*?\}[^]]*?\])'
        moduleResolverMatch = re.search(moduleResolverPattern, content, re.DOTALL)
        
        if moduleResolverMatch:
            # 如果已存在 module-resolver，合并 alias
            print(f"  ℹ️  发现现有的 module-resolver 配置，正在合并 alias...")
            existing_alias = moduleResolverMatch.group(2).strip()
            
            # 构建新的 alias 内容
            new_alias_entries = []
            for key, value in harmonyAliases.items():
                if key not in existing_alias:
                    new_alias_entries.append(f"                    '{key}': '{value}'")
            
            if new_alias_entries:
                if existing_alias and not existing_alias.endswith(','):
                    existing_alias += ','
                new_alias_content = existing_alias + '\n' + ',\n'.join(new_alias_entries)
                new_content = content.replace(
                    moduleResolverMatch.group(0),
                    f"{moduleResolverMatch.group(1)}\n{new_alias_content}\n                {moduleResolverMatch.group(3)}"
                )
            else:
                new_content = content
                print(f"  ℹ️  所有 harmony alias 已存在，跳过合并")
        else:
            # 如果不存在 module-resolver，准备创建一个新的
            moduleResolverPlugin = f"""[
            'module-resolver',
            {{
                alias: {{
{chr(10).join([f"                    '{k}': '{v}'," for k, v in harmonyAliases.items()])}
                }},
            }},
        ]"""
            new_content = content
        
        # 在plugins数组的末尾添加harmony插件（在最后一个插件后面）
        if moduleResolverMatch:
            # 已存在 module-resolver，只添加其他插件
            plugins_to_add = otherHarmonyPlugins
        else:
            # 不存在 module-resolver，添加 module-resolver 和其他插件
            all_plugins = [moduleResolverPlugin] + otherHarmonyPlugins
            plugins_to_add = all_plugins
        
        # 查找 plugins 数组的结束位置（在 env 之前）
        envPattern = r'(\],\s*)(env:\s*\{)'
        envMatch = re.search(envPattern, new_content, re.DOTALL)
        
        if envMatch:
            # 在 env 之前插入新的插件，确保逗号正确
            # 查找最后一个插件的结束位置
            last_plugin_pattern = r'(.*?)(\],\s*env:)'
            last_plugin_match = re.search(last_plugin_pattern, new_content, re.DOTALL)
            
            if last_plugin_match:
                before_env = last_plugin_match.group(1)
                # 检查是否以逗号结尾
                if not before_env.rstrip().endswith(','):
                    # 在最后一个插件后添加逗号，然后添加新插件
                    plugins_str = ',\n        ' + ',\n        '.join(plugins_to_add)
                else:
                    # 直接添加新插件
                    plugins_str = '\n        ' + ',\n        '.join(plugins_to_add)
                
                new_content = new_content.replace(
                    envMatch.group(0),
                    f"{plugins_str}\n    {envMatch.group(1)}{envMatch.group(2)}"
                )
        else:
            # 如果没有 env，查找 plugins 数组的结束
            pluginsEndPattern = r'(\],\s*)(};?\s*$)'
            pluginsEndMatch = re.search(pluginsEndPattern, new_content, re.DOTALL)
            
            if pluginsEndMatch:
                # 在 plugins 数组结束前插入新的插件
                last_plugin_pattern = r'(.*?)(\],\s*};?)'
                last_plugin_match = re.search(last_plugin_pattern, new_content, re.DOTALL)
                
                if last_plugin_match:
                    before_end = last_plugin_match.group(1)
                    # 检查是否以逗号结尾
                    if not before_end.rstrip().endswith(','):
                        # 在最后一个插件后添加逗号，然后添加新插件
                        plugins_str = ',\n        ' + ',\n        '.join(plugins_to_add)
                    else:
                        # 直接添加新插件
                        plugins_str = '\n        ' + ',\n        '.join(plugins_to_add)
                    
                    new_content = new_content.replace(
                        pluginsEndMatch.group(0),
                        f"{plugins_str}\n    {pluginsEndMatch.group(1)}{pluginsEndMatch.group(2)}"
                    )
            else:
                # 如果没有找到plugins数组，添加一个
                new_content = new_content.replace(
                    'presets: [\'module:metro-react-native-babel-preset\'],',
                    f'presets: [\'module:metro-react-native-babel-preset\'],\n    plugins: [\n        {",".join(plugins_to_add)}\n    ],'
                )
            
        with open(babelConfigPath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  ✅ 已更新 {modulePath.name}/babel.config.js")
    
    def _createHarmonyDirectory(self, modulePath: Path):
        """创建harmony目录和文件"""
        harmonyDir = modulePath / "harmony"
        harmonyDir.mkdir(exist_ok=True)
        
        # 复制jumpUrl.ts文件
        try:
            # 尝试从包资源中获取文件路径
            package_path = res.as_file(res.files('krn_harmony_adapter') / 'jumpUrl.ts')
            print(f"  ✅ 已从包资源中获取jumpUrl.ts文件, {package_path}")
            if os.path.exists(package_path):
                sourceJumpUrl = Path(package_path)
        except:
            # 如果 pkg_resources 失败，使用相对路径
            sourceJumpUrl = self.harmonyPath / "jumpUrl.ts"
            print(f"  ⚠️  未找到包资源中的jumpUrl.ts文件，使用相对路径 {sourceJumpUrl}")
        
        targetJumpUrl = harmonyDir / "jumpUrl.ts"
        
        if sourceJumpUrl.exists():
            shutil.copy2(sourceJumpUrl, targetJumpUrl)
            print(f"  ✅ 已创建 {modulePath.name}/harmony/jumpUrl.ts")
        else:
            print(f"  ⚠️  模板文件 {sourceJumpUrl} 不存在，跳过创建jumpUrl.ts")

    def _fixCharsetIssues(self, modulePath: Path):
        """
        遍历指定模块路径下的 `src` 目录，并将所有文件中的
        'charset=UTF-8' 字符串替换为 'charset=utf-8'
        """
        
        # 1. 构建目标 'src' 目录的完整路径
        srcPath = modulePath / 'src'

        # 2. 检查 'src' 目录是否存在，如果不存在则打印警告并直接返回
        if not srcPath.is_dir():
            print(f"⚠️  警告: 在 '{modulePath}' 中未找到 'src' 目录，跳过处理。")
            return

        print(f"🔍 正在扫描目录: {srcPath}")

        # 初始化计数器，用于最终的报告
        filesScanned = 0
        filesChanged = 0

        # 3. 使用 rglob('*') 递归地遍历 'src' 目录下的所有文件和文件夹
        for filePath in srcPath.rglob('*'):
            # 确保当前路径是一个文件，而不是一个目录
            if filePath.is_file():
                filesScanned += 1
                try:
                    # 4. 读取文件内容。我们假设文件是 utf-8 编码。
                    #    Path.read_text() 会自动处理文件的打开和关闭。
                    originalContent = filePath.read_text(encoding='utf-8')

                    # 5. 检查是否包含需要修改的字符串，避免不必要的写操作
                    if 'charset=UTF-8' in originalContent:
                        # 6. 执行替换
                        modified_content = originalContent.replace('charset=UTF-8', 'charset=utf-8')

                        # 7. 将修改后的内容写回文件
                        filePath.write_text(modified_content, encoding='utf-8')

                        # 打印日志并更新计数器
                        # 使用 relative_to() 让路径显示更友好
                        print(f"✅ 已修正: {filePath.relative_to(modulePath)}")
                        filesChanged += 1

                except UnicodeDecodeError:
                    # 8. 错误处理：如果文件不是有效的 utf-8 文本（例如图片、二进制文件），
                    #    read_text 会抛出此异常。我们将其捕获并跳过该文件。
                    print(f"⚪️  已跳过 (非文本文件): {filePath.relative_to(modulePath)}")
                except Exception as e:
                    # 捕获其他可能的异常，例如权限问题
                    print(f"❌ 处理文件时出错 {filePath.relative_to(modulePath)}: {e}", file=sys.stderr)

        # 9. 打印最终的总结报告
        print(f"\n✨ 扫描完成。共扫描 {filesScanned} 个文件，修正了 {filesChanged} 个文件。")

    def _fixReactReduxVersion(self, packageData):
        """将react-redux版本从8.0.0+降级到7.2.6"""
        targetPackage = 'react-redux'
        targetVersion = '^7.2.6'
        versionThreshold = version.parse("8.0.0")

        # 1. 安全地检查 'dependencies' 和 'react-redux' 是否存在
        dependencies = packageData.get('dependencies')
        if not isinstance(dependencies, dict):
            # 如果没有 dependencies 块，直接返回原数据
            return packageData

        currentVersionStr = dependencies.get(targetPackage)
        if not isinstance(currentVersionStr, str):
            # 如果 dependencies 中没有 react-redux，也直接返回
            return packageData

        # 2. 从版本字符串中提取出纯净的版本号（例如从 "^8.1.0" 提取 "8.1.0"）
        #    使用正则表达式查找第一个 x.y.z 格式的数字
        versionMatch = re.search(r'(\d+\.\d+\.\d+)', currentVersionStr)
        if not versionMatch:
            # 如果找不到有效的版本号（例如它是一个 git url），则不处理
            print(f"⚪️  在 '{currentVersionStr}' 中未找到可比较的版本号，跳过对 '{targetPackage}' 的处理。")
            return packageData
        
        cleanVersionStr = versionMatch.group(1)

        # 3. 使用 packaging 库比较版本
        try:
            currentVersion = version.parse(cleanVersionStr)
            
            # 检查当前版本是否 > 8.0.0
            if currentVersion > versionThreshold:
                print(f"✅ 检测到 '{targetPackage}' 版本 '{currentVersionStr}' > {versionThreshold}，将替换为 '{targetVersion}'。")
                # 4. 如果条件满足，执行替换
                packageData['dependencies'][targetPackage] = targetVersion
            else:
                print(f"ℹ️  '{targetPackage}' 版本 '{currentVersionStr}' 无需修改。")

        except Exception:
            print(f"⚠️  警告: 无法解析版本号 '{cleanVersionStr}'，跳过处理。")

        # 5. 返回修改后（或未修改）的数据
        return packageData
    
    def _runYarnInstall(self, modulePath: Path):
        """在模块目录中执行yarn命令安装依赖"""
        print(f"📦 正在执行 yarn install...")
        
        try:
            # 切换到模块目录并执行yarn命令
            result = subprocess.run(
                ['yarn', 'install'],
                cwd=modulePath,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                print(f"  ✅ yarn install 执行成功")
                # 如果有输出信息，显示最后几行
                if result.stdout:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 3:
                        print(f"  📝 最后几行输出:")
                        for line in lines[-3:]:
                            if line.strip():
                                print(f"     {line}")
                    else:
                        for line in lines:
                            if line.strip():
                                print(f"     {line}")
            else:
                print(f"  ❌ yarn install 执行失败 (退出码: {result.returncode})")
                if result.stderr:
                    print(f"  错误信息: {result.stderr}")
                # 即使yarn失败也不中断适配流程，只是警告
                print(f"  ⚠️  继续完成适配流程，请手动检查依赖安装")
                
        except subprocess.TimeoutExpired:
            print(f"  ⏰ yarn install 执行超时 (5分钟)，请手动执行")
        except FileNotFoundError:
            print(f"  ❌ 未找到 yarn 命令，请确保已安装 yarn")
            print(f"  💡 提示: 可以运行 'npm install -g yarn' 安装 yarn")
        except Exception as e:
            print(f"  ❌ 执行 yarn install 时出错: {e}")
            print(f"  ⚠️  继续完成适配流程，请手动执行 yarn install")

    def updateModuleCode(self, moduleName: str, aiType: str) -> bool:
        print(f"🔀 更新模块代码 - {moduleName}")
        print("=" * 50)
        
        modulePath = os.path.join(self.basePath, moduleName)
        if not os.path.exists(modulePath):
            print(f"❌ 模块不存在: {moduleName}")
            return False
        
        try:
            # 1. 从最新Dev分支检出最新代码
            latedBranch = self.gitManager.getLatestDevBranch()
            print(f"📍 步骤1: 从{latedBranch}分支检出最新代码...")
            success, output = self.gitManager.checkoutModuleFromBranch(latedBranch, moduleName)
            if not success:
                print(f"❌ 检出最新dev分支代码失败: {output}")
                if self.agreeMaster == False:
                    res = input("是否从master分支检出最新代码：Y/n").strip()
                    if res.lower() == 'n':
                        return False
                self.agreeMaster = True
                success, output = self.gitManager.checkoutModuleFromBranch("master", moduleName)
                if not success:
                    print(f"❌ 从master分支检出代码失败: {output}")
                    return
            
            # 2. 从harmony_master分支备份harmony内容
            print("📍 步骤2: 备份harmony相关内容...")
            backupInfo = self.backupManager.backup_harmony_content(modulePath, "harmony_master")
            
            
            # 3. 恢复harmony相关内容
            print("📍 步骤3: 恢复harmony相关内容...")
            success = self.backupManager.restore_harmony_content(modulePath, backupInfo)
            if not success:
                print("⚠️  部分harmony内容恢复失败")
            
            # 4. 智能合并冲突的代码
            # print("📍 步骤4: 智能合并冲突代码...")
            # self._mergeConflictedFiles(modulePath, backupInfo, aiType)
            
            # 5. 清理备份目录
            print("📍 步骤4: 清理备份目录...")
            self.backupManager.cleanup_backup(modulePath)
            
            print(f"✅ 模块 {moduleName} 代码合并完成")
            return True
            
        except Exception as e:
            print(f"❌ 合并代码时出错: {e}")
            return False
    
    def _mergeConflictedFiles(self, modulePath: str, backupInfo: Dict[str, Any], aiType: str = "") -> None:
        """合并有冲突的文件"""
        if aiType == AiType.KWAIPILLOT or aiType == AiType.OPENAI:
            self._mergeConfictedByAI(modulePath, backupInfo, aiType)
        else:
            self._mergeConfictedByCode(modulePath, backupInfo)

    def _mergeConfictedByAI(self, modulePath: str, backupInfo: Dict[str, Any], aiType: str) -> None:
        harmonyFiles = backupInfo.get('harmony_files', {})
        
        startTime = time.time()
        mergeResults = []
        totalFiles, filePaths = self.moduleManager.findHarmonyFiles(modulePath)
        for originalPath, backupPath in harmonyFiles.items():
            fullOriginalPath = os.path.join(self.basePath, originalPath)
            
            print(f"  处理文件: {originalPath}")
            if os.path.exists(fullOriginalPath) and os.path.exists(backupPath):
                try:
                    mergeResult = self.mergeManager.mergeHarmonyContentByAi(fullOriginalPath, backupPath, aiType)
                    mergeResults.append({
                        'file': fullOriginalPath,
                        'result': mergeResult
                    })
                    
                    # 显示合并结果
                    if mergeResult.get('success', False):
                        confidence = mergeResult.get('confidence', 0)
                        conflicts = mergeResult.get('conflicts_found', 0)
                        
                        if confidence > 0.8:
                            print(f"  ✅ 自动合并成功")
                        else:
                            print(f"  ⚠️  合并完成，建议人工检查")
                        
                        if conflicts > 0:
                            print(f"  📊 解决了 {conflicts} 个冲突")
                        
                        # 显示AI建议
                        suggestions = mergeResult.get('suggestions', [])
                        if suggestions:
                            print("  💡 AI建议:")
                            for suggestion in suggestions[:3]:  # 只显示前3个建议
                                print(f"     • {suggestion}")
                    else:
                        print(f"  ❌ 合并失败: {mergeResult.get('error', '未知错误')}")
                    
                except Exception as e:
                    print(f"⚠️  合并文件失败 {originalPath}: {e}")

        successfulMerges = sum(1 for r in mergeResults if r['result']['success'])
        
        print(f"\n📊 合并完成统计:")
        print(f"   总文件数: {totalFiles}")
        print(f"   成功合并: {successfulMerges}")
        print(f"   失败数量: {totalFiles - successfulMerges}")
        print(f"   总耗时：{time.time() - startTime:.2f}秒")
        
        # 显示AI统计信息
        ai_stats = self.mergeManager.getAiMergeStatistics()
        print(f"\n🤖 AI合并统计:")
        print(f"   自动解决: {ai_stats['auto_resolved']}")
        print(f"   需要审查: {ai_stats['manual_reviews']}")

    def _mergeConfictedByCode(self, modulePath: str, backupInfo: Dict[str, Any]) -> None:
        harmonyFiles = backupInfo.get('harmony_files', {})
        
        for originalPath, backupPath in harmonyFiles.items():
            fullOriginalPath = os.path.join(modulePath, originalPath)
            
            if os.path.exists(fullOriginalPath) and os.path.exists(backupPath):
                try:
                    self.mergeManager.mergeHarmonyContentByCode(fullOriginalPath, backupPath, modulePath, originalPath)
                    # 读取当前文件和备份文件
                    with open(fullOriginalPath, 'r', encoding='utf-8') as f:
                        currentContent = f.read()
                    
                    with open(backupPath, 'r', encoding='utf-8') as f:
                        backup_content = f.read()
                    
                    # 智能合并
                    mergedContent = self.mergeManager.mergeHarmonyContentByCode(
                        currentContent, backup_content, originalPath
                    )
                    
                    # 写回文件
                    if mergedContent != currentContent:
                        with open(fullOriginalPath, 'w', encoding='utf-8') as f:
                            f.write(mergedContent)
                        print(f"✅ 智能合并文件: {originalPath}")
                    
                except Exception as e:
                    print(f"⚠️  合并文件失败 {originalPath}: {e}")
