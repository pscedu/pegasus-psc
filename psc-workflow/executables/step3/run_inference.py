import os
import sys

# replace this with your modelzoo path
MODELZOO_PATH = os.getenv(key='MODELZOO_PATH', default='/ocean/neocortex/cerebras/modelzoo')
sys.path.append(MODELZOO_PATH)

import argparse
import json
from modelzoo.transformers.pytorch.huggingface_common.modeling_bert import BertForSequenceClassification, BertConfig
from modelzoo.transformers.pytorch.bert.fine_tuning.classifier.input.BertClassifierDataProcessor import SST2Dataset
import numpy as np
import torch
from torch.nn import MSELoss
from tqdm import tqdm
import yaml


def get_mae(arr1, arr2):
    diff = np.abs(np.subtract(arr1, arr2))
    mae = np.sum(diff)
    mae /= diff.shape[0]
    print("MAE:", mae)
    return mae


def get_rsquared(arr1, arr2):
    arr_bar = np.mean(arr1)
    ss_tot = ((arr1 - arr_bar) ** 2).sum()
    ss_res = ((arr1 - arr2) ** 2).sum()
    return 1 - (ss_res / ss_tot)


def run_model(model, dataloader):
    count = 0
    running_loss = 0.
    preds = []
    true = []

    with torch.no_grad():
        for i, data in tqdm(enumerate(dataloader)):
            outputs = model(data['input_ids'])
            labels = data['labels']
            logits = outputs.logits.squeeze()
            preds.extend(logits.tolist())
            true.extend(labels.tolist())
            loss = loss_fn(logits, labels)
            loss *= data['labels'].size(0)
            count += data['labels'].size(0)
            running_loss += loss
        running_loss /= count
        print("RUNNING LOSS:", running_loss)

    values = {'preds': preds, 'labels': true}
    return values


# ======Shreya================
with open('regression_params_inference.yaml', 'r') as f:
    params = yaml.safe_load(f)
f.close()
# =========Shreya==============

model_params = params['model']
model_params['layer_norm_epsilon'] = 1e-5

config = BertConfig(
    vocab_size=model_params['vocab_size'],
    hidden_size=model_params['hidden_size'],
    num_hidden_layers=model_params['num_hidden_layers'],
    num_attention_heads=model_params['num_heads'],
    intermediate_size=model_params['filter_size'],
    hidden_act=model_params['encoder_nonlinearity'],
    hidden_dropout_prob=model_params['dropout_rate'],
    attention_probs_dropout_prob=model_params['attention_dropout_rate'],
    max_position_embeddings=model_params['max_position_embeddings'],
    classifier_dropout=model_params['task_dropout'],
    problem_type=model_params['problem_type'],
    num_labels=1,
    layer_norm_eps=float(model_params['layer_norm_epsilon'])
)

loss_fn = MSELoss()

if torch.cuda.is_available():
    device = 'cuda'
else:
    device = 'cpu'

parser = argparse.ArgumentParser()
parser.add_argument('--checkpoint_path')
parser.add_argument('--outfile')
args = parser.parse_args()

model = BertForSequenceClassification(config)
model.load_state_dict(torch.load(args.checkpoint_path, weights_only=True, map_location=device)['model'])
dataset = SST2Dataset(params['train_input'], is_training=False)
dataloader = torch.utils.data.DataLoader(dataset, batch_size=params['eval_input'].get('batch_size'), shuffle=False)
model.eval()
values = run_model(model, dataloader)

# =========Shreya================
preds_np = np.asarray(values["preds"], dtype=np.float32)
labels_np = np.asarray(values["labels"], dtype=np.float32)

mae = get_mae(labels_np, preds_np)
r2 = get_rsquared(labels_np, preds_np)

print(f"MAE: {mae:.6f}")
print(f"R^2: {r2:.6f}")

# add metrics to JSON
values["metrics"] = {
    "mae": float(mae),
    "r2": float(r2)
}
# ====== Shreya ================

with open('{}'.format(args.outfile), 'w') as f:
    json.dump(values, f, indent=2)
f.close()
