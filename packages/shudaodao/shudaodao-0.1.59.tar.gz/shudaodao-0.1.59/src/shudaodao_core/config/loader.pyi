from ..utils.core_utils import CoreUtil as CoreUtil

class ConfigLoader:
    """
    配置加载器，负责从多个 YAML 文件中按环境合并配置。

    加载顺序：
    1. 加载 `base.yaml` 作为基础配置；
    2. 根据 `SmartShudao.environment.model` 的值（如 `dev` 或 `prod`），
       加载对应环境配置（如 `dev.yaml`）和密钥文件（如 `secrets/dev.yaml`）；
    3. 合并所有配置，并可选地将最终结果写入 `environment.yaml` 用于调试。

    合并策略：
    1. 字典：递归合并；
    2. 列表：若元素为字典且包含指定 `key_field`（默认 `name`），则按键合并（覆盖）；
      否则直接拼接；
    3. 基本类型（str/int/bool）：直接覆盖。

    """
    @classmethod
    def open(cls):
        """加载并合并应用配置，返回完整的配置字典。

        首先加载 `base.yaml`，从中读取环境模式（`environment.model`），
        然后加载对应环境的 YAML 文件进行合并。

        Returns:
            dict: 合并后的完整配置字典，包含 'SmartShudao' 根节点。

        Raises:
            ValueError: 若 base.yaml 不是字典，或 environment.model 为未知值。
            FileNotFoundError / yaml.YAMLError: 若配置文件缺失或格式错误。
        """
