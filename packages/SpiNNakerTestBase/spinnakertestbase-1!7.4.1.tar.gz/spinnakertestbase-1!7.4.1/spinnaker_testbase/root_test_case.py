# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import time
from typing import Callable, List, Optional

import unittest
from spinnman.exceptions import SpinnmanException
from pacman.exceptions import PacmanPartitionException, PacmanValueError
from spalloc_client.job import JobDestroyedError
from spinn_front_end_common.data import FecDataView

if os.environ.get('CONTINUOUS_INTEGRATION', 'false').lower() == 'true':
    MAX_TRIES = 3
else:
    MAX_TRIES = 1


class RootTestCase(unittest.TestCase):
    """
    This holds the code shared by the all test and script checkers

    """

    def _setup(self, script: str) -> None:
        # Remove random effect for testing
        # Set test_seed to None to allow random
        # pylint: disable=attribute-defined-outside-init
        self._test_seed = 1

        path = os.path.dirname(script)
        os.chdir(path)

    @staticmethod
    def assert_not_spin_three() -> None:
        """
        Will raise a SkipTest if run on a none virtual 4 chip board

        :raises SkipTest: If we're on the wrong sort of board
        """
        version = FecDataView.get_machine_version().number
        if version != 5:
            raise unittest.SkipTest(
                f"This test will not run on a spinn-{version} board")

    def report(self, message: str, file_name: str) -> None:
        """
        Writes some text to the specified file

        The file will be written in the env GLOBAL_REPORTS directory.

        If no GLOBAL_REPORTS is defined the timestamp directory
        holding the run data is used.

        :param message:
        :param file_name: local file name.
        """
        if not message.endswith("\n"):
            message += "\n"

        report_path = os.path.join(
            FecDataView.get_global_reports_dir(), file_name)
        with open(report_path, "a", encoding="utf-8") as report_file:
            report_file.write(message)

    def runsafe(self, method: Callable, retry_delay: float = 3.0,
                skip_exceptions: Optional[List[type]] = None) -> None:
        """
        Will run the method possibly a few times

        :param method:
        :param retry_delay:
        :param skip_exceptions:
            list of exception classes to convert in SkipTest
        """
        if skip_exceptions is None:
            skip_exceptions = []
        retries = 0
        while True:
            try:
                method()
                break
            except (JobDestroyedError, SpinnmanException) as ex:
                for skip_exception in skip_exceptions:
                    if isinstance(ex, skip_exception):
                        FecDataView.raise_skiptest(
                            f"{ex} Still not fixed!", ex)
                class_file = sys.modules[self.__module__].__file__
                assert class_file is not None
                with open(FecDataView.get_error_file(), "a",
                          encoding="utf-8") as error_file:
                    error_file.write(class_file)
                    error_file.write("\n")
                    error_file.write(str(ex))
                    error_file.write("\n")
                retries += 1
                if retries >= MAX_TRIES:
                    raise ex
            except (PacmanValueError, PacmanPartitionException) as ex:
                # skip out if on a spin three
                self.assert_not_spin_three()
                for skip_exception in skip_exceptions:
                    if isinstance(ex, skip_exception):
                        FecDataView.raise_skiptest(
                            f"{ex} Still not fixed!", ex)
                raise ex
            print("")
            print("==========================================================")
            print(f" Will run {method} again in {retry_delay} seconds")
            print(f" retry: {retries}")
            print("==========================================================")
            print("")
            time.sleep(retry_delay)
