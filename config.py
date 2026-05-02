from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from typing import List


class Settings(BaseSettings):
    FH_TOKEN: str
    BOT_TOKEN: SecretStr
    # CHAT_ID — comma-separated list of chat ids ("193727188,1325581898").
    # Зберігаємо як string і парсимо через chat_ids_list — щоб додати другого адміна
    # не треба міняти схему.
    CHAT_ID: str
    GEMINI_KEYS: str
    # Optional: comma-separated Freelancehunt skill IDs to filter by
    # (e.g. "68,96" — Online Stores + Website Development).
    # Empty → нотіфікації йдуть про всі нові проєкти, без фільтра.
    FILTER_SKILL_IDS: str = ""

    @property
    def gemini_keys_list(self) -> List[str]:
        return [k.strip() for k in self.GEMINI_KEYS.split(",") if k.strip()]

    @property
    def chat_ids_list(self) -> List[int]:
        return [int(c.strip()) for c in str(self.CHAT_ID).split(",") if c.strip()]

    @property
    def filter_skill_ids_set(self) -> set:
        return {int(s.strip()) for s in self.FILTER_SKILL_IDS.split(",") if s.strip()}

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
