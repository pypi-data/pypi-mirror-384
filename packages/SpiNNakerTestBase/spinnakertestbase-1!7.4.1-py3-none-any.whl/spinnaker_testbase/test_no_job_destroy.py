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
import unittest

from spinn_front_end_common.data import FecDataView
from .base_test_case import BaseTestCase


class TestNoJobDestory(BaseTestCase):
    """
    Used by Jenkins to check if a job was destroyed.
    """

    def test_no_destory_file(self) -> None:
        """
        Checks for the error file and prints it out if found

        :raise AssertionError: if the error file exists
        """
        if os.path.exists(FecDataView.get_error_file()):
            with open(FecDataView.get_error_file(),
                      encoding="utf-8") as error_file:
                error_text = error_file.read()
            print(error_text)
            raise AssertionError(error_text)


if __name__ == "__main__":
    unittest.main()
