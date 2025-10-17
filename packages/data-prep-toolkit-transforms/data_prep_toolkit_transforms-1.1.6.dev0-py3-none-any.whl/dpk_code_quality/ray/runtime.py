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

import os

from dpk_code_quality.transform import CodeQualityTransformConfiguration
from data_processing_ray.runtime.ray import RayTransformLauncher
from data_processing_ray.runtime.ray import (
    RayTransformRuntimeConfiguration,
    Transform
)

class CodeQualityRayTransformConfiguration(RayTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=CodeQualityTransformConfiguration())


if __name__ == "__main__":
    launcher = RayTransformLauncher(CodeQualityRayTransformConfiguration())
    launcher.launch()


class CodeQuality(Transform):
    def __init__(self, **kwargs):
        super().__init__(CodeQualityTransformConfiguration(), **kwargs)
        

