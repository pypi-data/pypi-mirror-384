from dataclasses import dataclass

@dataclass
class JsonWebTokenModel:
    iss: str
    sub: str
    aud: str
    exp: int
    iat: int
    nbf: int
    jti: str

@dataclass
class LicenseModel(JsonWebTokenModel):
    license_type: str
    machine_id: str
    features: list[any]
    version: str
