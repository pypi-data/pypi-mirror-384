"""错误类型定义 - 支持智能化重试机制

根据错误类型进行分类：
- RetryableError: 可重试的错误（临时性网络问题、超时、限流）
- NonRetryableError: 不可重试的错误（格式错误、业务逻辑错误）

智能体消息处理过程中会抛出对应的错误类型，MessageBroker
根据错误类型决定是否重试。
"""


class RetryableError(Exception):
    """可重试的错误基类

    这类错误表示操作可能在稍后成功，应该进行重试。
    常见场景：网络抖动、服务临时不可用、限流等
    """

    pass


class NonRetryableError(Exception):
    """不可重试的错误基类

    这类错误表示操作不应该重试，需要立即失败。
    常见场景：消息格式错误、业务逻辑错误等
    """

    pass


# === 具体的可重试错误类型 ===


class NetworkError(RetryableError):
    """网络错误

    场景：网络连接失败、超时、DNS解析失败等
    重试策略：适合指数退避重试
    """

    pass


class LLMTimeoutError(RetryableError):
    """LLM处理超时错误

    场景：调用LLM时超过指定时间
    重试策略：适合指数退避重试，可能是临时的性能波动
    """

    pass


class LLMRateLimitError(RetryableError):
    """LLM限流错误

    场景：LLM API限流（Too Many Requests 429）
    重试策略：需要更大的延迟才能成功，建议指数退避重试
    """

    pass


class ServiceUnavailableError(RetryableError):
    """服务暂时不可用

    场景：服务状态为503 Service Unavailable
    重试策略：适合指数退避重试，等待服务恢复
    """

    pass


# === 具体的不可重试错误类型 ===


class MessageFormatError(NonRetryableError):
    """消息格式错误

    场景：JSON解析失败、必要字段缺失等
    处理策略：立即失败，发送到死信队列，需要人工处理
    """

    pass


class BusinessLogicError(NonRetryableError):
    """业务逻辑错误

    场景：参数验证失败、业务规则违反等
    处理策略：立即失败，发送到死信队列，需要人工审查
    """

    pass


class AuthenticationError(NonRetryableError):
    """认证错误

    场景：API密钥无效、权限不足等
    处理策略：立即失败，需要修复配置或权限
    """

    pass


class InvalidMessageError(NonRetryableError):
    """无效的消息类型或结构

    场景：消息类型不支持、必要信息缺失等
    处理策略：立即失败，发送到死信队列
    """

    pass


class ConfigurationError(NonRetryableError):
    """配置错误

    场景：智能体配置有误、必需参数缺失等
    处理策略：立即失败，需要修复配置
    """

    pass
