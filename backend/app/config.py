from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Realtime Global News'
    api_prefix: str = '/api'

    database_url: str = 'postgresql+asyncpg://postgres:postgres@localhost:5432/realtime_news'
    poll_seconds: int = 60

    request_timeout_seconds: int = 20
    max_articles_per_source: int = 30
    feed_max_retries: int = 2
    feed_retry_backoff_seconds: float = 1.5
    retry_queue_batch_size: int = 20
    retry_max_attempts: int = 5
    retry_initial_delay_seconds: int = 120
    user_agent: str = (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/122.0.0.0 Safari/537.36'
    )

    enable_translation: bool = True
    translation_source_lang: str = 'en'
    translation_target_lang: str = 'zh-CN'


settings = Settings()
