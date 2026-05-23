from pydantic import BaseModel
from typing import Optional

class BrandGuidelines(BaseModel):
    tone: str = ""
    colors: list[str] = []
    fonts: list[str] = []
    keywords: list[str] = []
    avoid: list[str] = []

class SocialAccounts(BaseModel):
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    tiktok: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None

class ClientCreate(BaseModel):
    name: str
    industry: str
    brand_guidelines: BrandGuidelines = BrandGuidelines()
    social_accounts: SocialAccounts = SocialAccounts()

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    brand_guidelines: Optional[BrandGuidelines] = None
    social_accounts: Optional[SocialAccounts] = None
    active: Optional[bool] = None

class ClientOut(BaseModel):
    id: int
    name: str
    industry: str
    brand_guidelines: dict
    social_accounts: dict
    active: bool

    model_config = {"from_attributes": True}
