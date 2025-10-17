import logging
from typing import Dict, List, Union

import snowflake.connector
from acedeploy.core.model_configuration import SolutionConfig
from aceutils.logger import LoggingAdapter, LogOperation, LogStatus
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


class SnowClientConfig(object):
    def __init__(
        self,
        account: str,
        user: str,
        password: str = None,
        private_key: str = None,
        private_key_pass: str = None,
        warehouse: str = None,
        role: str = None,
        database: str = None,
        sql_variables: dict = None,
    ):
        self.user = user
        self.password = password
        if private_key is not None:
            self.private_key_bytes = self._format_private_key(private_key, private_key_pass)
        else:
            self.private_key_bytes = None
        self.private_key_pass = private_key_pass
        self.account = account
        self.warehouse = warehouse
        self.role = role
        self.database = database
        self.sql_variables = {} if sql_variables is None else sql_variables

    @staticmethod
    def _format_private_key(private_key: str, private_key_pass: str) -> bytes:
        if not private_key:
            raise ValueError("Private key content is not provided.")
        # Remove all unnecessary whitespace to ensure proper formatting
        private_key = "".join(private_key.split())
        # Check if the key starts and ends correctly
        if not (
            private_key.startswith("-----BEGINENCRYPTEDPRIVATEKEY-----")
            and private_key.endswith("-----ENDENCRYPTEDPRIVATEKEY-----")
        ):
            raise ValueError(
                "Private key must start with '-----BEGIN ENCRYPTED PRIVATE KEY-----' and end with '-----END ENCRYPTED PRIVATE KEY-----'."
            )
        # Extract the Base64 content between header and footer
        base64_content = private_key.replace(
            "-----BEGINENCRYPTEDPRIVATEKEY-----", ""
        ).replace("-----ENDENCRYPTEDPRIVATEKEY-----", "")
        # Insert newlines every 64 characters for proper PEM formatting
        base64_lines = [
            base64_content[i : i + 64] for i in range(0, len(base64_content), 64)
        ]
        # Add headers and footers with correct line breaks
        formatted_pk = (
            "-----BEGIN ENCRYPTED PRIVATE KEY-----\n"
            + "\n".join(base64_lines)
            + "\n-----END ENCRYPTED PRIVATE KEY-----"
        )
        formatted_pk = serialization.load_pem_private_key(
            formatted_pk.encode("utf-8"),
            password=private_key_pass.encode("utf-8"),
            backend=default_backend(),
        )
        private_key_bytes = formatted_pk.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return private_key_bytes

    def get_connect_info(self) -> Dict:
        connect_info = {
            "account": self.account,
            "user": self.user,
            "password": self.password,
            "private_key": self.private_key_bytes,
            "private_key_pass": self.private_key_pass,
        }

        for opt_prop in ["warehouse", "role", "database"]:
            if getattr(self, opt_prop) is not None:
                connect_info[opt_prop] = getattr(self, opt_prop)

        return connect_info

    @staticmethod
    def get_from_solution_config(
        config: SolutionConfig, database: str = None
    ) -> "SnowClientConfig":
        """
            Convienience wrapper to return a snowflake client config object based of the solution config
        Args:
            config: SolutionConfig
            database: str - The name of the database to use in the snowflake connection (optional)
        Returns:
            SnowClientConfig - snowflake client config
        """
        return SnowClientConfig(
            config.snow_account,
            config.snow_login,
            config.snow_password,
            config.snow_private_key,
            config.snow_private_key_pass,
            config.snow_warehouse,
            config.snow_role,
            database,
            config.sql_variables,
        )


