# /// script
# dependencies = [
#   "discrete-distribution-network",
#   "datasets",
#   "wandb"
# ]
# ///

import torch

# hf datasets for easy oxford flowers training

import torchvision.transforms as T
from torch.utils.data import Dataset
from datasets import load_dataset

class OxfordFlowersDataset(Dataset):
    def __init__(
        self,
        image_size
    ):
        self.ds = load_dataset('nelorth/oxford-flowers')['train']

        self.transform = T.Compose([
            T.Resize((image_size, image_size)),
            T.PILToTensor()
        ])

    def __len__(self):
        return len(self.ds)

    def __getitem__(self, idx):
        pil = self.ds[idx]['image']
        tensor = self.transform(pil)
        return tensor / 255.

flowers_dataset = OxfordFlowersDataset(
    image_size = 64
)

# models and trainer

from discrete_distribution_network import DDN, Network, Trainer

model = Network(
    dim = 64
)

ddn = DDN(model)

trainer = Trainer(
    ddn,
    dataset = flowers_dataset,
    num_train_steps = 70_000,
    sample_temperature = 1.5,
    results_folder = './results'   # samples will be saved periodically to this folder
)

trainer()
