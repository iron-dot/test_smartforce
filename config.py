import os

class Config:
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///smartforce.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# 환경별 설정을 정의할 수도 있습니다.
class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
