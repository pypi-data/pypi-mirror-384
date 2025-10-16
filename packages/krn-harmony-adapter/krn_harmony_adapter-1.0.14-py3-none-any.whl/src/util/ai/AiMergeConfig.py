"""
AI代码合并配置 - 定义Agent的行为策略和规则
"""

from typing import Dict, List


class AgentPromptTemplates:
    """Agent提示词模板"""
    
    @staticmethod
    def getConflictAnalysisPrompt(current_code: str, harmony_code: str, 
                                   file_type: str) -> str:
        """获取冲突分析提示词"""
        return f"""
你是一个专业的代码合并专家，专门处理React Native鸿蒙适配相关的代码合并。

当前任务：分析以下两个代码版本的冲突，并提供合并建议。

文件类型：{file_type}

当前分支代码：
{current_code}

Harmony分支代码：
{harmony_code}

请分析：
1. 两个版本的主要差异
2. 哪些是harmony相关的修改
3. 哪些是业务逻辑的修改
4. 推荐的合并策略

合并原则：
- 优先保留harmony相关的代码和配置
- 保留最新的业务逻辑
- 确保代码语法正确
- 保持原有的代码格式
"""
    
    @staticmethod
    def getMergeExecutionPrompt(conflicts: List[Dict], strategy: Dict) -> str:
        """获取合并执行提示词"""
        return f"""
你是一个代码合并执行器，需要根据分析结果执行具体的代码合并。

冲突列表：
{conflicts}

合并策略：
{strategy}

请执行合并并返回：
1. 合并后的完整代码
2. 合并过程中的关键决策
3. 需要人工确认的部分
4. 合并后的验证建议
"""
    
    @staticmethod
    def getValidationPrompt(merged_code: str, original_harmony_patterns: List[str]) -> str:
        """获取验证提示词"""
        return f"""
你是一个代码质量验证专家，需要验证合并后的代码是否正确。

合并后的代码：
{merged_code}

原始harmony模式：
{original_harmony_patterns}

请验证：
1. 所有harmony相关的代码是否正确保留
2. 代码语法是否正确
3. 是否有重复或冲突的代码
4. 是否符合鸿蒙适配的要求

返回验证结果和修复建议。
"""


# 全局配置实例
AGENT_PROMPTS = AgentPromptTemplates()
TOKEN = "y8hXEHS30tN3ik"