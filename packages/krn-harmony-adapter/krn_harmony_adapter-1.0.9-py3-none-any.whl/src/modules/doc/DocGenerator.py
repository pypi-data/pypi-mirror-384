"""
文档生成模块
负责生成各种文档和报告
"""
import os
from datetime import datetime
from typing import Dict, Any, List

from modules.doc.UrlDetector import UrlDetector


class DocGenerator(UrlDetector):
    """文档生成器"""
    
    def generateAllDocs(self) -> bool:
        """生成所有文档"""
        print("📝 生成文档")
        print("=" * 50)
        
        try:
            # 生成适配状态报告
            self.generateAdaptationStatusReport()
            
            # 生成模块统计报告
            self.generateModuleStatisticsReport()
            
            # 生成使用指南
            self.generateUsageGuide()

            # 生成未注册接口报告
            self.generateUrlReport()
            
            print("✅ 所有文档生成完成")
            return True
            
        except Exception as e:
            print(f"❌ 生成文档失败: {e}")
            return False
    
    def generateAdaptationStatusReport(self) -> str:
        """生成适配状态报告"""
        modules = self.moduleManager.discoverModules()
        categorized = self._categorizeModulesByAdaptation(modules)
        stats = self.moduleManager.getModuleStatistics()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        content = f"""# 鸿蒙适配状态报告

> 生成时间: {timestamp}

## 📊 总体统计

- **总模块数**: {stats['total_modules']}
- **已适配**: {stats['adapted_modules']} ({stats['adaptation_rate']:.1f}%)
- **未适配**: {stats['not_adapted_modules']} ({100-stats['adaptation_rate']:.1f}%)

## 🎥 直播Bundle统计

- **总数**: {stats['live_modules']['total']}
- **已适配**: {stats['live_modules']['adapted']} ({stats['live_modules']['adaptation_rate']:.1f}%)
- **未适配**: {stats['live_modules']['not_adapted']} ({100-stats['live_modules']['adaptation_rate']:.1f}%)

## 📱 非直播Bundle统计

- **总数**: {stats['non_live_modules']['total']}
- **已适配**: {stats['non_live_modules']['adapted']} ({stats['non_live_modules']['adaptation_rate']:.1f}%)
- **未适配**: {stats['non_live_modules']['not_adapted']} ({100-stats['non_live_modules']['adaptation_rate']:.1f}%)

## ✅ 已适配模块列表

"""
        
        # 已适配模块
        if categorized['adapted']:
            live_adapted = [m for m in categorized['adapted'] if 'live' in m['moduleName'].lower()]
            non_live_adapted = [m for m in categorized['adapted'] if 'live' not in m['moduleName'].lower()]
            
            if live_adapted:
                content += "### 🎥 直播Bundle\n\n"
                for module in live_adapted:
                    content += f"- **{module['moduleName']}** \n"
                content += "\n"
            
            if non_live_adapted:
                content += "### 📱 非直播Bundle\n\n"
                for module in non_live_adapted:
                    content += f"- **{module['moduleName']}** \n"
                content += "\n"
        
        content += "## ❌ 未适配模块列表\n\n"
        
        # 未适配模块
        if categorized['not_adapted']:
            live_not_adapted = [m for m in categorized['not_adapted'] if 'live' in m['moduleName'].lower()]
            non_live_not_adapted = [m for m in categorized['not_adapted'] if 'live' not in m['moduleName'].lower()]
            
            if live_not_adapted:
                content += "### 🎥 直播Bundle\n\n"
                for module in live_not_adapted:
                    content += f"- **{module['moduleName']}**\n"
                    if module['issues']:
                        content += f"  - 问题: {', '.join(module['issues'])}\n"
                content += "\n"
            
            if non_live_not_adapted:
                content += "### 📱 非直播Bundle\n\n"
                for module in non_live_not_adapted:
                    content += f"- **{module['moduleName']}**\n"
                    if module['issues']:
                        content += f"  - 问题: {', '.join(module['issues'])}\n"
                content += "\n"
        
        content += """## 📋 适配建议

### 优先级建议

1. **高优先级**: 直播Bundle (业务核心功能)
2. **中优先级**: 基础功能Bundle
3. **低优先级**: 辅助功能Bundle

### 适配步骤

1. 使用脚本检查模块适配状态
2. 优先适配直播相关Bundle
3. 批量适配其他模块
4. 验证适配结果

---

*此报告由鸿蒙适配器自动生成*
"""
        
        # 保存到文件
        reportPath = os.path.join(self.docPath, "适配状态报告.md")
        with open(reportPath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 适配状态报告已生成: {reportPath}")
        return reportPath
    
    def generateModuleStatisticsReport(self) -> str:
        """生成模块统计报告"""
        modules = self.moduleManager.discoverModules()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        content = f"""# 模块详细统计报告

> 生成时间: {timestamp}

## 📋 所有模块详细信息

"""
        
        for moduleName in sorted(modules):
            status = self.moduleManager.checkModuleAdaptationStatus(moduleName)
            is_live = 'live' in moduleName.lower()
            
            content += f"### {moduleName}\n\n"
            content += f"- **类型**: {'🎥 直播Bundle' if is_live else '📱 非直播Bundle'}\n"
            content += f"- **适配状态**: {'✅ 已适配' if status['is_adapted'] else '❌ 未适配'}\n"
            content += f"- **React Native版本**: {status['react_native_version']}\n"
            content += f"- **Auto-adapt依赖**: {'✅' if status['has_auto_adapt_dependency'] else '❌'}\n"
            content += f"- **Harmony目录**: {'✅' if status['has_harmony_directory'] else '❌'}\n"
            content += f"- **Harmony文件数量**: {status['harmony_files_count']}\n"
            content += f"- **包含Harmony文件路径**: \n{(status['harmony_files_path']) if status['harmony_files_path'] else '无'}"
            
            if status['issues']:
                content += f"- **问题**: {', '.join(status['issues'])}\n"
            
            content += "\n"
        
        content += """---

*此报告由鸿蒙适配器自动生成*
"""
        
        # 保存到文件
        reportPath = os.path.join(self.docPath, "鸿蒙模块统计报告.md")
        with open(reportPath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 模块统计报告已生成: {reportPath}")
        return reportPath
    
    def generateUsageGuide(self) -> str:
        """生成使用指南"""
        content = """# 鸿蒙适配器使用指南

## 🚀 快速开始

### 基本使用

```bash
# 交互式模式
kha

# 命令行模式
kha [命令] [参数]
```

## 📋 功能说明

### 1. 同步缺失模块

自动同步master分支有但当前分支没有的模块。

```bash
# 交互式
选择选项 1

# 命令行
kha sync
```

### 2. 检查适配状态

检查所有模块的鸿蒙适配状态，区分直播和非直播Bundle。

```bash
# 交互式
选择选项 2

# 命令行
kha check
```

### 3. 适配指定模块

按照SOP规则一键适配指定模块。

```bash
# 交互式
选择选项 3，然后输入模块名

# 命令行
kha adapt <模块名>
```

### 4. 批量适配模块

批量适配多个模块，支持按类型筛选。

```bash
# 交互式
选择选项 4，然后选择适配类型

# 命令行
kha batch [all|live|non_live]
```

### 5. 检查接口注册状态

检查未注册的接口。

```bash
# 交互式
选择选项 5

# 命令行
kha url
```

### 6. 生成文档

生成适配状态报告和统计文档。

```bash
# 交互式
选择选项 6

# 命令行
kha doc
```

## 🔧 高级功能

### 代码冲突处理

当合并代码时遇到冲突，脚本会：

1. 自动识别harmony相关的代码块
2. 尝试智能合并
3. 如果无法自动合并，会在相关位置插入冲突标记
4. 用户需要手动解决冲突


## ⚠️  注意事项

1. **备份重要数据**: 在执行适配操作前，建议备份重要代码
2. **检查Git状态**: 确保工作区干净，避免意外覆盖
3. **验证适配结果**: 适配完成后，检查模块是否正常工作
4. **处理冲突**: 遇到代码冲突时，仔细检查并手动解决

## 🐛 故障排除

### 常见问题


### 获取帮助


---

*此指南由鸿蒙适配器自动生成*
"""
        
        # 保存到文件
        readMePath = os.path.join(self.docPath, "鸿蒙适配指南.md")
        with open(readMePath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 使用指南已生成: {readMePath}")
        return readMePath
    
    def _categorizeModulesByAdaptation(self, modules: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """按适配状态分类模块"""
        categorized = {
            'adapted': [],
            'not_adapted': [],
            'live_modules': {
                'adapted': [],
                'not_adapted': []
            },
            'non_live_modules': {
                'adapted': [],
                'not_adapted': []
            }
        }
        
        for moduleName in modules:
            status = self.moduleManager.checkModuleAdaptationStatus(moduleName)
            is_live = 'live' in moduleName.lower()
            
            if status['is_adapted']:
                categorized['adapted'].append(status)
                if is_live:
                    categorized['live_modules']['adapted'].append(status)
                else:
                    categorized['non_live_modules']['adapted'].append(status)
            else:
                categorized['not_adapted'].append(status)
                if is_live:
                    categorized['live_modules']['not_adapted'].append(status)
                else:
                    categorized['non_live_modules']['not_adapted'].append(status)
        
        return categorized
