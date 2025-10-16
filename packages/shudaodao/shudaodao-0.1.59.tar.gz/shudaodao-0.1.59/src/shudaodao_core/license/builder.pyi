from ..utils.core_utils import CoreUtil as CoreUtil
from .model import LicenseModel as LicenseModel
from _typeshed import Incomplete

class LicenseBuilder:
    license: Incomplete
    def __init__(self) -> None: ...
    def generate(
        self,
        *,
        customer_id=None,
        machine_id=None,
        features=None,
        valid_days=None,
        license_type=None,
        product_name=None,
    ): ...
