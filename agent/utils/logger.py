class Logger:
    def __init__(self, verbose=True, log_level="INFO"):
        self.verbose = verbose
        self.log_level = log_level.upper()
        self.levels = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
    
    def _log(self, message: str, level: str = "INFO"):
        if not self.verbose:
            return
        
        current_level = self.levels.get(self.log_level, 1)
        message_level = self.levels.get(level.upper(), 1)
        
        if message_level >= current_level:
            prefix = f"[{level}]" if level != "INFO" else "[LOG]"
            print(f"{prefix} {message}")
    
    def debug(self, message: str):
        self._log(message, "DEBUG")
    
    def info(self, message: str):
        self._log(message, "INFO")
    
    def warning(self, message: str):
        self._log(message, "WARNING")
    
    def error(self, message: str):
        self._log(message, "ERROR")
