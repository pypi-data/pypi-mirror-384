
<img width="300" alt="trm-fig1" src="https://github.com/user-attachments/assets/950db79e-5f9c-4fec-a4e4-7b9355b39ce8" />

## Tiny Recursive Model (TRM)

Implementation of [Tiny Recursive Model](https://arxiv.org/abs/2510.04871) (TRM), improvement to [HRM](https://github.com/lucidrains/hrm) from Sapient AI, by [Alexia Jolicoeur-Martineau](https://ajolicoeur.wordpress.com/about/)

Official repository is [here](https://github.com/SamsungSAILMontreal/TinyRecursiveModels)

<img width="300" alt="trm-fig3" src="https://github.com/user-attachments/assets/bfe3dd2a-e859-492a-84d5-faf37339f534" />

## Install

```bash
$ pip install tiny-recursive-model
```

## Usage

```python
import torch
from tiny_recursive_model import TinyRecursiveModel, MLPMixer1D, Trainer

trm = TinyRecursiveModel(
    dim = 16,
    num_tokens = 256,
    network = MLPMixer1D(
        dim = 16,
        depth = 2,
        seq_len = 256
    ),
)

# mock dataset

from torch.utils.data import Dataset
class MockDataset(Dataset):
    def __len__(self):
        return 16

    def __getitem__(self, idx):
        inp = torch.randint(0, 256, (256,))
        out = torch.randint(0, 256, (256,))
        return inp, out

mock_dataset = MockDataset()

# trainer

trainer = Trainer(
    trm,
    mock_dataset,
    epochs = 1,
    batch_size = 16,
    cpu = True
)

trainer()

# inference

pred_answer, exit_indices = trm.predict(
    torch.randint(0, 256, (1, 256)),
    max_deep_refinement_steps = 12,
    halt_prob_thres = 0.1
)

# save to collection of specialized networks for tool call

torch.save(trm.state_dict(), 'saved-trm.pt')

```

## Citations

```bibtex
@misc{jolicoeurmartineau2025morerecursivereasoningtiny,
    title   = {Less is More: Recursive Reasoning with Tiny Networks}, 
    author  = {Alexia Jolicoeur-Martineau},
    year    = {2025},
    eprint  = {2510.04871},
    archivePrefix = {arXiv},
    primaryClass = {cs.LG},
    url     = {https://arxiv.org/abs/2510.04871}, 
}
```
