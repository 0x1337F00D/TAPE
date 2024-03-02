# Import the W&B Python Library and log into W&B
import wandb

# Import objective relevant libraries
import os
import sys
from typing import Dict
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Import organization
import numpy as np
import scipy.sparse as ssp
import torch
from utils import (
    get_git_repo_root_path
)

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.manifold import TSNE
import random 
from numba.typed import List
from torch_geometric.utils import to_scipy_sparse_matrix    
from Embedding.node2vec_tagplus import node2vec, data_loader
from yacs.config import CfgNode as CN

wandb.login()
FILE_PATH = get_git_repo_root_path() + '/'


def objective(config=None):
    with wandb.init(config=config):
        config = wandb.config
        
        cfg_file = FILE_PATH + "core/configs/pubmed/node2vec.yaml"
        # # Load args file
        with open(cfg_file, "r") as f:
            args = CN.load_cfg(f)
        
        # Set Pytorch environment
        torch.set_num_threads(args.num_threads)
        
        _, _, splits = data_loader[args.data.name](args)
        
        # ust test edge_index as full_A
        full_edge_index = splits['test'].edge_index
        
        # Access individual parameters
        walk_length = config.walk_length
        num_walks = 80
        p = 0.5 
        q = 0.5
        
        embed_size = 64
        ws = 5
        iter = 100
        num_neg_samples = 1
        
        # G = nx.from_scipy_sparse_matrix(full_A, create_using=nx.Graph())
        adj = to_scipy_sparse_matrix(full_edge_index)

        embed = node2vec(adj, 
                         embedding_dim=embed_size,
                         walk_length=walk_length, 
                         walks_per_node=num_walks,
                         workers=8, 
                         window_size=ws, 
                         num_neg_samples=num_neg_samples,
                         p=p,
                         q=q)
    
        # embedding method 
        X_train_index, y_train = splits['train'].edge_label_index.T, splits['train'].edge_label
        # dot product
        X_train = embed[X_train_index]
        X_train = np.multiply(X_train[:, 1], (X_train[:, 0]))
        X_test_index, y_test = splits['test'].edge_label_index.T, splits['test'].edge_label
        # dot product 
        X_test = embed[X_test_index]
        X_test = np.multiply(X_test[:, 1], (X_test[:, 0]))
        
        
        clf = LogisticRegression(solver='lbfgs',max_iter=iter, multi_class='auto')
        clf.fit(X_train, y_train)

        score = clf.score(X_test, y_test)
        print("acc", score)
        wandb.log({"score": score})
    return score


# 2: Define the search space
sweep_config = {
    "method": "bayes",
    "metric": {"goal": "maximize", "name": "score"},
    "parameters": {
        "walk_length": {"max": 30, "min": 5, 'distribution': 'int_uniform'},
        # "num_walks": {"values": [40, 60, 80]},
        # "embed_size": {"max": 128, "min": 32, 'distribution': 'int_uniform'},
        "window_size": {"max": 10, "min": 1, 'distribution': 'int_uniform'},
        # "p": {"max": 1, "min": 0.0, 'distribution': 'uniform'},
        # "q": {"max": 1, "min": 0.0, 'distribution': 'uniform'},
        # "ws": {"values": [3, 5, 7]},
        # "iter": {"values": [1, 3, 7]},
        # "num_neg_samples": {"values": [1, 3, 5]},
    },
}

# 3: Start the sweep
sweep_id = wandb.sweep(sweep=sweep_config, project="embedding-sweep")
import pprint

pprint.pprint(sweep_config)
wandb.agent(sweep_id, objective, count=40)

