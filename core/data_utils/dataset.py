
import torch
import os.path as osp
import torch
from torch_geometric.data import Dataset

class CustomDGLDataset(Dataset):
    def __init__(self, name, pyg_data):
        self.name = name
        self.pyg_data = pyg_data

    def __len__(self):
        return 1

    def __getitem__(self, idx):

        data = self.pyg_data
        g = dgl.DGLGraph()
        if self.name == 'ogbn-arxiv' or self.name == 'ogbn-products':
            edge_index = data.edge_index.to_torch_sparse_coo_tensor().coalesce().indices()
        else:
            edge_index = data.edge_index
        g.add_nodes(data.num_nodes)
        g.add_edges(edge_index[0], edge_index[1])

        if data.edge_attr is not None:
            g.edata['feat'] = torch.FloatTensor(data.edge_attr)
        if self.name == 'ogbn-arxiv' or self.name == 'ogbn-products':
            g = dgl.to_bidirected(g)
            print(
                f"Using GAT based methods,total edges before adding self-loop {g.number_of_edges()}")
            g = g.remove_self_loop().add_self_loop()
            print(f"Total edges after adding self-loop {g.number_of_edges()}")
        if data.x is not None:
            g.ndata['feat'] = torch.FloatTensor(data.x)
        g.ndata['label'] = torch.LongTensor(data.y)
        return g

    @property
    def train_mask(self):
        return self.pyg_data.train_mask

    @property
    def val_mask(self):
        return self.pyg_data.val_mask

    @property
    def test_mask(self):
        return self.pyg_data.test_mask


# Create torch dataset
class CustomPygDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels=None):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx])
                for key, val in self.encodings.items()}
        item['node_id'] = idx
        if self.labels:
            item["labels"] = torch.tensor(self.labels[idx])

        return item

    def __len__(self):
        return len(self.encodings["input_ids"])


class CustomPyGNodeDataset(Dataset):
    def __init__(self, name, root, transform=None, pre_transform=None, pre_filter=None):
        super().__init__(root, transform, pre_transform, pre_filter)

    def len(self):
        return len(self.processed_file_names)

    def get(self, idx):
        data = torch.load(osp.join(self.processed_dir, f'data_{idx}.pt'))
        return data
    
    
class CustomLinkDataset(Dataset):
    def __init__(self,  root, name, transform=None, pre_transform=None):
        super(CustomLinkDataset, self).__init__(root, transform, pre_transform)
        self.name  = name
        
    @property
    def raw_file_names(self):
        # If you have raw files to download, specify their names here
        return []

    @property
    def processed_file_names(self):
        # If you have processed files, specify their names here
        return []

    def download(self):
        # Download raw data here
        pass

    def process(self):
        # Process raw data and save it to processed files
        pass

    def len(self):
        # Return the number of graphs in the dataset
        return 0

    def get(self, idx):
        # Load and return the graph at index idx
        pass
