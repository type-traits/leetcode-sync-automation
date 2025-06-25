import logging
import os
import traceback
import inspect
from datetime import datetime
from rich import print

LEVEL_STYLE_EMOJI_MAP = {
    "DEBUG":    ("blue", "🔍"),
    "INFO":     ("cyan", "🔄"),
    "WARNING":  ("yellow", "⚠️"),
    "ERROR":    ("red", "❌"),
    "CRITICAL": ("magenta", "💥"),
    "SUCCESS":  ("green", "✅"),
}

_sync_logger = None

def init_logger(level_str="INFO"):
    global _sync_logger
    if _sync_logger is None:
        level = getattr(logging, level_str.upper(), logging.INFO)
        _sync_logger = SyncLogger(level=level)
    return _sync_logger

def get_logger():
    return _sync_logger.get_logger() if _sync_logger else None

def get_log_and_print():
    return _sync_logger.get_log_and_print() if _sync_logger else None


class SyncLogger:
    """
    Sets up and manages a shared logger for the sync automation tool.
    Configures both file logging and console output.

    - Log files are timestamped and saved in the 'logs/' directory.
    - Console output is clean and level-tagged.
    - Also exposes a LogAndPrint instance for dual logging and styled print.
    """

    def __init__(self, log_dir="logs", level=logging.INFO):
        """
        Initializes the logger configuration:
        - Creates the log directory if needed
        - Sets up file and console handlers
        - Attaches a custom LogAndPrint helper for styled logging

        Args:
            log_dir (str): Directory where log files will be saved. Default is 'logs'.
            level (int): Logging level (e.g., logging.INFO, logging.DEBUG).
        """
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        log_path = os.path.join(log_dir, f"sync_{timestamp}.log")

        self.logger = logging.getLogger("LeetCodeSync")
        self.logger.setLevel(level)
        self.logger.handlers.clear()  # Prevent duplicate handlers on re-import

        # File handler (persistent logs)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_format = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        file_handler.setFormatter(file_format)

        # Console handler (immediate user feedback)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.CRITICAL)
        console_handler.setFormatter(logging.Formatter())

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # Provide styled logger interface
        self.log_and_print = LogAndPrint(self.logger)

    def get_logger(self):
        """
        Returns:
            logging.Logger: The core logger instance for silent log tracking.
        """
        return self.logger

    def get_log_and_print(self):
        """
        Returns:
            LogAndPrint: A helper for log + styled print output in the terminal.
        """
        return self.log_and_print


