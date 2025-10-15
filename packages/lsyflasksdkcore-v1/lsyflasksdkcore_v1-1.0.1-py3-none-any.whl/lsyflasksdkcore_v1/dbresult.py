# -*- coding: utf-8 -*-

from functools import wraps
from typing import Dict
from typing import List, Tuple, TypeVar, Generic, Optional

from marshmallow.types import StrSequenceOrSet

from lsyflasksdkcore_v1.linq import LinqQuery
from lsyflasksdkcore_v1.utils.lazy import lazy_property
from lsyflasksdkcore_v1.serialization import Serialization, SerializationError

T = TypeVar("T")


class DBResult(Generic[T]):
    def __init__(self, data, schema_class, many: bool = False):
        """
        封装数据库查询结果，支持序列化和类型提示。
        :param data: 原始数据
        :param schema_class: 序列化类
        :param many: 是否为多条数据
        """
        self.original_data = data
        self.schema_class = schema_class
        self.many = many
        self._exclude: StrSequenceOrSet = ()
        self._include: Optional[StrSequenceOrSet] = None
        self._cached_data = None  # 缓存序列化后的数据

    def set_exclude(self, exclude: StrSequenceOrSet):
        """设置需要排除的字段"""
        self._exclude = exclude
        return self

    def set_include(self, include: StrSequenceOrSet):
        """设置需要包含的字段"""
        self._include = include
        return self

    @lazy_property
    def schema_instance(self):
        """获取序列化类实例"""
        return self.schema_class(exclude=self._exclude, only=self._include)

    @lazy_property
    def _json(self):
        """序列化为 JSON 格式"""
        if not self.original_data:
            return [] if self.many else {}

        try:
            return Serialization.dump(self.schema_instance, self.original_data, self.many)
        except SerializationError as ex:
            raise SerializationError(f"Error serializing data: {ex}")

    @lazy_property
    def _data(self):
        """反序列化为 Python 对象"""
        if not self._json:
            return [] if self.many else {}

        try:
            return Serialization.load(self.schema_instance, self._json, self.many)
        except SerializationError as ex:
            raise SerializationError(f"Error deserializing data: {ex}")

    def to_json(self) -> Dict:
        """返回 JSON 格式数据"""
        return self._json

    def to_data(self) -> T:
        """返回单条数据的 Python 对象"""
        if self.many:
            raise ValueError("to_data() is not applicable for multiple results. Use to_list() instead.")
        return self._data

    def to_list(self) -> List[T]:
        """返回多条数据的 Python 对象列表"""
        if not self.many:
            return [self._data] if self._data else []
        return self._data

    def to_query(self) -> LinqQuery[T]:
        """返回 LinqQuery 对象，支持链式查询"""
        return LinqQuery(self._data)

    @staticmethod
    def entity(schema_class):
        """装饰器：将单条查询结果封装为 DBResult"""

        def _query(func):
            @wraps(func)
            def __query(self, *args, **kwargs) -> DBResult:
                # 判断传入的是 lambda 还是 schema_class 类本身
                resolved_schema_class = schema_class(self) if isinstance(schema_class,
                                                                         type(lambda: None)) else schema_class
                result = func(self, *args, **kwargs)
                dbr = DBResult(result, resolved_schema_class, False)
                return dbr

            return __query

        return _query

    @staticmethod
    def list(schema_class):
        """装饰器：将多条查询结果封装为 DBResult"""

        def _query(func):
            @wraps(func)
            def __query(self, *args, **kwargs) -> DBResult:
                # 判断传入的是 lambda 还是 schema_class 类本身
                resolved_schema_class = schema_class(self) if isinstance(schema_class,
                                                                         type(lambda: None)) else schema_class
                result = func(self, *args, **kwargs)
                dbr = DBResult(result, resolved_schema_class, True)
                return dbr

            return __query

        return _query

    @staticmethod
    def pager(schema_class):
        """装饰器：将分页查询结果封装为 DBResult"""

        def _pager(func):
            @wraps(func)
            def __pager(self, *args, **kwargs) -> Tuple[DBResult, int]:
                # 判断传入的是 lambda 还是 schema_class 类本身
                resolved_schema_class = schema_class(self) if isinstance(schema_class,
                                                                         type(lambda: None)) else schema_class
                result, count = func(self, *args, **kwargs)
                dbr = DBResult(result, resolved_schema_class, True)
                return dbr, count

            return __pager

        return _pager
