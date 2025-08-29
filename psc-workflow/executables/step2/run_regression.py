# Copyright 2022 Cerebras Systems.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import sys

MODELZOO_PATH = os.getenv(key='MODELZOO_PATH', default='/ocean/neocortex/cerebras/modelzoo')
sys.path.append(MODELZOO_PATH)

from modelzoo.common.pytorch.run_utils import run
from modelzoo.transformers.pytorch.bert.fine_tuning.classifier.data import (
    eval_input_dataloader,
    train_input_dataloader,
)
from modelzoo.transformers.pytorch.bert.fine_tuning.classifier.model import (
    BertForSequenceClassificationModel,
)
from modelzoo.transformers.pytorch.bert.fine_tuning.classifier.utils import (
    set_defaults,
)


def main():
    run(
        BertForSequenceClassificationModel,
        train_input_dataloader,
        eval_input_dataloader,
        default_params_fn=set_defaults,
    )


if __name__ == '__main__':
    main()
