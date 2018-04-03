# coding=utf-8


class ClientException(Exception):
    pass
class ClockException(ClientException):
    pass
class ParseException(ClientException):
    pass
class NoStringException(ParseException):
    def __init__(self):
        super(NoStringException, self).__init__('no string to parse')
