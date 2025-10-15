from logstash import LogstashHandler
from logstash.formatter import LogstashFormatterBase, LogstashFormatterVersion1, LogstashFormatterVersion0


class LogstashFormatterVersion3(LogstashFormatterBase):

    def __init__(self, message_type='Logstash', app_name=None, tags=None, fqdn=False):
        super(LogstashFormatterVersion3, self).__init__(message_type, tags, fqdn)
        self.app_name = app_name

    def format(self, record):
        # Create message dict
        message = {
            '@app_name': self.app_name,
            '@timestamp': self.format_timestamp(record.created),
            '@version': '3',
            'message': record.getMessage() + f'{record.funcName}',
            'host': self.host,
            'path': record.pathname,
            'tags': self.tags,
            'type': self.message_type,

            # Extra Fields
            'level': record.levelname,
            'logger_name': record.name,
        }

        # Add extra fields
        message.update(self.get_extra_fields(record))

        # If exception, add debug info
        if record.exc_info:
            message.update(self.get_debug_fields(record))

        return self.serialize(message)


class LsyUDPLogstashHandler(LogstashHandler):
    def __init__(self, host, port=5959, app_name=None, message_type='logstash', tags=None, fqdn=False, version=0):
        super(LsyUDPLogstashHandler, self).__init__(host, port)
        if version == 1:
            self.formatter = LogstashFormatterVersion1(message_type, tags, fqdn)
        elif version == 0:
            self.formatter = LogstashFormatterVersion0(message_type, tags, fqdn)
        else:
            self.formatter = LogstashFormatterVersion3(message_type, app_name, tags, fqdn)


def stash_logging_handler(app):
    elk_host = app.config.get("Logstash_host", '127.0.0.1')
    elk_port = app.config.get("Logstash_port", 5044)
    app_name = app.config.get("Logstash_Name", 'lsy')
    stash_handler = LsyUDPLogstashHandler(elk_host, elk_port, app_name=app_name, version=3)
    return stash_handler
