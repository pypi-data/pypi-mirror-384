#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块检查器 - 负责检查模块的鸿蒙适配状态
"""

from typing import Any, Dict

from config.Config import Config

"""模块检查器"""
class Check(Config):

    def checkAllModulesAdaptation(self) -> Dict[str, Any]:
        print("🔍 检查所有模块的鸿蒙适配状态")
        print("=" * 50)
        
        moduleManager = self.moduleManager
        modules = moduleManager.discoverModules()
        categorized = moduleManager.categorizeModulesByAdaptation(modules)
        stats = moduleManager.getModuleStatistics()
        
        # 显示统计信息
        print(f"📊 模块适配统计报告")
        print(f"   总模块数: {stats['total_modules']}")
        print(f"   已适配: {stats['adapted_modules']} ({stats['adaptation_rate']:.1f}%)")
        print(f"   未适配: {stats['not_adapted_modules']} ({100-stats['adaptation_rate']:.1f}%)")
        print()
        
        # 显示直播Bundle统计
        print(f"🎥 直播Bundle (名字中包含Live):")
        print(f"   总数: {stats['live_modules']['total']}")
        print(f"   已适配: {stats['live_modules']['adapted']} ({stats['live_modules']['adaptation_rate']:.1f}%)")
        print(f"   未适配: {stats['live_modules']['not_adapted']} ({100-stats['live_modules']['adaptation_rate']:.1f}%)")
        print()
        
        # 显示非直播Bundle统计
        print(f"📱 非直播Bundle:")
        print(f"   总数: {stats['non_live_modules']['total']}")
        print(f"   已适配: {stats['non_live_modules']['adapted']} ({stats['non_live_modules']['adaptation_rate']:.1f}%)")
        print(f"   未适配: {stats['non_live_modules']['not_adapted']} ({100-stats['non_live_modules']['adaptation_rate']:.1f}%)")
        print()
        
        # 显示未适配的模块列表
        if categorized['not_adapted']:
            print("📋 未适配的模块列表:")
            
            # 分类显示
            live_not_adapted = [m for m in categorized['not_adapted'] if 'live' in m['moduleName'].lower()]
            non_live_not_adapted = [m for m in categorized['not_adapted'] if 'live' not in m['moduleName'].lower()]
            
            if live_not_adapted:
                print("  🎥 直播Bundle:")
                for module in live_not_adapted:
                    print(f"    - {module['moduleName']}")
            
            if non_live_not_adapted:
                print("  📱 非直播Bundle:")
                for module in non_live_not_adapted:
                    print(f"    - {module['moduleName']}")
        
        return categorized
