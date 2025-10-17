class UnauthorizedError(ValueError):
    msg: str

    def __init__(self, msg: str):
        self.msg = msg
