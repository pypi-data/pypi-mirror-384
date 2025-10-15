from enum import Enum
from typing import Optional

from galtea.utils.from_camel_case_base_model import FromCamelCaseBaseModel


class RiskLevel(str, Enum):
    GPAI = "GPAI"
    GPAI_SYNTHETIC = "GPAI_SYSTEMIC"
    HIGH = "HIGH"
    PROHIBITED = "PROHIBITED"
    SPECIAL_SYSTEM = "SPECIAL_SYSTEM"


class OperatorType(str, Enum):
    AUTHORISED_REPRESENTATIVE = "AUTHORISED_REPRESENTATIVE"
    DEPLOYER = "DEPLOYER"
    DISTRIBUTER = "DISTRIBUTER"
    IMPORTER = "IMPORTER"
    PRODUCT_MANUFACTURER = "PRODUCT_MANUFACTURER"
    PROVIDER = "PROVIDER"


class ProductBase(FromCamelCaseBaseModel):
    name: str
    description: str
    risk_level: Optional[RiskLevel] = None
    operator_type: Optional[OperatorType] = None
    security_boundaries: Optional[str] = None
    capabilities: Optional[str] = None
    policies: Optional[str] = None
    inabilities: Optional[str] = None


class Product(ProductBase):
    id: str
    organization_id: str
    created_at: str
    deleted_at: Optional[str] = None
