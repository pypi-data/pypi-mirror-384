from app.utils.constants.environment import Environment
from dotenv import load_dotenv
from logyca import parse_bool
from pathlib import Path
import os

env_path= Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    def __init__(self) -> None:
        self.DB_HOST: str = os.getenv(Environment.PostgreSQL.HOST)
        self.DB_NAME: str = os.getenv(Environment.PostgreSQL.DB_NAME)
        self.DB_PASS: str = os.getenv(Environment.PostgreSQL.PASSWORD)
        self.DB_PORT: int = int(os.getenv(Environment.PostgreSQL.PORT))
        self.DB_USER: str = os.getenv(Environment.PostgreSQL.USER)
        self.DB_SSL: bool = parse_bool(os.getenv(Environment.PostgreSQL.SSL))

        self.mandatory_attribute_validation()

    def mandatory_attribute_validation(self):
        attributes = vars(self)
        none_attributes = [attr for attr, value in attributes.items() if value is None]
        if len(none_attributes)!=0:
            raise KeyError(f"The following environment variables have not been created: {none_attributes}")

settings = Settings()
