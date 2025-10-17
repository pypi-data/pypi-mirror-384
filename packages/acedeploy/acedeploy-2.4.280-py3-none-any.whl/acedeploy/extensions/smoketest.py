import json
import logging
from datetime import datetime

import aceutils.file_util as file_util
from aceservices.snowflake_service import SnowClient
from aceutils.logger import LoggingAdapter

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


class Smoketest:
    """
    Class to perform a smoketest
    """

    def __init__(
        self,
        snow_client: SnowClient,
        smoketest_config_file: str,
        results_file: str = "",
    ):
        """
            Inits a metadata service.
        Args:
            snow_client: SnowClient - provides connection a snowflake database
            smoketest_config_file: str - path to file which contains the config json
            results_file: str - optional: file in which to store smoketest results
        """
        self._snow_client = snow_client
        if not self._validate_json(smoketest_config_file):
            raise ValueError("The given smoktest config is not valid")
        self._config = file_util.load_json(smoketest_config_file)
        self._results_file = results_file
        self.results_succeeded = []
        self.results_failed = []

    def _validate_json(self, smoketest_config_file: str):
        """
        Validate if the given json string contains a valid config
        """
        json_schema_file = file_util.get_path(
            ["resources", "json-schemas", "smoketest.schema.json"]
        )
        return file_util.validate_json(json_schema_file, smoketest_config_file)

    def start_smoketest(self):
        """
        Start the smoketest execution
        """
        log.info("START SMOKETEST")

        self.results_succeeded = []
        self.results_failed = []

        s, f = self.smoketest_explain_select_from_views()
        self.results_succeeded.extend(s)
        self.results_failed.extend(f)

        s, f = self.smoketest_explain_select_from_tables()
        self.results_succeeded.extend(s)
        self.results_failed.extend(f)

        log.info(
            f"FINISH SMOKETEST. Ran [ '{len(self.results_succeeded)+len(self.results_failed)}' ] tests. Success: [ '{len(self.results_succeeded)}' ]. Failed: [ '{len(self.results_failed)}' ]."
        )
        if len(self.results_succeeded) > 0:
            log.info(
                f"List of successful tests:\n{json.dumps(self.results_succeeded, indent=4)}"
            )
        if len(self.results_failed) > 0:
            log.info(
                f"List of failed tests:\n{json.dumps(self.results_failed, indent=4)}"
            )

        if self._results_file != "":
            self.save_results()

    def smoketest_explain_select_from_views(self):
        """
        Run a select for all views.
        """
        log.info(
            f"RUN test [ 'smoketest_explain_select_from_views' ] on DATABASE [ '{self._config['database']}' ] with ROLE [ '{self._config['role']}' ]"
        )
        succeeded, failed = self.explain_select_from_object(
            self._config["objects"]["views"],
            "view",
            "smoketest_explain_select_from_views",
        )
        log.info("FINISH test [ 'smoketest_explain_select_from_views' ]")
        return succeeded, failed

    def smoketest_explain_select_from_tables(self):
        """
        Run a select for all tables.
        """
        log.info(
            f"RUN test [ 'smoketest_explain_select_from_tables' ] on DATABASE [ '{self._config['database']}' ] with ROLE [ '{self._config['role']}' ]"
        )
        succeeded, failed = self.explain_select_from_object(
            self._config["objects"]["tables"],
            "table",
            "smoketest_explain_select_from_tables",
        )
        log.info("FINISH test [ 'smoketest_explain_select_from_tables' ]")
        return succeeded, failed

    def explain_select_from_object(self, objectnames, objecttype, testname):
        """
        Run a select for all given objects.
        """
        succeeded = []
        failed = []
        self._snow_client.execute_statement(f"USE ROLE {self._config['role']};")
        for obj in objectnames:
            query = f"EXPLAIN SELECT * FROM {self._config['database']}.{obj};"
            try:
                self._snow_client.execute_query(query)
                succeeded.append(
                    {
                        "name": obj,
                        "type": objecttype,
                        "test": testname,
                        "query": query,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
            except Exception as e:
                failed.append(
                    {
                        "name": obj,
                        "type": objecttype,
                        "test": testname,
                        "query": query,
                        "timestamp": datetime.utcnow().isoformat(),
                        "error": str(e),
                    }
                )
        return succeeded, failed

    def save_results(self):
        """
        Save all results in a JSON file
        """
        log.info(f"SAVE results as [ '{self._results_file}' ]")
        content = {
            "config": self._config,
            "results": {
                "failed": self.results_failed,
                "succeeded": self.results_succeeded,
            },
        }
        file_util.save_json(self._results_file, content)
