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

from logging import LogRecord
import os
import random
import sys
from typing import List
from spinn_front_end_common.data import FecDataView
from .root_test_case import RootTestCase


random.seed(os.environ.get('P8_INTEGRATION_SEED', None))


class BaseTestCase(RootTestCase):
    """
    This extends unittest.TestCase to offer extra functions as needed.
    """

    def setUp(self) -> None:
        file = sys.modules[self.__module__].__file__
        assert file is not None
        self._setup(file)

    def assert_logs_messages(
            self, log_records: List[LogRecord], sub_message: str,
            log_level: str = 'ERROR', count: int = 1,
            allow_more: bool = False) -> None:
        """
        Tool to assert the log messages contain the sub-message.

        :param log_records: list of log message
        :param sub_message: text to look for
        :param log_level: level to look for
        :param count: number of times this message should be found
        :param allow_more: If True, OK to have more than count repeats
        """
        seen = 0
        for record in log_records:
            if record.levelname == log_level and \
                    sub_message in str(record.msg):
                seen += 1
        if allow_more and seen > count:
            return
        if seen != count:
            raise self.failureException(
                f'"{sub_message}" not found in any {log_level} logs '
                f'{count} times, was found {seen} times')

    def get_system_iobuf_files(self) -> List[str]:
        """
        :returns: A list of the system iobuf files.
        """
        system_iobuf_file_path = FecDataView.get_system_provenance_dir_path()
        return os.listdir(system_iobuf_file_path)

    def get_app_iobuf_files(self) -> List[str]:
        """
        :returns: A list of the application iobuf files.
        """
        app_iobuf_file_path = FecDataView.get_app_provenance_dir_path()
        return os.listdir(app_iobuf_file_path)
