class NotFoundError(Exception):
    """记录未找到错误"""

    def __init__(self, message: str = "Record not found"):
        super().__init__(message)


class MultipleRecordsError(Exception):
    """多条记录错误"""

    def __init__(self, message: str = "Multiple records found"):
        super().__init__(message)
