from marshmallow import ValidationError, EXCLUDE


class AutoClass(object):
    """根据字典自动给类实例字段赋值"""

    def __fill__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self


def _depth_error_msg(err_msg):
    valid_message = []
    field_error = err_msg[1]

    if isinstance(field_error, dict):
        for key, value in field_error.items():
            if isinstance(value, (list, tuple)):
                for item in value:
                    valid_message.append(f"{err_msg[0]}:{key}:{item}")
            elif isinstance(value, dict):
                for field_name, err in value.items():
                    msg_lst = _depth_error_msg(err)
                    for item in msg_lst:
                        valid_message.append(f"{err_msg[0]}:第{key + 1}条:{item}")
    else:
        valid_message.append("{}:{}".format(err_msg[0], ",".join(err_msg[1])))
    return valid_message


class SerializationError(Exception):
    def __init__(self, message: ValidationError, many=False):
        self.validation_error = message
        self.many = many
        super().__init__(message)

    def normalized_messages(self):
        return self.validation_error

    def description_messages(self):
        _valid_message = set()
        if self.many:
            for index, row_err in self.validation_error.messages.items():
                for field_name, msg in row_err.items():
                    lst = _depth_error_msg(msg)
                    _valid_message.add("第{}条:{}".format(index + 1, ",".join(lst)))
        else:
            for field_name, msg in self.validation_error.messages.items():
                lst = _depth_error_msg(msg)
                _valid_message.add(",".join(lst))
        return _valid_message


class Serialization(object):
    """_deserialize"""

    def __init__(self):
        pass

    @staticmethod
    def dump(shema_instance, data, many=False):
        try:
            return shema_instance.dump(data, many=many)
        except ValidationError as ex:
            raise SerializationError(ex, many)

    @staticmethod
    def load(shema_instance, data, many=False):
        try:
            return shema_instance.load(data=data, unknown=EXCLUDE, many=many)
        except ValidationError as ex:
            raise SerializationError(ex, many)
        except Exception as ex:
            raise ex
