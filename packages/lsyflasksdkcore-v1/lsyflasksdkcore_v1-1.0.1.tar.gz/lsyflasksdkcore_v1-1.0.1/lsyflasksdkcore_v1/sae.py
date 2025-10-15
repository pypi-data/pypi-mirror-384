from abc import ABCMeta, abstractmethod
import functools
from typing import Optional

from flask import abort, request
from flask_login import LoginManager


class AuthUserABC(metaclass=ABCMeta):
    @property
    @abstractmethod
    def is_active(self) -> bool:
        pass

    @property
    @abstractmethod
    def is_authenticated(self) -> bool:
        return True

    @property
    @abstractmethod
    def is_superuser(self) -> bool:
        pass

    @property
    @abstractmethod
    def system_role_id(self) -> str:
        pass

    @property
    @abstractmethod
    def is_anonymous(self) -> bool:
        return False

    @abstractmethod
    def get_id(self):
        pass

    @abstractmethod
    def get_name(self):
        pass


def require_share_key(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        share_key = request.args.get("Share-Key") or request.headers.get("Share-Key")
        if share_key != "7FC512C1-0304-449E-A970-449A973D545E":
            abort(401)
        return f(*args, **kwargs)

    return decorated_function


class TokenManagerABC(metaclass=ABCMeta):

    def init_app(self, app):
        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.request_loader(self.request_loader)

    @abstractmethod
    def request_loader(self, request) -> Optional[AuthUserABC]:
        pass
