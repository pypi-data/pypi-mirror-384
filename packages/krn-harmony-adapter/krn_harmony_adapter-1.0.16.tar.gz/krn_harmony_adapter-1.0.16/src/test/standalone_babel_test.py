import json
import re
from pathlib import Path
import textwrap

def update_babel_config_content(content: str) -> str:
    """
    一个独立的函数，用于更新 babel.config.js 的内容。
    它包含了从 Adapter._updateBabelConfig 中提取的核心逻辑。
    """
    # 定义需要添加的 alias 配置
    harmonyAliases = {
        'react-native-linear-gradient': '@kds/react-native-linear-gradient',
        'react-native-gesture-handler': '@kds/react-native-gesture-handler',
        'react-native-tab-view': '@kds/react-native-tab-view',
    }

    # 将插件定义为Python数据结构，以便自动格式化
    otherHarmonyPlugins_data = [
        [
            '@locallife/auto-adapt-harmony/src/plugin/bridge-replace-plugin.js',
            {
                "notSupportBridges": {
                    "invoke": [
                        'getShowingPendants', 'publishRubas', 'setRubasDimension',
                        'setRubasDimensionBatch', 'subscribe', 'unSubscribe'
                    ],
                },
            },
        ],
        ['@locallife/auto-adapt-harmony/src/plugin/error-delete-plugin.js'],
        [
            '@locallife/auto-adapt-harmony/src/plugin/file-replace-plugin.js',
            {
                "replacements": {
                    '@locallife/utils': {"jumpUrl": '/harmony/jumpUrl.ts'},
                },
            },
        ],
        ['@locallife/auto-adapt-harmony/src/plugin/transform-kwaimage-children.js']
    ]

    # 准备 module-resolver 插件的字符串
    moduleResolverPlugin_data = [
        'module-resolver',
        {
            'alias': harmonyAliases
        }
    ]

    # 查找并尝试更新现有的 module-resolver
    moduleResolverPattern = r"('module-resolver'[\s\S]*?alias:\s*\{)([\s\S]*?)(\})"
    moduleResolverMatch = re.search(moduleResolverPattern, content)

    new_content = content
    plugins_to_add = []

    if moduleResolverMatch:
        # 如果已存在 module-resolver，合并 alias
        print("  ℹ️  发现现有的 module-resolver 配置，正在合并 alias...")
        existing_alias_block = moduleResolverMatch.group(2)
        
        new_alias_entries = []
        for key, value in harmonyAliases.items():
            if f"'{key}'" not in existing_alias_block and f'"{key}"' not in existing_alias_block:
                new_alias_entries.append(f"                    '{key}': '{value}'")
        
        if new_alias_entries:
            if existing_alias_block.strip() and not existing_alias_block.strip().endswith(','):
                existing_alias_block = existing_alias_block.rstrip() + ',\n'

            aliases_to_insert = ',\n'.join(new_alias_entries)
            updated_alias_block = existing_alias_block + aliases_to_insert

            new_content = new_content.replace(
                moduleResolverMatch.group(0),
                f"{moduleResolverMatch.group(1)}{updated_alias_block}{moduleResolverMatch.group(3)}"
            )
            print(f"  ✅  已准备合并 {len(new_alias_entries)} 个新 alias。")
        else:
            print("  ℹ️  所有 harmony alias 已存在，跳过合并。")

    else:
        # 如果不存在 module-resolver，则需要添加它和所有其他插件
        # 注意：这里只准备 module-resolver，其他插件在下一步统一处理
        plugins_to_add.append(moduleResolverPlugin_data)

    # --- 步骤 2: 注入其他 Harmony 插件 (如果需要) ---
    if '@locallife/auto-adapt-harmony' not in new_content:
        # 将 otherHarmonyPlugins_data 插入到待添加列表的最前面
        plugins_to_add = otherHarmonyPlugins_data + plugins_to_add

    if plugins_to_add:
        plugins_array_match = re.search(r"plugins:\s*\[([\s\S]*?)\]", new_content, re.DOTALL)
        if plugins_array_match:
            # --- 采用更可靠的前置插入逻辑 ---
            plugins_json_str = json.dumps(plugins_to_add, indent=4).replace('"', "'")
            plugins_str_inner = plugins_json_str[1:-1].strip()
            indented_plugins_str = textwrap.indent(plugins_str_inner, ' ' * 4) # 基础缩进4

            existing_plugins_content = plugins_array_match.group(1)
            separator = ',\n' if existing_plugins_content.strip() else ''

            # 构建最终的、完整的 plugins 数组
            final_plugins_block = f"plugins: [\n    {indented_plugins_str}{separator}{existing_plugins_content}]"
            new_content = new_content.replace(plugins_array_match.group(0), final_plugins_block)
            print(f"  ✅  已准备注入 {len(plugins_to_add)} 个新插件。")
    else:
        print("  ℹ️  Harmony 插件已存在，跳过添加。")


    return new_content


if __name__ == "__main__":
    # 1. 定义 babel.config.js 文件路径
    # 使用 .resolve() 和 .parent 确保我们能准确地从脚本位置找到项目根目录
    # __file__ 是当前脚本的路径，.parent 会获取该脚本所在的目录
    script_dir = Path(__file__).resolve().parent
    babel_config_path = script_dir / 'babel.config.js'
    output_path = script_dir / 'babel.config.modified.js'

    if not babel_config_path.exists():
        print(f"❌ 错误: 未在项目根目录找到 '{babel_config_path.name}' 文件。")
        exit(1)

    # 2. 读取原始文件内容
    original_content = babel_config_path.read_text(encoding='utf-8')

    # 3. 调用核心函数处理内容
    print("🚀 开始处理 babel.config.js...\n")
    modified_content = update_babel_config_content(original_content)
    
    # 4. 将修改后的内容写入新文件
    output_path.write_text(modified_content, encoding='utf-8')
    print(f"\n🚀 处理完成！修改后的内容已写入到: {output_path.name}")
