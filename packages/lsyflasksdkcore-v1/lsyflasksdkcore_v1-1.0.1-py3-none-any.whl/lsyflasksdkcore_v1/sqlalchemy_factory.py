from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base


class SQLAlchemyFactory:
    """SQLAlchemy 工厂类，提供数据库和模型的初始化与访问"""

    _instance = None  # 单例实例

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SQLAlchemyFactory, cls).__new__(cls, *args, **kwargs)
            cls._instance._db = SQLAlchemy()
        return cls._instance

    def init_app(self, app) -> None:
        """初始化 Flask 应用"""
        self._db.init_app(app)

    @property
    def db(self) -> SQLAlchemy:
        """获取 SQLAlchemy 实例"""
        return self._db

    @db.setter
    def db(self, value: SQLAlchemy):
        """设置 SQLAlchemy 实例"""
        self._db = value

    @staticmethod
    def create_db_model(schema: str = None):
        """创建自定义的数据库模型基类"""

        if schema:
            custom_metadata = MetaData(schema=schema)
        else:
            custom_metadata = MetaData()
        return declarative_base(metadata=custom_metadata)


# 单例实例
sqlalchemy_factory = SQLAlchemyFactory()
