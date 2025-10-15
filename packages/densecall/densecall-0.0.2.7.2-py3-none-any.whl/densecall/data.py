"""
modified based on Bonito data
"""

import importlib
import os
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
import h5py
from transformers import AutoTokenizer, AutoModel
import numpy as np
from torch.utils.data import DataLoader
from torch.utils.data import BatchSampler, SubsetRandomSampler, Sampler

class ChunkDataSet:
    def __init__(self, chunks, chunk_lengths, targets, lengths):
        
        self.chunks = chunks
        self.chunk_lengths = chunk_lengths
        self.chunks = np.expand_dims(chunks, axis=1)
        self.targets = targets
        self.lengths = lengths

    def __getitem__(self, i):

        return (
            self.chunks[i].astype(np.float32),
            self.chunk_lengths[i].astype(np.int64),
            self.targets[i].astype(np.int64),
            self.lengths[i].astype(np.int64),
        )

    def __len__(self):
        return len(self.lengths)




class HDF5Dataset(Dataset):
    def __init__(self, recfile="/tmp/train.hdf5"):
        self.recfile = recfile
        with h5py.File(self.recfile, 'r', libver='v110') as file:
            self.dataset_len, self.seqlen = file["events"].shape
            #print(file['labels'].chunks)

    def open_hdf5(self):
        self.h5 = h5py.File(self.recfile, 'r')
        self.chunks = self.h5["events"]
        self.chunk_lengths = np.full(self.dataset_len, self.seqlen, dtype=np.int64)
        self.targets = self.h5["labels"]
        self.lengths = self.h5["labels_len"]
        self.chunk_size = self.chunks.chunks
        #print(self.chunk_lengths)
        
    def __getitem__(self, i):
        if not hasattr(self, "h5"):
            self.open_hdf5()

        #print(chunks.shape, targets.shape, lengths.shape)
        return (
            self.chunks[i].astype(np.float32),
            self.chunk_lengths[i].astype(np.int64),
            self.targets[i].astype(np.int64),
            self.lengths[i].astype(np.int64),
        )
        
    def __len__(self):
        return self.dataset_len



class SequentialSampler(Sampler[int]):
    """
    Samples elements sequentially, always in the same order.

    Args:
        data_source (Dataset): dataset to sample from
        chunks (int, optional): number of chunks to sample. Defaults to None.
    """

    def __init__(self, data_source, chunks=None) -> None:
        self.data_source = data_source
        self.chunks = chunks
        self.data_len = len(self.data_source)
        self.split = min(self.chunks, self.data_len) if self.chunks else self.data_len

    def __iter__(self):
        return iter(range(self.split))

    def __len__(self):
        return self.data_len
        
def load_script(directory, name="dataset", suffix=".py", **kwargs):
    directory = Path(directory)
    filepath = (directory / name).with_suffix(suffix)
    spec = importlib.util.spec_from_file_location(name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    loader = module.Loader(**kwargs)
    return loader.train_loader_kwargs(**kwargs), loader.valid_loader_kwargs(**kwargs)


def load_numpy(limit, directory, valid_chunks=None, mod=False):
    """
    Returns training and validation DataLoaders for data in directory.
    """
    
    if not mod and os.path.exists(os.path.join(directory, 'train.hdf5')):
        
        train_loader_kwargs = {"dataset": HDF5Dataset(os.path.join(directory, 'train.hdf5'))}
        valid_loader_kwargs = {"dataset": HDF5Dataset(os.path.join(directory, 'valid.hdf5'))}
        print(f"[loading hdf5 format dataset]")
    else:
        train_data = load_numpy_datasets(limit=limit, directory=directory, mod=mod)
        if os.path.exists(os.path.join(directory, 'validation')):
            valid_data = load_numpy_datasets(limit=valid_chunks,
                directory=os.path.join(directory, 'validation'), mod=mod
            )
        else:
            print("[validation set not found: splitting training set]")
            if valid_chunks is None:
                split = np.floor(len(train_data[0]) * 0.97).astype(np.int32)
            else:
                split = max(0, len(train_data[0]) - valid_chunks)

            valid_data = [x[split:] for x in train_data]
            train_data = [x[:split] for x in train_data]
        
        train_loader_kwargs = {"dataset": ChunkDataSet(*train_data)}
        valid_loader_kwargs = {"dataset": ChunkDataSet(*valid_data)}
        print(f"[loading numpy format dataset]")
    return train_loader_kwargs, valid_loader_kwargs


def load_numpy_datasets(limit=None, directory=None, mod=False):
    """
    Returns numpy chunks, targets and lengths arrays.
    """
    if directory is None:
        directory = default_data

    chunks = np.load(os.path.join(directory, "chunks.npy"), mmap_mode='r')
    if mod:
        print(f"[loading mod numpy format dataset]")
        targets = np.load(os.path.join(directory, "mod_references.npy"), mmap_mode='r')
    else:
        targets = np.load(os.path.join(directory, "references.npy"), mmap_mode='r')
        
    lengths = np.load(os.path.join(directory, "reference_lengths.npy"), mmap_mode='r')
    try:
        chunk_lengths = np.load(os.path.join(directory, "chunk_lengths.npy"), mmap_mode='r')
    except:
        n, T = chunks.shape
        chunk_lengths = np.full(n, T, dtype=np.int16)

    indices = os.path.join(directory, "indices.npy")

    if os.path.exists(indices):
        idx = np.load(indices, mmap_mode='r')
        idx = idx[idx < lengths.shape[0]]
        if limit:
            idx = idx[:limit]
        return chunks[idx, :], chunk_lengths[idx, :], targets[idx, :], lengths[idx]

    if limit:
        chunks = chunks[:limit]
        chunk_lengths = chunk_lengths[:limit]
        targets = targets[:limit]
        lengths = lengths[:limit]
    #print(chunks.shape)
    if len(chunks) < 3e6:
        return np.array(chunks), np.array(chunk_lengths), np.array(targets), np.array(lengths)
    return chunks, chunk_lengths, targets, lengths
