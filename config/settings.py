import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    sf_url: str
    sf_username: str
    sf_password: str
    sf_token: str
    sf_api_base_url: str
    sf_api_version: str
    headless: bool

    @property
    def api_limits_endpoint(self) -> str:
        base = self.sf_api_base_url.rstrip("/")
        return f"{base}/services/data/{self.sf_api_version}/limits"


def get_settings() -> Settings:
    return Settings(
        sf_url=os.getenv("SF_URL", "https://login.salesforce.com"),
        sf_username=os.getenv("SF_USERNAME", ""),
        sf_password=os.getenv("SF_PASSWORD", ""),
        sf_token=os.getenv("SF_TOKEN", ""),
        sf_api_base_url=os.getenv("SF_API_BASE_URL", ""),
        sf_api_version=os.getenv("SF_API_VERSION", "v61.0"),
        headless=os.getenv("HEADLESS", "true").lower() == "true",
    )
