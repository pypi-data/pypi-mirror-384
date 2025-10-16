"""
AI Agent接口 - 与外部AI服务集成，提供智能代码合并能力
"""

import os
import json
import time
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from abc import ABC

from .AiMergeConfig import AGENT_PROMPTS, TOKEN


@dataclass
class AIResponse:
    """AI响应数据结构"""
    success: bool
    content: str
    confidence: float
    reasoning: str
    suggestions: List[str]
    error: Optional[str] = None


class BaseAIProvider(ABC):
    """AI服务提供者基类"""

    def __init__(self, provider: str, api_key: str = TOKEN, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://ai-gateway.corp.kuaishou.com/v2/chat/completions"
        self.provider = provider
    
    def analyzeCodeConflict(self, current_code: str, harmony_code: str, 
                            file_type: str) -> AIResponse:
        """分析代码冲突"""
        prompt = AGENT_PROMPTS.getConflictAnalysisPrompt(
            current_code, harmony_code, file_type
        )
        return self._makeRequest(prompt)
    
    def generateMergeStrategy(self, conflicts: List[Dict]) -> AIResponse:
        """生成合并策略"""
        prompt = AGENT_PROMPTS.getMergeExecutionPrompt(conflicts, {})
        return self._makeRequest(prompt)
    
    def executeMerge(self, current_code: str, harmony_code: str) -> AIResponse:
        """执行代码合并"""
        prompt = f"""
根据以下策略合并代码：

当前代码：
{current_code}

Harmony代码：
{harmony_code}

合并策略：
1、仅修改冲突块，其余保持原样。
2、冲突块保留 harmony 特有标记（含“harmony”字符串的行）。
3、保证代码语法正确。

输出纯代码，不要```、语言标记及任何解释。
"""
        return self.makeRequest(prompt)

    def makeRequest(self, prompt: str) -> AIResponse:
       """发送请求到Kwaipilot API"""
       headers = {
            "x-dmo-provider": self.provider,
            "authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
       data = {
            "model": self.model,
            "stream": False,  # 修改为非流式响应
            "messages": [
                {
                    "role": "system", 
                    "content": "你是一个专业的代码合并专家，专门处理React Native鸿蒙适配相关的代码合并。"
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": 0.1
       }
        
       try:
            startTime = time.time()
            response = requests.post(self.base_url, headers=headers, json=data, timeout=300)
            response.raise_for_status()
            
            # 检查响应内容
            response_text = response.text
            print(f"响应内容: {response_text[:200]}...")  # 只打印前200个字符
            costTime = time.time() - startTime
            print(f"耗时：{costTime:.2f}秒")
            
            if not response_text.strip():
                raise ValueError("API返回空响应")
            
            try:
                result = response.json()
                
                # 检查响应结构
                if "choices" not in result or not result["choices"]:
                    raise ValueError("API响应格式错误：缺少choices字段")
                
                if "message" not in result["choices"][0]:
                    raise ValueError("API响应格式错误：缺少message字段")
                
                content = result["choices"][0]["message"]["content"]
                
                if not content.strip():
                    raise ValueError("API返回空响应")
                return AIResponse(
                    success=True,
                    content=content,
                    confidence=0.8,  # 默认置信度
                    reasoning="AI analysis completed",
                    suggestions=[],
                )
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                print(f"完整响应内容: {response_text}")
                return AIResponse(
                    success=False,
                    content="",
                    confidence=0.0,
                    reasoning="",
                    suggestions=[],
                    error=f"JSON解析失败: {str(e)}"
                )
            
       except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {e}")
            return AIResponse(
                success=False,
                content="",
                confidence=0.0,
                reasoning="",
                suggestions=[],
                error=f"网络请求失败: {str(e)}"
            )
       except Exception as e:
            print(f"❌ AI请求失败: {e}")
            return AIResponse(
                success=False,
                content="",
                confidence=0.0,
                reasoning="",
                suggestions=[],
                error=str(e)
            )

class KwaipilotProvider(BaseAIProvider):
    """AI服务提供者"""
    
    def __init__(self, api_key: str = TOKEN, model: str = "kwaipilot-32k"):
        super().__init__("kwaipilot", api_key, model)


class OpenAiProvider(BaseAIProvider):
    """AI服务提供者"""
    
    def __init__(self, api_key: str = TOKEN, model: str = "gpt-4o"):
        super().__init__("openai", api_key, model)



class AIAgentManager:
    """AI Agent接口主类"""
    
    def __init__(self, provider: BaseAIProvider = None):
        self.provider = provider
        self.conversation_history = []
        self.mergeStatistics = {
            'total_merges': 0,
            'successful_merges': 0,
            'manual_reviews': 0,
            'auto_resolved': 0
        }
    
    def setProvider(self, provider: BaseAIProvider):
        """设置AI服务提供者"""
        self.provider = provider
    
    def mergeWithAiAgent(self, currentFile: str, backupFile: str, 
                               outputFile: str) -> Dict[str, Any]:
        """使用AI辅助进行代码合并"""
        try:
            # 读取文件内容
            with open(currentFile, 'r', encoding='utf-8') as f:
                current_code = f.read()
            
            with open(backupFile, 'r', encoding='utf-8') as f:
                harmony_code = f.read()
            file_type = os.path.splitext(currentFile)[1]
            # 1. 分析冲突
            # conflict_analysis = self.provider.analyzeCodeConflict(
            #     current_code, harmony_code, file_type
            # )
            # if not conflict_analysis.success:
            #     return {
            #         'success': False,
            #         'error': conflict_analysis.error,
            #         'stage': 'conflict_analysis'
            #     }
            
            # # 2. 生成合并策略
            # conflicts = json.loads(conflict_analysis.content) if conflict_analysis.content else []
            # strategy_response = self.provider.generateMergeStrategy(conflicts)
            # if not strategy_response.success:
            #     return {
            #         'success': False,
            #         'error': strategy_response.error,
            #         'stage': 'strategy_generation'
            #     }
            
            # # 3. 执行合并
            # strategy = json.loads(strategy_response.content) if strategy_response.content else {}
            mergeResponse = self.provider.executeMerge(current_code, harmony_code)
            
            if not mergeResponse.success:
                return {
                    'success': False,
                    'error': mergeResponse.error,
                    'stage': 'merge_execution'
                }
            
            # 4. 保存结果
            with open(outputFile, 'w', encoding='utf-8') as f:
                f.write(mergeResponse.content)
            
            # 5. 更新统计
            self.mergeStatistics['total_merges'] += 1
            if mergeResponse.confidence > 0.8:
                self.mergeStatistics['auto_resolved'] += 1
            else:
                self.mergeStatistics['manual_reviews'] += 1
            
            self.mergeStatistics['successful_merges'] += 1
            
            return {
                'success': True,
                'output_file': outputFile,
                'confidence': mergeResponse.confidence,
                'reasoning': mergeResponse.reasoning,
                'suggestions': mergeResponse.suggestions,
                # 'conflicts_found': len(conflicts),
                # 'merge_strategy': strategy
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stage': 'file_processing'
            }
    
    def getMergeStatistics(self) -> Dict[str, Any]:
        """获取合并统计信息"""
        return self.mergeStatistics.copy()
    
    def resetStatistics(self):
        """重置统计信息"""
        self.mergeStatistics = {
            'total_merges': 0,
            'successful_merges': 0,
            'manual_reviews': 0,
            'auto_resolved': 0
        }