class YTError(Exception):
    def __init__(self, error: dict):
        self.code: int = error['code']
        self.message: str = error['message']
