import json
from pathlib import Path
from typing import Tuple

import mflog

from mfire.settings import get_logger
from mfire.settings.logger import Logger


class TestLogger:
    """Class for testing the logger."""

    logger_name = "my_logger"
    logger_module = "test_logger"

    def _get_logger(self, dirname: Path) -> Tuple[Logger, Path]:
        log_filename = Path(dirname) / "promethee_mflog.json"
        if log_filename.is_file():
            log_filename.unlink()

        mflog.set_config(
            minimal_level="DEBUG", json_file=log_filename, json_minimal_level="DEBUG"
        )
        logger = get_logger(name=self.logger_name, module=self.logger_module)
        return logger, log_filename

    def test_logger_msg(self, working_dir: Path):
        # Tests writing logs to the promethee_mflog.json file
        logger, log_filename = self._get_logger(working_dir)
        events = ["debug", "info", "warning", "error", "critical"]
        logger.debug(f"Mon {events[0]}", size=len(events[0]))
        logger.info(f"Mon {events[1]}", size=len(events[1]))
        logger.warning(f"Mon {events[2]}", size=len(events[2]))
        logger.error(f"Mon {events[3]}", size=len(events[3]))
        logger.critical(f"Mon {events[4]}", size=len(events[4]))
        mflog.set_config(
            minimal_level="WARNING", json_file=None, json_minimal_level="WARNING"
        )

        assert log_filename.is_file()
        with open(log_filename) as fp:
            for i, line in enumerate(fp.readlines()):
                log = json.loads(line)
                assert log.get("name") == self.logger_name
                assert log.get("module") == self.logger_module
                assert log.get("level") == events[i]
                assert log.get("event") == f"Mon {events[i]}"
                assert log.get("size") == len(events[i])

    def test_bind_and_unbind(self, working_dir: Path):
        logger, log_filename = self._get_logger(working_dir)

        log = logger.bind(test="123")
        log.warning("Msg")
        log = logger.try_unbind("test")
        log.warning("Msg")

        assert log_filename.is_file()
        with open(log_filename) as fp:
            first_line = fp.readline()
            log = json.loads(first_line)
            assert log.get("name") == self.logger_name
            assert log.get("module") == self.logger_module
            assert log.get("level") == "warning"
            assert log.get("event") == "Msg"
            assert log.get("test") == "123"

            second_line = fp.readline()
            log = json.loads(second_line)
            assert log.get("name") == self.logger_name
            assert log.get("module") == self.logger_module
            assert log.get("level") == "warning"
            assert log.get("event") == "Msg"
            assert log.get("test") is None
