"""LLM服务集成"""

import logging
from typing import Any, Dict, List, Optional, Union

import litellm
from litellm import acompletion

from ..utils.config import Config


class LLMService:
    """LLM推理服务类

    基于litellm库，提供统一的LLM调用接口，支持OpenRouter等多种模型提供商。
    """

    def __init__(self, config: Config):
        """初始化LLM服务

        Args:
            config: 配置对象
        """
        self.config = config
        self.logger = logging.getLogger("LLMService")

        # 配置litellm环境变量
        import os

        if config.kimi_api_key:
            # 设置Moonshot API密钥和base URL - litellm标准格式
            os.environ["MOONSHOT_API_KEY"] = config.kimi_api_key
            os.environ["MOONSHOT_BASE_URL"] = config.kimi_base_url
        elif config.openrouter_api_key:
            litellm.api_key = config.openrouter_api_key
            litellm.api_base = config.openrouter_base_url

        # 设置默认参数
        self.default_model = config.default_model
        self.default_temperature = config.default_temperature
        self.default_max_tokens = config.default_max_tokens

        self.logger.info(f"LLM服务初始化完成，默认模型: {self.default_model}")
        self.logger.info(
            f"API基础URL: {config.kimi_base_url if config.kimi_api_key else config.openrouter_base_url}"
        )

    async def chat(
        self,
        messages: Union[str, List[Dict[str, str]]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        """聊天接口

        Args:
            messages: 消息内容，可以是字符串或消息列表
            model: 模型名称，默认使用配置的模型
            temperature: 温度参数，控制输出的随机性
            max_tokens: 最大token数
            system_prompt: 系统提示词
            **kwargs: 其他参数

        Returns:
            LLM响应内容

        Examples:
            # 简单文本对话
            response = await llm.chat("你好")

            # 带系统提示
            response = await llm.chat("介绍一下Python", system_prompt="你是一位编程专家")

            # 多轮对话
            messages = [
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"},
                {"role": "user", "content": "介绍一下Python"}
            ]
            response = await llm.chat(messages)
        """
        try:
            # 准备参数
            model = model or self.default_model
            temperature = (
                temperature if temperature is not None else self.default_temperature
            )
            max_tokens = max_tokens or self.default_max_tokens

            # 构造消息列表
            if isinstance(messages, str):
                message_list = []
                if system_prompt:
                    message_list.append({"role": "system", "content": system_prompt})
                message_list.append({"role": "user", "content": messages})
            else:
                message_list = messages.copy()
                if system_prompt and (
                    not message_list or message_list[0]["role"] != "system"
                ):
                    message_list.insert(0, {"role": "system", "content": system_prompt})

            self.logger.debug(f"调用LLM: {model}, 消息数量: {len(message_list)}")

            # 调用litellm - 明确设置api_base覆盖默认值
            call_kwargs = {
                "model": model,
                "messages": message_list,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs,
            }

            # 如果是Moonshot模型，强制设置正确的api_base
            if model.startswith("moonshot/"):
                call_kwargs["api_base"] = self.config.kimi_base_url

            response = await acompletion(**call_kwargs)

            content = response.choices[0].message.content

            # 记录token使用量
            usage = response.usage
            if usage:
                self.logger.info(
                    f"LLM调用完成 - 输入: {usage.prompt_tokens} tokens, "
                    f"输出: {usage.completion_tokens} tokens, "
                    f"总计: {usage.total_tokens} tokens"
                )

            return content

        except Exception as e:
            self.logger.error(f"LLM调用失败: {e}")
            raise

    async def chat_stream(
        self,
        messages: Union[str, List[Dict[str, str]]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ):
        """流式聊天接口

        Args:
            messages: 消息内容
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            system_prompt: 系统提示词
            **kwargs: 其他参数

        Yields:
            str: 流式响应内容片段
        """
        try:
            # 准备参数
            model = model or self.default_model
            temperature = (
                temperature if temperature is not None else self.default_temperature
            )
            max_tokens = max_tokens or self.default_max_tokens

            # 构造消息列表
            if isinstance(messages, str):
                message_list = []
                if system_prompt:
                    message_list.append({"role": "system", "content": system_prompt})
                message_list.append({"role": "user", "content": messages})
            else:
                message_list = messages.copy()
                if system_prompt and (
                    not message_list or message_list[0]["role"] != "system"
                ):
                    message_list.insert(0, {"role": "system", "content": system_prompt})

            self.logger.debug(f"流式调用LLM: {model}, 消息数量: {len(message_list)}")

            # 流式调用litellm - 明确设置api_base覆盖默认值
            call_kwargs = {
                "model": model,
                "messages": message_list,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
                **kwargs,
            }

            # 如果是Moonshot模型，强制设置正确的api_base
            if model.startswith("moonshot/"):
                call_kwargs["api_base"] = self.config.kimi_base_url

            response = await acompletion(**call_kwargs)

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            self.logger.error(f"流式LLM调用失败: {e}")
            raise

    async def function_call(
        self,
        messages: Union[str, List[Dict[str, str]]],
        functions: List[Dict[str, Any]],
        function_call: Union[str, Dict[str, str]] = "auto",
        model: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """函数调用接口

        Args:
            messages: 消息内容
            functions: 可用函数列表
            function_call: 函数调用策略
            model: 模型名称
            **kwargs: 其他参数

        Returns:
            函数调用结果
        """
        try:
            model = model or self.default_model

            # 构造消息列表
            if isinstance(messages, str):
                message_list = [{"role": "user", "content": messages}]
            else:
                message_list = messages

            self.logger.debug(f"函数调用: {model}, 函数数量: {len(functions)}")

            # 调用litellm
            response = await acompletion(
                model=model,
                messages=message_list,
                functions=functions,
                function_call=function_call,
                **kwargs,
            )

            return response.choices[0].message

        except Exception as e:
            self.logger.error(f"函数调用失败: {e}")
            raise

    def set_api_key(self, api_key: str):
        """设置API密钥"""
        litellm.api_key = api_key
        self.logger.info("API密钥已更新")

    def set_base_url(self, base_url: str):
        """设置API基础URL"""
        litellm.api_base = base_url
        self.logger.info(f"API基础URL已更新: {base_url}")

    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        # 常用的OpenRouter模型
        return [
            "openai/gpt-4",
            "openai/gpt-4-turbo",
            "openai/gpt-3.5-turbo",
            "anthropic/claude-3-haiku",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-opus",
            "google/gemini-pro",
            "meta-llama/llama-2-70b-chat",
            "mistralai/mistral-7b-instruct",
            "cohere/command-r",
        ]
