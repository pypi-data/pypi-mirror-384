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

from io import TextIOBase
import os
import platform
from shutil import copyfile
import sys
from typing import Dict, List, Optional, Union

SKIP_TOO_LONG = "        raise SkipTest(\"{}\")\n"
NO_SKIP_TOO_LONG = "        # raise SkipTest(\"{}\")\n"
WARNING_LONG = "        # Warning this test takes {}.\n" \
               "        # raise skiptest is uncommented on branch tests\n"


class RootScriptBuilder(object):
    """
    Looks for example scripts that can be made into integration tests.
    """

    def _add_script(self, test_file: TextIOBase, name: str, local_path: str,
                    skip_imports: Optional[List[str]]) -> None:
        test_file.write("\n    def test_")
        test_file.write(name)
        test_file.write("(self):\n")
        if skip_imports:
            if isinstance(skip_imports, str):
                skip_imports = [skip_imports]
            for skip_import in skip_imports:
                test_file.write("        ")
                test_file.write(skip_import)
                test_file.write("\n")
        test_file.write("        self.check_script(\"")
        test_file.write(local_path)
        test_file.write("\"")
        if skip_imports:
            test_file.write(", skip_exceptions=[")
            test_file.write(
                ",".join(map(lambda x: x.split()[-1], skip_imports)))
            test_file.write("]")
        test_file.write(")\n")

    def _add_scripts(self, a_dir: str, prefix_len: int, test_file: TextIOBase,
                     too_long: Dict[str, str], exceptions: Dict[str, str],
                     skip_exceptions: Dict[str, List[str]]) -> None:
        for a_script in os.listdir(a_dir):
            script_path = os.path.join(a_dir, a_script)
            if os.path.isdir(script_path) and not a_script.startswith("."):
                self._add_scripts(
                    script_path, prefix_len, test_file, too_long, exceptions,
                    skip_exceptions)
            if a_script.endswith(".py") and a_script != "__init__.py":
                local_path = script_path[prefix_len:]
                # As the paths are written to strings in files
                # Windows needs help!
                if platform.system() == "Windows":
                    local_path = local_path.replace("\\", "/")
                if a_script in too_long and len(sys.argv) > 1:
                    # Lazy boolean distinction based on presence of parameter
                    test_file.write("\n    # Not testing file due to: ")
                    test_file.write(too_long[a_script])
                    test_file.write("\n    # ")
                    test_file.write(local_path)
                    test_file.write("\n")
                elif a_script in exceptions:
                    test_file.write("\n    # Not testing file due to: ")
                    test_file.write(exceptions[a_script])
                    test_file.write("\n    # ")
                    test_file.write(local_path)
                    test_file.write("\n")
                else:
                    name = local_path[:-3].replace(os.sep, "_").replace(
                        "-", "_")
                    skip_imports = skip_exceptions.get(a_script, None)
                    self._add_script(test_file, name, local_path, skip_imports)

    def create_test_scripts(
            self, dirs: Union[str, List[str]],
            too_long: Optional[Dict[str, str]] = None,
            exceptions: Optional[Dict[str, str]] = None,
            skip_exceptions: Optional[Dict[str, List[str]]] = None) -> None:
        """
        Creates a file of integration tests to run the scripts/ examples

        :param dirs: List of dirs to find scripts in.
            These are relative paths to the repository
        :param too_long: Dict of files that take too long to run and how long.
            These are just the file name including the `.py`.
            They are mapped to a skip reason.
            These are only skip tests if asked to be (currently not done).
        :param exceptions: Dict of files that should be skipped.
            These are just the file name including the `.py`.
            They are mapped to a skip reason.
            These are always skipped.
        :param skip_exceptions:
            Dict of files and exceptions to skip on.
            These are just the file name including the `.py`.
            They are mapped to a list of INDIVIUAL import statements
            in the::

                from xyz import Abc

            format.
        """
        if too_long is None:
            too_long = {}
        if exceptions is None:
            exceptions = {}
        if skip_exceptions is None:
            skip_exceptions = {}
        if isinstance(dirs, str):
            dirs = [dirs]

        class_file = sys.modules[self.__module__].__file__
        assert class_file is not None
        integration_dir = os.path.dirname(class_file)
        assert integration_dir is not None
        repository_dir = os.path.dirname(integration_dir)
        assert repository_dir is not None
        test_base_directory = os.path.dirname(__file__)

        test_script = os.path.join(integration_dir, "test_scripts.py")
        header = os.path.join(test_base_directory, "test_scripts_header")
        copyfile(header, test_script)

        with open(test_script, "a", encoding="utf-8") as test_file:
            for script_dir in dirs:
                a_dir = os.path.join(repository_dir, script_dir)
                self._add_scripts(a_dir, len(repository_dir)+1, test_file,
                                  too_long, exceptions, skip_exceptions)
