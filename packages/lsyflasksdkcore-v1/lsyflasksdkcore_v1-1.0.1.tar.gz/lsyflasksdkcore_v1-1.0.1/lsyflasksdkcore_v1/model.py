# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from typing import Callable, List, Tuple, TypeVar, Generic, Union, Type

from marshmallow import ValidationError
from sqlalchemy import and_, literal, func, union_all
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, aliased

from lsyflasksdkcore_v1.dbresult import DBResult
from lsyflasksdkcore_v1.exceptions import DBError, DBRefError
from lsyflasksdkcore_v1.schema import Schema, DBRefSchema, DBRef

T = TypeVar("T")


class BaseModel(Generic[T], metaclass=ABCMeta):
    """通用数据库操作基类"""

    @property
    @abstractmethod
    def session(self) -> Session:
        """获取数据库会话"""
        raise NotImplementedError("Subclasses must implement the 'session' property.")

    @property
    @abstractmethod
    def model_class(self):
        """获取模型类"""
        raise NotImplementedError("Subclasses must implement the 'model_class' property.")

    @property
    @abstractmethod
    def schema_class(self) -> Type[Schema]:
        """获取 Schema 类"""
        raise NotImplementedError("Subclasses must implement the 'schema_class' property.")

    @property
    def primary_keys(self) -> Union[str, List[str]]:
        """
        获取主键字段，支持单主键和联合主键。
        默认主键为 'id'，子类可覆盖此属性。
        """
        return "id"

    @property
    def ref_tables(self) -> list:
        """定义外键关联信息"""
        return []

    @property
    def effective_conditions(self) -> dict:
        """
        数据有效性判定字段
        """
        return {"status": 1}

    def _get_sorted(self, sort: str = None, order: str = None, model_class=None):
        """获取排序字段"""
        if sort and order:
            if model_class is None:
                model_class = self.model_class
            return getattr(getattr(model_class, sort), order)()
        return None

    def _execute(self, _func: Callable, *args, **kwargs):
        """通用执行方法，封装异常处理"""
        try:
            return _func(*args, **kwargs)
        except ValidationError as ex:
            raise DBError(f"Validation error: {ex}")
        except SQLAlchemyError as ex:
            self.session.rollback()
            raise DBError(f"Database error: {ex}")
        except Exception as ex:
            raise DBError(f"Unexpected error: {ex}")

    def _apply_sort(self, query, sort: str, order: str, model_class=None):
        """应用排序"""
        _sorted = self._get_sorted(sort, order, model_class)
        return query.order_by(_sorted) if _sorted is not None else query

    def _build_primary_key_filter(self, primary_key_values: Union[str, dict]) -> Callable:
        """
        构建主键过滤条件。
        :param primary_key_values: 主键值（单主键为字符串，联合主键为字典）
        :return: SQLAlchemy 过滤条件
        """
        if isinstance(self.primary_keys, str):
            # 单主键
            return lambda query: query.filter(getattr(self.model_class, self.primary_keys) == primary_key_values)
        elif isinstance(self.primary_keys, list):
            # 联合主键
            if not isinstance(primary_key_values, dict):
                raise ValueError("For composite primary keys, primary_key_values must be a dictionary.")
            return lambda query: query.filter(*[getattr(self.model_class, key) == primary_key_values[key] for key in self.primary_keys])
        else:
            raise ValueError("primary_keys must be a string or a list of strings.")

    @DBResult.list(DBRefSchema)
    def get_refer(self, primary_key_values: Union[str, dict], references: list = None) -> DBResult[DBRef]:
        """检查外键关联信息"""

        if references is None:
            references = self.ref_tables or []

        def create_query(table, ref_desc, filter_condition):
            return (
                self.session.query(literal(table.__tablename__).label("ref_code"), literal(ref_desc).label("ref_desc"), func.count("*").label("ref_count"))
                .select_from(table)
                .filter(filter_condition)
            )

        queries = []
        for ref in references:
            # 关联方式
            link = ref.get("link", "eq")
            if isinstance(primary_key_values, dict):
                # 复合主键(一般复合主键不会用于外键关联)
                condition = and_(*[getattr(ref["table"], key) == primary_key_values[key] for key in primary_key_values])
            else:
                if link == "in":
                    condition = getattr(ref["table"], ref["primary_key"]).any(primary_key_values)
                else:
                    condition = getattr(ref["table"], ref["primary_key"]) == primary_key_values
            queries.append(create_query(ref["table"], ref["desc"], condition))

        if queries:
            union_query = union_all(*queries)
            t = aliased(union_query.subquery())
            return self._execute(lambda: self.session.query(t).filter(t.c.ref_count > 0).all())

    @DBResult.entity(schema_class=lambda self: self.schema_class)
    def get_one_base(self, primary_key_values: Union[str, dict]) -> DBResult[T]:
        """根据主键获取单条数据"""
        filter_condition = self._build_primary_key_filter(primary_key_values)
        return self._execute(lambda: filter_condition(self.session.query(self.model_class)).first())

    @DBResult.list(schema_class=lambda self: self.schema_class)
    def get_all_base(self, sort: str = None, order: str = "asc") -> DBResult[List[T]]:
        """获取所有数据"""
        return self._execute(lambda: self._apply_sort(self.session.query(self.model_class), sort, order).all())

    def get_count_base(self) -> int:
        """查询表数据的总条数"""
        return self._execute(lambda: self.session.query(self.model_class).count())

    @DBResult.list(schema_class=lambda self: self.schema_class)
    def get_all_effective(self, sort: str = None, order: str = None) -> DBResult[List[T]]:
        """获取有效数据，支持通过配置字段和值的方式设置默认查询条件"""

        def _inner():
            q = self.session.query(self.model_class)
            # 从子类配置中获取默认条件
            # filters = [getattr(self.model_class, key) == value for key, value in self.effective_conditions.items()]
            filters = [getattr(self.model_class, key) == value for key, value in self.effective_conditions.items() if hasattr(self.model_class, key)]  # 判断是否包含对应属性
            q = q.filter(and_(*filters))
            return self._apply_sort(q, sort, order).all()

        return self._execute(_inner)

    @DBResult.pager(schema_class=lambda self: self.schema_class)
    def get_page_base(self, limit: int = 10, offset: int = 0, sort: str = None, order: str = "asc") -> Tuple[DBResult[List[T]], int]:
        """
        分页查询数据
        :param limit: 每页记录数
        :param offset: 偏移量
        :param sort: 排序字段
        :param order: 排序方式（asc 或 desc）
        :return: 查询结果列表和总记录数
        :return: 查询结果列表和总记录数
        """

        def _inner():
            q = self.session.query(self.model_class)
            count = q.count()
            rows = self._apply_sort(q, sort, order).limit(limit).offset(offset).all()
            return rows, count

        return self._execute(_inner)

    def add_base(self, entity: T, exclude=None) -> dict:
        """新增数据"""

        def _inner():
            if exclude:
                schema = self.schema_class(exclude=exclude)
            else:
                schema = self.schema_class()
            data = schema.dump(entity)
            row = self.model_class(**data)
            self.session.add(row)
            self.session.commit()
            return data

        return self._execute(_inner)

    def tran_import_base(self, entities: List[T]) -> None:
        """批量导入数据"""

        def _inner():
            schema = self.schema_class()
            rows = [self.model_class(**schema.dump(entity)) for entity in entities]
            self.session.add_all(rows)
            self.session.commit()

        self._execute(_inner)

    def modify_base(self, primary_key_values: Union[str, dict], entity: T) -> None:
        """修改数据"""

        def _inner():
            schema = self.schema_class()
            data = schema.dump(entity)
            filter_condition = self._build_primary_key_filter(primary_key_values)
            filter_condition(self.session.query(self.model_class)).update(data)
            self.session.commit()

        self._execute(_inner)

    def tran_delete_base(self, primary_key_values_list: List[Union[str, dict]]) -> None:
        """批量删除数据"""
        if self.ref_tables:
            for primary_key_values in primary_key_values_list:
                refs = self.get_refer(primary_key_values, self.ref_tables).to_list()
                if refs:
                    raise DBRefError(refs.pop())

        def _inner():
            for primary_key_values1 in primary_key_values_list:
                filter_condition = self._build_primary_key_filter(primary_key_values1)
                filter_condition(self.session.query(self.model_class)).delete()
            self.session.commit()

        self._execute(_inner)

    def delete_base(self, primary_key_values: Union[str, dict]) -> None:
        """删除单条数据"""
        self.tran_delete_base([primary_key_values])

        """
        if self.ref_tables:
            refs = self.get_refer(primary_key_values, self.ref_tables).to_list()
            if refs:
                raise DBRefError(refs.pop())

        def _inner():
            filter_condition = self._build_primary_key_filter(primary_key_values)
            filter_condition(self.session.query(self.model_class)).delete()
            self.session.commit()

        self._execute(_inner)
        """
