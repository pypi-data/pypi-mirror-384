from .loader import ConfigLoader as ConfigLoader
from .schemas.app_config import AppConfigSetting as AppConfigSetting

class AppConfigLoader:
    """应用配置加载器，实现配置的单例加载与基础验证。

    该类确保整个应用生命周期中仅加载一次配置（惰性单例），
    并在加载后执行必要的安全与环境合规性检查。
    """
    @classmethod
    def load_config(cls) -> AppConfigSetting:
        """加载并返回应用配置实例（单例）。

        首次调用时从配置文件中读取 'SmartShudao' 节点并解析为 AppConfigSetting 对象，
        后续调用直接返回缓存实例。

        Returns:
            AppConfigSetting: 解析后的应用配置对象。

        Raises:
            ValueError: 当配置文件中缺少 'SmartShudao' 根节点时。
            Exception: 配置解析或加载过程中发生的其他异常（如文件不存在、格式错误等）。
        """

AppConfig: AppConfigSetting
