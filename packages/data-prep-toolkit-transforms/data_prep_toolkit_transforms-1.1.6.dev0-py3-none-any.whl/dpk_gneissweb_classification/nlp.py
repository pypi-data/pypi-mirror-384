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

from typing import Any

import pyarrow as pa
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from data_processing.utils import TransformUtils, get_dpk_logger
from dpk_gneissweb_classification.classification_models import FastTextModel


logger = get_dpk_logger()


def get_label_ds_pa(
    table: pa.table,
    model: Any,
    url: str,
    content_column_name: str,
    output_label_column_name: str,
    output_score_column_name: str,
    max_workers=1
) -> tuple[pa.table, dict[str, Any]]:
    nlp = FastTextModel(model, url)
    logger.debug(f"Classifying with {max_workers} threads")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:     # Set max_workers for desired thread count
        detected_label = pa.Table.from_pylist(
            list(
                map(
                    lambda r: {"label": r[0], "score": r[1]},
                    list(executor.map(nlp.detect_label, table[content_column_name].to_pylist())),
                )
            )
        )
    logger.debug(f"Classifying with {max_workers} threads completed")





    stats = pa.table([detected_label["label"]], names=["label"]).group_by("label").aggregate([("label", "count")])
    stats_dict = {}
    for batch in stats.to_batches():
        d = batch.to_pydict()
        for label, count in zip(d["label"], d["label_count"]):
            stats_dict[label] = count
    result = TransformUtils.add_column(table=table, name=output_label_column_name, content=detected_label["label"])
    result = TransformUtils.add_column(table=result, name=output_score_column_name, content=detected_label["score"])
    return result, stats_dict
