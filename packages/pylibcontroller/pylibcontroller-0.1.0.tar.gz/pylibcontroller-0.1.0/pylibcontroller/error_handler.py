class LibraryError(Exception):
    """
    Custom exception class for library-related errors.
    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"LibraryError: {self.message}"
