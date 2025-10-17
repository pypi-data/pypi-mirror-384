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

import time

from dpk_code_profiler.transform import (
    CodeProfilerTransform,
    CodeProfilerTransformConfiguration,
)
from data_processing.utils import get_dpk_logger
from data_processing_ray.runtime.ray import RayTransformLauncher
from data_processing_ray.runtime.ray.runtime_configuration import (
    RayTransformRuntimeConfiguration,
)


logger = get_dpk_logger()


class CodeProfilerRayTransformConfiguration(RayTransformRuntimeConfiguration):
    """
    Implements the RayTransformConfiguration for NOOP as required by the RayTransformLauncher.
    NOOP does not use a RayRuntime class so the superclass only needs the base
    python-only configuration.
    """

    def __init__(self):
        """
        Initialization
        :param base_configuration - base configuration class
        """
        super().__init__(transform_config=CodeProfilerTransformConfiguration(transform_class=CodeProfilerTransform))


if __name__ == "__main__":

    print("In code_profiler_transform_ray")
    launcher = RayTransformLauncher(CodeProfilerRayTransformConfiguration())
    logger.info("Launching CodeProfiler transform")
    launcher.launch()
