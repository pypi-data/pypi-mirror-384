class FatalError(Exception):
    def __init__(self, message: str = "No message"):
        self.message = message
        super().__init__(self.message)