class LogAndPrint:
    """
    A logging utility that logs messages to a file (via the standard logging module)
    and also prints a styled version of the message to the console using Rich-like formatting.

    Styles and emojis are automatically selected based on the log level.
    """

    def __init__(self, logger):
        """
        Initialize the wrapper with a base logger instance.

        Args:
            logger (logging.Logger): A configured logger to use for writing log entries.
        """
        self.logger = logger

    def _style_message(self, msg, level, style=None, emoji=None):
        """
        Apply console color styling and emoji based on either log level or user-specified style/emoji.
        Priority:
        - If style is passed and emoji is not, look up emoji by style
        - If neither is passed, fall back to log level
        """
        if style is None and emoji is None:
            style, emoji = LEVEL_STYLE_EMOJI_MAP.get(level.upper(), ("white", "ℹ️"))
        elif style is not None and emoji is None:
            # reverse lookup by style
            for s, e in LEVEL_STYLE_EMOJI_MAP.values():
                if s == style:
                    emoji = e
                    break
            else:
                emoji = "ℹ️"
        elif style is None and emoji is not None:
            style = LEVEL_STYLE_EMOJI_MAP.get(level.upper(), ("white", emoji))[0]

        return f"[{style}]{emoji} {msg}[/{style}]"

    def debug(self, msg, style=None, emoji=None):
        """
        Log a DEBUG-level message and print it styled in blue with a debug emoji.

        Args:
            msg (str): The debug message to log.
            style (str, optional): Console color override. Defaults to "blue" if not provided.
            emoji (str, optional): Emoji override. Defaults to "🔍" based on style or level.
        """
        self.logger.debug(msg)
        print(self._style_message(msg, level="DEBUG", style=style, emoji=emoji))


    def info(self, msg, style=None, emoji=None):
        """
        Log an INFO-level message and print it styled in cyan with a sync emoji.

        Args:
            msg (str): Informational message to log.
            style (str, optional): Console color override. Defaults to "cyan" if not provided.
            emoji (str, optional): Emoji override. Defaults to "🔄" based on style or level.
        """
        self.logger.info(msg)
        print(self._style_message(msg, level="INFO", style=style, emoji=emoji))


    def success(self, msg, style=None, emoji=None):
        """
        Log a SUCCESS-level message (internally logs as INFO) and print it styled in green.

        Args:
            msg (str): Success message to log.
            style (str, optional): Console color override. Defaults to "green" if not provided.
            emoji (str, optional): Emoji override. Defaults to "✅" based on style or level.
        """
        self.logger.info(msg)
        print(self._style_message(msg, level="SUCCESS", style=style, emoji=emoji))


    def warning(self, msg, style=None, emoji=None):
        """
        Log a WARNING-level message and print it styled in yellow with a warning emoji.

        Args:
            msg (str): Warning message to log.
            style (str, optional): Console color override. Defaults to "yellow" if not provided.
            emoji (str, optional): Emoji override. Defaults to "⚠️" based on style or level.
        """
        self.logger.warning(msg)
        print(self._style_message(msg, level="WARNING", style=style, emoji=emoji))


    def error(self, msg, style=None, emoji=None):
        """
        Log an ERROR-level message and print it styled in red with a cross emoji.

        Args:
            msg (str): Error message to log.
            style (str, optional): Console color override. Defaults to "red" if not provided.
            emoji (str, optional): Emoji override. Defaults to "❌" based on style or level.
        """
        self.logger.error(msg)
        print(self._style_message(msg, level="ERROR", style=style, emoji=emoji))


    def critical(self, msg, style=None, emoji=None):
        """
        Log a CRITICAL-level message and print it styled in magenta with an explosion emoji.

        Args:
            msg (str): Critical message to log.
            style (str, optional): Console color override. Defaults to "magenta" if not provided.
            emoji (str, optional): Emoji override. Defaults to "💥" based on style or level.
        """
        self.logger.critical(msg)
        print(self._style_message(msg, level="CRITICAL", style=style, emoji=emoji))

    def exception(self, msg, exc: Exception = None, show_trace=False):
        """
        Log an exception (with full traceback in file), and print a styled error message to the user.

        Args:
            msg (str): Contextual description (e.g., "Failed to sync submissions").
            exc (Exception, optional): The actual exception object.
            show_trace (bool): If True, also show traceback on CLI (not recommended for normal users).
        """
        if exc:
            self.logger.exception(f"{msg}: {str(exc)}")

            if show_trace:
                trace = traceback.format_exc()
                print(self._style_message(f"{msg}\n{trace}", level="ERROR"))
            else:
                # Extract caller location
                tb = exc.__traceback__
                while tb.tb_next:  # Get to the last traceback frame
                    tb = tb.tb_next
                frame = tb.tb_frame
                filename = os.path.basename(frame.f_code.co_filename)
                func_name = frame.f_code.co_name
                lineno = tb.tb_lineno

                loc = (
                    f"in [bold yellow]line {lineno}[/bold yellow] of "
                    f"[cyan]{func_name}()[/cyan] in [magenta]{filename}[/magenta]"
                )
                print(self._style_message(f"{msg}: {str(exc)} {loc}", level="ERROR"))
        else:
            self.logger.error(msg)
            print(self._style_message(msg, level="ERROR"))