#!/usr/bin/env python3
"""
Harmony Adapter CLI - 命令行接口
"""

import sys
import os
import argparse
from typing import Optional, List

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from .Main import Main
    from . import __version__
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    sys.path.append(os.path.dirname(current_dir))
    from .Main import Main
    from . import __version__


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog='kha',
        description='KRN鸿蒙适配自动化工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  kha                       # 交互式模式
  kha check                 # 检查所有模块适配状态
  kha sync                  # 同步缺失模块
  kha adapt <模块名>         # 适配指定模块
  kha batch                 # 批量适配所有未适配模块
    kha batch live          # 批量适配直播模块
    kha batch non_live      # 批量适配非直播模块
    kha batch all           # 批量适配所有模块
  kha doc                   # 生成文档
  kha url                   # 检查接口注册状态

        """
    )
    
    parser.add_argument(
        'command',
        nargs='?',
        choices=['check', 'sync', 'adapt', 'batch', 'doc', 'url'],
        help='要执行的命令'
    )
    
    parser.add_argument(
        'args',
        nargs='*',
        help='命令参数（如模块名称、URL路径等）'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    parser.add_argument(
        '--base-path',
        default='.',
        help='项目根目录路径（默认为当前目录）'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细输出'
    )
    
    return parser


def main():
    """主入口函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # 初始化适配器
        adapter = Main(args.base_path)
        
        # 如果没有指定命令，进入交互式模式
        if not args.command:
            adapter.interactive_menu()
            return
        
        # 执行指定命令
        if args.command == 'check':
            adapter.checkAllModulesAdaptation()
        
        elif args.command == 'sync':
            adapter.syncMissingModules()
        
        elif args.command == 'adapt':
            if not args.args:
                print("❌ adapt命令需要指定模块名称")
                print("使用方法: kha adapt <模块名>")
                sys.exit(1)
            for module_name in args.args:
                adapter.adaptSingleModule(module_name, "")
        
        elif args.command == 'batch':
            module_type = args.args[0] if args.args else "all"
            adapter.adaptBatchModules(module_type)
        
        elif args.command == 'doc':
            adapter.generateDocumentation()
        
        elif args.command == 'url':
            if args.args:
                if args.args[0].startswith('/'):
                    adapter.checkUrlRegisteryStatus('harmonyos-lbs.kwailocallife.com', args.args)
                else:
                    adapter.checkUrlRegisteryStatus(args.args[0], args.args[1:])
            else:
                adapter.checkUrlRegisteryStatus()
        
        else:
            parser.print_help()
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
        sys.exit(0)
    
    except Exception as e:
        if args.verbose:
            import traceback
            traceback.print_exc()
        else:
            print(f"❌ 执行失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()