# apeex/examples/hello_services.py

class Logger:
    """Simple logger service."""
    def log(self, message: str):
        print(f"[LOG] {message}")


class UserService:
    """Service depending on Logger."""
    def __init__(self, logger: Logger):
        self.logger = logger

    def create_user(self, username: str):
        self.logger.log(f"Creating user: {username}")
        return {"username": username}
