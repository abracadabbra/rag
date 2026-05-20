"""
澄清机制
检测模糊问题并生成澄清选项
"""

import logging
from typing import List, Optional, Dict, Any

from openai import OpenAI
from api.config import settings

logger = logging.getLogger(__name__)


def get_llm_client():
    """获取 LLM 客户端"""
    if settings.llm_provider == "minimax":
        return OpenAI(
            api_key=settings.minimax_api_key,
            base_url=settings.minimax_api_base
        )
    elif settings.llm_provider == "openai":
        return OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base
        )
    elif settings.llm_provider == "local":
        return OpenAI(
            api_key="dummy",
            base_url=settings.local_llm_base_url
        )
    else:
        raise ValueError(f"未知的 LLM Provider: {settings.llm_provider}")


class ClarificationService:
    """澄清服务"""

    def __init__(self):
        """初始化澄清服务"""
        self.llm_client = get_llm_client()
        self.model = settings.minimax_model if settings.llm_provider == "minimax" else settings.openai_model
        logger.info(f"澄清服务初始化完成 - Model: {self.model}")

    def needs_clarification(
        self,
        query: str,
        conversation_history: List[Dict[str, str]],
        retrieved_docs: List[Dict[str, Any]]
    ) -> tuple[bool, List[str]]:
        """
        判断是否需要澄清

        Args:
            query: 用户问题
            conversation_history: 对话历史
            retrieved_docs: 检索到的文档

        Returns:
            (是否需要澄清, 澄清选项列表)
        """
        # 策略 1：问题过于简短或模糊
        if self._is_too_vague(query):
            options = self._generate_clarification_options(
                query,
                conversation_history,
                retrieved_docs
            )
            if options:
                logger.info(f"检测到模糊问题 - query: {query}, options: {options}")
                return True, options

        # 策略 2：检索到多个不同类别的文档
        if self._has_multiple_categories(retrieved_docs):
            options = self._extract_categories(retrieved_docs)
            if len(options) > 1:
                logger.info(f"检测到多个类别 - query: {query}, categories: {options}")
                return True, options

        return False, []

    def _is_too_vague(self, query: str) -> bool:
        """
        判断问题是否过于模糊

        模糊问题特征：
        - 长度过短（< 5 个字符）
        - 只包含疑问词（"呢"、"吗"、"多少"等）
        - 缺少主语或宾语
        """
        # 去除空格
        query = query.strip()

        # 长度检查
        if len(query) < 5:
            return True

        # 常见模糊问题模式
        vague_patterns = [
            "呢？",
            "呢",
            "多少？",
            "多少",
            "怎么样？",
            "怎么样",
            "如何？",
            "如何",
            "什么？",
            "什么",
        ]

        # 如果问题只是这些模式之一，认为是模糊的
        if query in vague_patterns:
            return True

        # 如果问题以这些模式结尾，且长度很短，认为是模糊的
        for pattern in vague_patterns:
            if query.endswith(pattern) and len(query) <= 10:
                return True

        return False

    def _has_multiple_categories(self, retrieved_docs: List[Dict[str, Any]]) -> bool:
        """
        判断检索结果是否包含多个不同类别

        Args:
            retrieved_docs: 检索到的文档

        Returns:
            是否包含多个类别
        """
        if len(retrieved_docs) < 2:
            return False

        # 提取类别
        categories = set()
        for doc in retrieved_docs:
            metadata = doc.get("metadata", {})
            category = metadata.get("category") or metadata.get("product")
            if category:
                categories.add(category)

        return len(categories) > 1

    def _extract_categories(self, retrieved_docs: List[Dict[str, Any]]) -> List[str]:
        """
        从检索结果中提取类别

        Args:
            retrieved_docs: 检索到的文档

        Returns:
            类别列表
        """
        categories = set()
        for doc in retrieved_docs:
            metadata = doc.get("metadata", {})
            category = metadata.get("category") or metadata.get("product")
            if category:
                categories.add(category)

        return sorted(list(categories))

    def _generate_clarification_options(
        self,
        query: str,
        conversation_history: List[Dict[str, str]],
        retrieved_docs: List[Dict[str, Any]]
    ) -> List[str]:
        """
        使用 LLM 生成澄清选项

        Args:
            query: 用户问题
            conversation_history: 对话历史
            retrieved_docs: 检索到的文档

        Returns:
            澄清选项列表
        """
        # 构建上下文
        history_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in conversation_history[-3:]  # 最近 3 条
        ])

        # 提取文档中的关键信息
        doc_info = []
        for doc in retrieved_docs[:5]:  # 最多 5 个文档
            metadata = doc.get("metadata", {})
            if "rule_name" in metadata:
                doc_info.append(metadata["rule_name"])
            elif "category" in metadata:
                doc_info.append(metadata["category"])

        doc_text = "\n".join([f"- {info}" for info in doc_info])

        # 构建 Prompt
        prompt = f"""
你是一个智能助手，需要判断用户的问题是否需要澄清。

对话历史：
{history_text}

当前问题：{query}

相关文档：
{doc_text}

如果问题明确，返回 "CLEAR"
如果需要澄清，返回 2-3 个澄清选项，格式如下：
CLARIFY:
1. 选项1
2. 选项2
3. 选项3

只返回上述格式，不要有其他内容。
"""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的问答助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200,
                timeout=10.0
            )

            result = response.choices[0].message.content.strip()

            # 解析结果
            if result.startswith("CLARIFY"):
                lines = result.split("\n")[1:]  # 跳过 "CLARIFY:" 行
                options = []
                for line in lines:
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith("-")):
                        # 移除序号
                        option = line.split(".", 1)[-1].strip()
                        option = option.split("-", 1)[-1].strip()
                        if option:
                            options.append(option)

                return options[:3]  # 最多 3 个选项

            return []

        except Exception as e:
            logger.error(f"生成澄清选项失败: {e}", exc_info=True)
            return []


# 全局单例
_clarification_service: Optional[ClarificationService] = None


def get_clarification_service() -> ClarificationService:
    """获取澄清服务单例"""
    global _clarification_service
    if _clarification_service is None:
        _clarification_service = ClarificationService()
    return _clarification_service
