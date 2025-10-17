import logging
import textwrap
from datetime import datetime
from enum import Enum

from snowflake.connector import SnowflakeConnection


class LogStatus(Enum):
    """
    Indicates which status a deployment step has
    """

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WARNING = "WARNING"


class LogOperation(Enum):
    """
    Indicates which operational step category a log message falls into.
    """

    DIFF = "DIFF"
    GIT = "GIT"
    SQLCOMMAND = "SQLCOMMAND"
    DEPLOYMENT = "DEPLOYMENT"
    TARGET = "TARGET"
    PREP = "PREPERATION"


class LoggingAdapter(logging.LoggerAdapter):
    """
    Logging adapter for Acedeploy framework.
    Adds the additional args 'operation', 'status', 'db' to the log message.
    """

    def __init__(self, logger, extra=None):
        if extra is None:
            extra = {}
        super().__init__(logger, extra)

    def process(self, msg, kwargs):
        extra_args = ("operation", "status", "db")
        extras = {}
        args = {}
        for kwarg in kwargs:
            if kwarg in extra_args:
                extras[kwarg] = kwargs[kwarg]
            else:
                args[kwarg] = kwargs[kwarg]
        args["extra"] = extras
        return msg, args


class LogFileFormatter(logging.Formatter):
    """
    Logging formatter for saving logfiles.
    Adds the additional args 'operation', 'status', 'db' to the log message.
    Note: default syntax logger.info("my message %s", "some string") is not supported by this
    """

    def format(self, record):
        timestring = datetime.utcfromtimestamp(record.created).isoformat(
            sep=" ", timespec="milliseconds"
        )
        result = f"{timestring} - {record.name} - {record.levelname} - {record.msg}"
        extra_args = ("operation", "status", "db")
        for arg in extra_args:
            if hasattr(record, arg):
                result += f" - {arg}: {getattr(record, arg)}"
        return result.replace("\r", "\\r").replace("\n", "\\n")


class DevOpsFormatter(logging.Formatter):
    """
    Logging formatter for use in DevOps pipelines.
    Adds syntax for errors and warnings.
    Note: default syntax logger.info("my message %s", "some string") is not supported by this
    """

    def __init__(self, add_timestamp=False):
        self.add_timestamp = add_timestamp
        super().__init__()

    def format(self, record):
        message = record.msg
        record.msg = ""
        if self.add_timestamp:
            timestring = datetime.utcfromtimestamp(record.created).isoformat(
                sep=" ", timespec="milliseconds"
            )
            header = f"{timestring} - {record.levelname} - "
        else:
            header = f"{record.levelname} - "
        msg = textwrap.indent(message, " " * len(header)).strip()
        record.msg = message
        result = header + msg
        if record.levelno >= logging.ERROR:
            return f"##vso[task.logissue type=error;]{result}"  # \n##vso[task.complete result=Failed;]DONE'
        elif record.levelno >= logging.WARNING:
            return f"##vso[task.logissue type=warning;]{result}"
        else:
            return result


class GitLabFormatter(logging.Formatter):
    """
    Logging formatter for use in terminals.
    Properly indents multiline strings.
    """

    def __init__(self):
        super().__init__()

    def format(self, record):
        timestring = datetime.utcfromtimestamp(record.created).isoformat(
            sep=" ", timespec="milliseconds"
        )
        message = record.msg
        record.msg = ""
        header = f"{timestring} - {record.levelname} - "
        msg = textwrap.indent(message, " " * len(header)).strip()
        record.msg = message
        return header + msg


class DefaultFormatter(logging.Formatter):
    """
    Logging formatter for use in terminals.
    Properly indents multiline strings.
    """

    def __init__(self):
        super().__init__()

    def format(self, record):
        message = record.msg
        record.msg = ""
        header = f"{record.levelname} - "
        msg = textwrap.indent(message, " " * len(header)).strip()
        record.msg = message
        return header + msg


def get_devops_adapter(logger, debug=False, add_timestamp=False) -> LoggingAdapter:
    """
        Convinience function for use in DevOps pipelines.
    Args:
        logger: logging.Logger
        debug: bool - Set output level to DEBUG, else INFO
        add_timestamp: bool - Add timestamp to each entry
    Returns:
        adapter: logging.LoggerAdapter - Adapter to log against
    Example:
        logger = logging.getLogger('acedeploy')
        log = get_devops_adapter(logger, os.getenv('SYSTEM_DEBUG', False), False)
    """
    logger.setLevel(logging.DEBUG)
    log_level = logging.DEBUG if debug else logging.INFO

    sh = logging.StreamHandler()
    sh.setLevel(log_level)
    sh.setFormatter(DevOpsFormatter(add_timestamp))
    logger.addHandler(sh)

    adapter = LoggingAdapter(logger)
    return adapter


def get_gitlab_adapter(logger, debug=False, add_timestamp=False) -> LoggingAdapter:
    """
        Convinience function for use in Gitlab pipelines.
    Args:
        logger: logging.Logger
        debug: bool - Set output level to DEBUG, else INFO
        add_timestamp: bool - Add timestamp to each entry
    Returns:
        adapter: logging.LoggerAdapter - Adapter to log against
    Example:
        logger = logging.getLogger('acedeploy')
        log = get_devops_adapter(logger, os.getenv('DEBUG_ACEDEPLOY', False), False)
    """
    logger.setLevel(logging.DEBUG)
    log_level = logging.DEBUG if debug else logging.INFO

    sh = logging.StreamHandler()
    sh.setLevel(log_level)
    sh.setFormatter(GitLabFormatter(add_timestamp))
    logger.addHandler(sh)

    adapter = LoggingAdapter(logger)
    return adapter


class SnowflakeTableHandler(logging.Handler):
    """
    Logging handler to log to an existing table in Snowflkae
    """

    def __init__(self, sf_connection: SnowflakeConnection, log_table: str, run_id: str):
        """
        Params:
            sf_connection: SnowflakeConnection - snowflake connection with role and warehouse set
            log_table: str - fully qualified name of logging table
            run_id: str - unique identifier for this script run
        """
        super().__init__()
        self.sf_connection = sf_connection
        self.log_table = log_table
        self.run_id = run_id
        self.log_msg = ""

    def emit(self, record):
        timestring = datetime.utcfromtimestamp(record.created).isoformat(
            sep=" ", timespec="milliseconds"
        )
        self.log_msg = record.msg
        self.log_msg = self.log_msg.strip()
        self.log_msg = self.log_msg.replace("'", "''")
        statement = f"""
            INSERT INTO {self.log_table} (
                RUN_ID,
                TIMESTAMP,
                LEVEL,
                MESSAGE,
                DATABASE,
                OPERATION,
                STATUS
            ) VALUES (
                '{self.run_id}',
                '{timestring}',
                '{record.levelname}',
                '{self.log_msg}',
                '{getattr(record, 'db', '')}',
                '{getattr(record, 'operation', '')}',
                '{getattr(record, 'status', '')}'
            )
        """
        try:
            self.sf_connection.execute_string(statement)
        except Exception as err:
            print(f"Error in SnowflakeTableHandler {str(err)}")
