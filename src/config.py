from functools import lru_cache

from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """App Settings"""
    DEBUG: str = 'False'
    ENVIRONMENT: str = 'local'
    INST_USERNAME: str = ''
    INST_PASSWORD: str = ''
    REDIS_HOST: str = 'localhost'
    REDIS_PORT: int | str = '6379'
    CORS_ORIGIN: str = ''
    SELENOID_HOST: str = ''
    SELENOID_PORT: int | str = ''
    DB_HOST: str = 'localhost'
    DB_PORT: int | str = '5432'
    DB_NAME: str = 'glam_db'
    DB_USER: str = 'glam_user'
    DB_PASSWORD: str = 'glam12345678'
    ACCEPTED_USERS: str = ''

    @property
    def accepted_users_list(self):
        return self.ACCEPTED_USERS.split(',')

    @property
    def get_db_url(self):
        return (f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}'
                f'@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}')


@lru_cache
def get_settings() -> AppSettings:
    """Gets env config"""
    settings = AppSettings()
    return settings
