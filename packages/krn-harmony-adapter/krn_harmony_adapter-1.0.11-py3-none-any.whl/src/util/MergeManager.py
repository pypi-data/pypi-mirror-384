"""
代码合并模块
负责智能合并Harmony相关的代码，处理冲突等
"""
import os
import re
from typing import Dict, Any

from util.ai.AiType import AiType
from util.ai.AiAgentManager import AIAgentManager, KwaipilotProvider, OpenAiProvider
from util.HarmonyDetector import HarmonyDetector
from util.merge.CodeMerger import CodeMerger

"""代码合并器"""
class MergeManager(HarmonyDetector):

    def __init__(self):
        super().__init__()
        self.aiAgent = AIAgentManager(OpenAiProvider())
        self.codeMerger = CodeMerger()

    def mergeHarmonyContentByAi(self, currentFile: str, backupFile: str, aiType: str) -> Dict[str, Any]:
        if aiType == AiType.KWAIPILLOT:
            self.aiAgent.setProvider(KwaipilotProvider())
        elif aiType == AiType.OPENAI:
            self.aiAgent.setProvider(OpenAiProvider())
        return self.aiAgent.mergeWithAiAgent(currentFile, backupFile, currentFile)
    
    def getAiMergeStatistics(self) -> Dict[str, Any]:
        return self.aiAgent.getMergeStatistics()
    
    def mergeHarmonyContentByCode(self, currentFile: str, backupFile: str, modulePath: str, originalPath: str) -> Dict[str, Any]:
        # 读取当前文件和备份文件
        with open(currentFile, 'r', encoding='utf-8') as f:
            currentContent = f.read()
        
        with open(backupFile, 'r', encoding='utf-8') as f:
            backupContent = f.read()
        
        # 智能合并
        mergedContent = self.codeMerger.merge_code(currentContent, backupContent)
        
        # 写回文件
        fullOriginalPath = os.path.join(modulePath, originalPath)
        if mergedContent != currentContent:
            with open(fullOriginalPath, 'w', encoding='utf-8') as f:
                f.write(mergedContent)
            print(f"✅ 智能合并文件: {originalPath}")
