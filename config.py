import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{os.environ.get('DB_USER')}:"
        f"{os.environ.get('DB_PASSWORD')}@"
        f"{os.environ.get('DB_HOST')}:"
        f"{os.environ.get('DB_PORT')}/"
        f"{os.environ.get('DB_NAME')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