class SnowClient(object):
    """
    Objects that collects all operations and information about the snowflake databases.
    """

    def __init__(self, config: SnowClientConfig):
        """
            Creates a new SnowClient
        Args:
            config: SolutionConfig - stored configuration values
        """
        self.connection = None
        self._config = config
        self.database = self._config.database

    def __del__(self):
        """
        Ensures the connection snowflake is closed at the end
        """
        if self.connection is not None:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.connection is not None:
            self.connection.close()

    def _get_connection(self):
        """
        Factory method to get snowflake connection
        Initializes new snowflake connection if not already connected
        """
        if self.connection is None:
            conn_info = self._config.get_connect_info()
            self.connection = snowflake.connector.connect(**conn_info)
            if self._config.database is not None:
                self.execute_statement(f"USE DATABASE {self.database};")

            self.set_sql_variables(self._config.sql_variables)

        return self.connection

    @staticmethod
    def _get_error_message(excepction: Exception, statement: str) -> None:
        """
        Compose error message if the execution of a statement or query fails.
        """
        if hasattr(excepction, "raw_msg"):
            message = excepction.raw_msg.replace("\n", " ")
        else:
            message = str(
                excepction
            )  # this makes sure that all kinds of errors can have a message, even if they do not have raw_msg attribute
        if hasattr(excepction, "sfqid"):
            message = message + f"\nQuery ID: {excepction.sfqid}"
        return f"SNOWFLAKE ERROR: {message}\nFailed statement:\n{statement}"

    def execute_statement(self, statement: Union[str, List[str]]) -> None:
        """
            Executes simple statement against snowflake
            Schema and Database settings must be set beforehand
        Args:
            statement Union[str, List[str]] - a sql statement or a list of sql statements to execute
        """
        connection = self._get_connection()
        statement_list: List[str] = (
            statement if isinstance(statement, list) else [statement]
        )

        try:
            for single_statement in statement_list:
                stripped_statement = (
                    single_statement.strip()
                )  # remove whitespace from statement, as execute_string() might produce warnings if empty new lines are found after a semicolon
                log.debug(
                    f"START execution [ '{stripped_statement}' ]",
                    operation=LogOperation.SQLCOMMAND,
                    status=LogStatus.PENDING,
                    db=self.database,
                )
                _ = connection.execute_string(stripped_statement)
                log.debug(
                    f"FINISH execution [ '{stripped_statement}' ]",
                    operation=LogOperation.SQLCOMMAND,
                    status=LogStatus.SUCCESS,
                    db=self.database,
                )

        except Exception as err:
            raise Exception(self._get_error_message(err, single_statement)) from err

    def execute_query(
        self, query: Union[str, List[str]], use_dict_cursor: bool = True
    ) -> Union[List[Dict], List[List[Dict]]]:
        """
            Executes sql statements and against snowflake and returns the result as dictionary or list of dictionaries
        Args:
            query Union[str, List[str]] - a sql query or a list of sql queries to execute
            use_dict_cursor bool (default true) - use snowflake DictCursor for results instead of returning a list
        """
        connection = self._get_connection()
        if use_dict_cursor is True:
            cursor = connection.cursor(snowflake.connector.DictCursor)
        else:
            cursor = connection.cursor()

        query_list: List[str] = query if isinstance(query, list) else [query]
        result: List[Dict] = []

        try:
            for single_query in query_list:
                log.debug(
                    f"START execution [ '{single_query}' ]",
                    operation=LogOperation.SQLCOMMAND,
                    status=LogStatus.PENDING,
                    db=self.database,
                )
                result.append(cursor.execute(single_query).fetchall())
                log.debug(
                    f"FINISH execution [ '{single_query}' ]",
                    operation=LogOperation.SQLCOMMAND,
                    status=LogStatus.SUCCESS,
                    db=self.database,
                )
        except Exception as err:
            raise Exception(self._get_error_message(err, single_query)) from err

        return result[0] if not isinstance(query, list) else result

    def set_sql_variables(self, variables_dict: dict) -> None:
        """
            Set given SQL variables for the session

            Supported variable types: int, float, bool, str
        Args
            variables_dict: dict - dictionary containing the variables to be set, example: {"varname1": "varvalue1", "varname2": "varvalue2"}
        """
        log.debug("SET sql variables")
        for key, value in variables_dict.items():
            if isinstance(value, int):
                value_string = str(value)
            elif isinstance(value, float):
                value_string = str(value)
            elif isinstance(value, bool):
                if value:
                    value_string = "TRUE"
                else:
                    value_string = "FALSE"
            else:
                if "'" in value:
                    raise ValueError(
                        f"Variable [ '{key}' ] contains illegal character \"'\"."
                    )
                value_string = f"'{value}'"
            statement = f"SET {key} = {value_string}"
            self.execute_statement(statement)
