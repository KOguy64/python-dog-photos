class InvalidPathError(Exception):

    def __init__(self, path):
        self.path = path
        self.message = f"{path} does not exist !"
        super().__init__(self.message)
