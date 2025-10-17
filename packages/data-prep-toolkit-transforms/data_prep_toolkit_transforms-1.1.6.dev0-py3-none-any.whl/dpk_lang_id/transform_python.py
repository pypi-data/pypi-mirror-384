# SPDX-License-Identifier: Apache-2.0
# (C) Copyright IBM Corp. 2024.
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################
import sys

from data_processing.runtime.pure_python import (
    PythonTransformLauncher,
    PythonTransformRuntimeConfiguration,
    Transform,
)
from data_processing.utils import ParamsUtils, get_dpk_logger
from dpk_lang_id.transform import LangIdentificationTransformConfiguration


logger = get_dpk_logger()


class LangIdentificationPythonTransformConfiguration(PythonTransformRuntimeConfiguration):
    """
    Implements the PythonTransformConfiguration for Language Identification as required by the PythonTransformLauncher.
    Language Identification does not use a RayRuntime class so the superclass only needs the base
    python-only configuration.
    """

    def __init__(self):
        """
        Initialization
        :param base_configuration - base configuration class
        """
        super().__init__(transform_config=LangIdentificationTransformConfiguration())


class LangId(Transform):
    def __init__(self, **kwargs):
        super().__init__(LangIdentificationTransformConfiguration(), **kwargs)


if __name__ == "__main__":
    launcher = PythonTransformLauncher(LangIdentificationPythonTransformConfiguration())
    logger.info("Launching lang_id transform")
    launcher.launch()
