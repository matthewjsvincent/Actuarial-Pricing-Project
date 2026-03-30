from datetime import datetime


class AppLogger:
    def __init__(self):
        self.logs = []
        self.callbacks = []

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{level}] {timestamp} - {message}"

        self.logs.append(formatted)

        # Notify GUI listeners
        for callback in self.callbacks:
            callback(formatted)

    def subscribe(self, callback):
        self.callbacks.append(callback)

        # Replay existing logs to new subscriber
        for log in self.logs:
            callback(log)


# Global logger instance
logger = AppLogger()