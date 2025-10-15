#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置
"""

from pathlib import Path

from util.BackupManager import BackupManager
from util.GitManager import GitManager
from util.HarmonyDetector import HarmonyDetector
from util.MergeManager import MergeManager
from util.ModuleManager import ModuleManager

class Config:
    
    def __init__(self):
        self.basePath = Path(".").resolve()
        self.harmonyPath = self.basePath / "harmony"
        self.docPath = self.basePath / "doc"
        
        # 确保doc目录存在
        self.docPath.mkdir(exist_ok=True)
        
        # 鸿蒙适配相关配置
        self.harmonyConfig = {
            "react_native_version": "npm:@kds/react-native@0.62.2-ks.18-lixuan-harmony.9",
            "linear_gradient_version": "2.6.4",
            "auto_adapt_version": "0.0.1-alpha.6",
            "krn_cli_version": "0.18.4-harmony.5",
            "resolutions": {
                "@kds/react-native-gesture-handler": "1.7.17-2-oh-SNAPSHOT",
                "@kds/react-native-sound": "0.11.8",
                "@kds/react-native-blur": "3.6.7",
                "@kds/refresh-list": "4.0.8",
                "@kds/lottie-react-native": "4.0.37",
                "@kds/react-native-linear-gradient": "2.6.4",
                "@kds/react-native-tab-view": "^2.16.1-SNAPSHOT"
            }
        }
        self.backupManager = BackupManager()
        self.gitManager = GitManager()
        self.harmonyDetector = HarmonyDetector()
        self.mergeManager = MergeManager()
        self.moduleManager = ModuleManager()
