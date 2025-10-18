# F9 Columnar

<div align="center">

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![python](https://img.shields.io/badge/-Python_3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![pytorch](https://img.shields.io/badge/-PyTorch_2.8-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![pytorch](https://img.shields.io/pypi/v/f9columnar)](https://pypi.org/project/f9columnar/)

</div>

A lightweight Python package for processing of ROOT and HDF5 event data in high energy physics.

### Project description

This package is designed for efficient handling of large datasets. Built on PyTorch, Awkward Array, and Uproot, it utilizes PyTorch's DataLoader with an IterableDataset to enable parallel processing. It implements a columnar event loop, returning batches of events in a format compatible with standard PyTorch training loops over multiple epochs.

It is optimized for machine learning applications, the package provides `RootDataLoader` and `Hdf5DataLoader` classes for data loading from ROOT and HDF5 files. Additionally, it supports parallel data processing through a modular pipeline of processor classes, allowing users to chain operations for complex computations and histogramming.

##  Setup

### Install with PyTorch GPU

```shell
pip install f9columnar[torch]
```

### Install with PyTorch CPU (recommended)

```shell
pip install f9columnar
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Install without PyTorch

```shell
pip install f9columnar
```

## Examples

- [Getting started](#getting-started)
- [Using processors and histogramming](#using-processors-and-histogramming)
- [Converting ROOT to HDF5](#converting-root-to-hdf5)
- [Feature scaling](#feature-scaling)
- [HDF5 ML DataLoader](#hdf5-ml-dataloader)

### Getting started

The most basic usage of the package is to load data from ROOT files using the `get_root_dataloader` function. This function returns a PyTorch DataLoader that yields batches of events as Awkward Arrays.

```python
from f9columnar.root_dataloader import get_root_dataloader

def filter_branch(branch):
    # select only these two branches
    return branch == "tau_p4" or branch == "lephad_p4"

# root_dataloader is an instance of a torch DataLoader that uses an IterableDataset
root_dataloader, total = get_root_dataloader(
    name="data", # name identifier
    files=files, # root files
    key="NOMINAL", # root file tree name
    step_size=10**5, # number of events per array batch to read into memory
    num_workers=12, # number of workers for parallel processing
    processors=None, # arbitrary calculations on arrays
    filter_name=filter_branch, # filter branches
)

# loop over batches of events from .root file(s), each batch is an awkward array
for events in root_dataloader:
    arrays, report = events
    # ... do something with the arrays
```

### Using processors and histogramming

The following example demonstrates how to define variables, apply a cut, and create a histogram using processors.

Calculations on arrays within worker processes can be performed using a `Processor`. Multiple processors can be linked together in a `ProcessorsGraph`, forming a directed acyclic graph (DAG). These processors are applied to arrays in the sequence determined by the DAG’s topological order.

Each worker executes the same processor graph on batches of event data and returns the results to the event loop once processing is complete. In the example above, 12 (`num_workers`) processor graphs would be running in parallel, each handling small batches of events. Below is an example demonstrating how to calculate the tau visible mass and apply a cut to this variable.

```python
from f9columnar.processors import ProcessorsGraph, CheckpointProcessor
from f9columnar.object_collections import Variable, VariableCollection, Cut, CutCollection
from f9columnar.histograms import HistogramProcessor

class VisibleMass(Variable): # Variable is a Processor
    name = "vis_mass" # processor name
    branch_name = "lephad_p4" # name of the branch in the .root file

    def __init__(self):
        super().__init__()

    def run(self, arrays): # each processor must implement a run method
        lephad_p4 = arrays[self.branch_name] # branch_name is the name of the field in the ak array
        v = get_kinematics_vector(lephad_p4) # use vector with px, py, pz and E

        arrays["tau_vis_mass"] = v.m # add a new field to the arrays

        return {"arrays": arrays} # return the arrays (can also return None if no changes are made)

class CutVisibleMass(Cut): # Cut is a Processor
    name = "vis_mass_cut"
    branch_name = None # is not a branch in ntuples but was defined in the VisibleMass processor

    def __init__(self, cut_lower, cut_upper): # argumnets of the processor
        super().__init__()
        self.cut_lower = cut_lower
        self.cut_upper = cut_upper

    def run(self, arrays):
        mask = (arrays["tau_vis_mass"] > self.cut_lower) & (arrays["tau_vis_mass"] < self.cut_upper)
        arrays = arrays[mask] # apply the cut

        return {"arrays": arrays} # return must be a dictionary with key name for the argument of the next processor

class Histograms(HistogramProcessor): # HistogramProcessor is a Processor
    def __init__(self, name="histograms"):
        super().__init__(name)

        self.make_hist1d("tau_vis_mass", 20, 80.0, 110.0) # make a histogram with 20 bins from 80 to 110 GeV

    def run(self, arrays):
        return super().run(arrays) # auto fills histograms if array names match histogram names

var_collection = VariableCollection(VisibleMass, init=False) # will initialize later
cut_collection = CutCollection(CutVisibleMass, init=False)

collection = var_collection + cut_collection # add collections of objects together
branch_filter = collection.branch_name_filter # defines the branches that the processors depend on

graph = ProcessorsGraph() # graph has a fit method that gets called inside the root_dataloader

# add nodes to the graph
graph.add(
    CheckpointProcessor("input"), # input node
    var_collection["vis_mass"](), # initialize the processor
    cut_collection["vis_mass_cut"](cut_lower=90.0, cut_upper=100.0),
    CheckpointProcessor("output", save_arrays=True), # saves final arrays
    Histograms(),
)

# build a processor graph
graph.connect(
    [
        ("input", "vis_mass"),
        ("vis_mass", "vis_mass_cut"),
        ("vis_mass_cut", "output"),
        ("output", "histograms"),
    ]
)

# plot the graph
graph.draw("graph.pdf")

# ... pass into the root_dataloader with the processors argument (e.g. processors=graph)
# in this case the dataloader will return a fitted graph
for processed_graph in dataloader:
    histograms = processed_graph["histograms"].hists
    arrays = processed_graph["output"].arrays
    # ... do something with the histograms and arrays
```

A higher level of abstraction is also possible using the [`ColumnarEventLoop`](f9columnar/run.py) class. See benchmark [examples](benchmark/f9columnar_benchmark.py) for some more details.


### Converting ROOT to HDF5

The package also includes a utility to convert ROOT files to HDF5 format.

Event shuffling is supported to randomize the order of events in the output HDF5 file. This is particularly useful for machine learning applications where data order can impact training. This is done using a 2-pass shuffling algorithm that is memory efficient and works well with large datasets:

```
first pass:
create empty datasets called piles p[0], p[1], ..., p[n-1] on disk as HDF5 files
for step size of events x from a root file i:
    for chunk of events y:
        j = random integer in [0, n-1]
        append y to p[j]

second pass:
for j in [0, n-1] in random order:
    read all events from p[j] into memory
    shuffle p[j] in memory
    for batch of events z in p[j]:
        yield z to DataLoader
```

Below is an example of how to use the [writing utility](https://gitlab.cern.ch/ijs-f9-ljubljana/F9Columnar/-/blob/main/f9columnar/ml/hdf5_writer.py?ref_type=heads#L134). In the example, the dataloader loop is abstracted away using the `ColumnarEventLoop` class.

```python
from f9columnar.ml.hdf5_writer import Hdf5WriterPostprocessor

# we will make a linear chain of processors
analysis_graph = ProcessorsGraph()
analysis_graph.add(
    CheckpointProcessor("input"),
    *analysis_collection.as_list(), # add a collection of processors that do some calculations
    CheckpointProcessor("output", save_arrays=True), # save arrays at the end of the chain for the hdf5 writer
)
analysis_graph.chain()
analysis_graph.draw("hdf_analysis_graph.pdf")

# create the hdf5 writer postprocessor
# a postprocessor is a special processor that runs after the main processor graph and is executed in the main process
# ProcessorsGraph can be thought of as a map step and PostprocessorsGraph as a reduce step
hdf5_writer = Hdf5WriterPostprocessor(
    output_file,
    flat_column_names=["tau_vis_mass"], # flat columns to save
    jagged_column_names=None, # jagged columns to save, pads extra values with a pad value if needed
    chunk_shape=512, # shape of chunks to write to hdf5 file
    n_piles=1024, # number of piles to use for shuffling
    pile_assignment="random", # how to assign events to piles, random or deque
    merge_piles=False, # merge piles into a single hdf5 file at the end
    enforce_dtypes=None, # enforce specific dtypes for columns
    save_node="output", # name of the node in the processor graph to save arrays from
)

# create a linear chain of postprocessors
postprocessors_graph = PostprocessorsGraph()
postprocessors_graph.add(
    CheckpointPostprocessor("input"),
    hdf5_writer,
)
postprocessors_graph.chain()
postprocessors_graph.draw("hdf_post_analysis_graph.pdf")

# we can make a root dataset for MC and data files lists
data_dataset = RootPhysicsDataset(f"Data", [str(f) for f in data_files], is_data=True)
mc_dataset = RootPhysicsDataset(f"MC", [str(f) for f in mc_files], is_data=False)

# get the branch filter from the analysis collection to not load unnecessary branches
branch_filter = analysis_collection.branch_name_filter

# setup the data dataloader
data_dataset.setup_dataloader(**dataloader_config)
data_dataset.init_dataloader(processors=analysis_graph)

# setup the mc dataloader
mc_dataset.setup_dataloader(**dataloader_config)
mc_dataset.init_dataloader(processors=analysis_graph)

# run the DataLoader event loop over batches of events for both datasets
event_loop = ColumnarEventLoop(
    mc_datasets=[mc_dataset], # supports multiple datasets
    data_datasets=[data_dataset], # supports multiple datasets
    postprocessors_graph=postprocessors_graph,
    fit_postprocessors=True,
    cut_flow=False,
)
event_loop.run() # iterates over batches of events in both datasets

postprocessors_graph["hdf5WriterPostprocessor"].close() # close the file handles
```

Note that variables ending with `*_type` have a special meaning in the HDF5 writer. For example, a variable named `label_type` can be used to determine the type of the event (e.g., signal or background) and will be saved as a column in the HDF5 file. This is useful for classification tasks in machine learning. Another special variable is `weights`, which will be used to store event weights in the HDF5 file. These special variables help in organizing and utilizing the data effectively for training machine learning models.

### Feature scaling

The package also includes a utility to scale the entire HDF5 dataset using sklearn scalers. This is particularly useful for machine learning applications where feature scaling can improve model performance.

```python
from f9columnar.ml.dataset_scaling import DatasetScaler

ds_scaler = DatasetScaler(
    files, # list of hdf5 files
    scaler_type, # minmax, maxabs, standard, robust, quantile, power, logit, standard_logit
    features, # names of the features to scale
    scaler_save_path=save_path,
    n_max=None, # maximum number of events to use for fitting the scaler if the scaler does not have partial fit
    extra_hash="", # extra string to add to the hash of the scaler
    scaler_kwargs=scaler_kwargs, # kwargs for the scaler
    dataloader_kwargs=dataloader_kwargs, # kwargs for the dataloader
)
ds_scaler.feature_scale()
```

The result will be a pickle file with the fitted scaler object that can be used in the HDF5 ML DataLoader as:

```python
feature_scaling_kwargs = {
    "scaler_type": scaler_type,
    "scaler_path": save_path, # where the scaler was saved
    "scalers_extra_hash": "",
}
dataset_kwargs = dataset_kwargs | feature_scaling_kwargs
```

Note that categorical features use a custom `LabelEncoder` that supports partial fitting and can be used in an online fashion.

### HDF5 ML DataLoader

We will use PyTorch Lightning to demonstrate how to use the [Hdf5IterableDataset](https://gitlab.cern.ch/ijs-f9-ljubljana/F9Columnar/-/blob/main/f9columnar/hdf5_dataloader.py?ref_type=heads#L375) in a training loop.

```python
from typing import Any, Callable

import lightning as L
from torch.utils.data import DataLoader

from f9columnar.ml.hdf5_ml_dataloader import (
    WeightedBatch,
    WeightedBatchType,
    default_setup_func,
    get_ml_hdf5_dataloader,
)

class LightningHdf5DataModule(L.LightningDataModule):
    def __init__(
        self,
        name: str,
        files: str | list[str],
        column_names: list[str],
        stage_split_piles: dict[str, list[int] | int],
        shuffle: bool = False,
        collate_fn: Callable[[list[WeightedBatch]], WeightedBatchType] | None = None,
        dataset_kwargs: dict[str, Any] | None = None,
        dataloader_kwargs: dict[str, Any] | None = None,
    ) -> None:
        super().__init__()
        self.dl_name = name
        self.files = files
        self.column_names = column_names
        self.stage_split_piles = stage_split_piles
        self.shuffle = shuffle
        self.collate_fn = collate_fn
        self.dataset_kwargs = dataset_kwargs
        self.dl_kwargs = dataloader_kwargs

    def _get_dataloader(self, stage: str) -> DataLoader:
        # returns DataLoader object for the given stage, selection and number of events
        dl, _, _ = get_ml_hdf5_dataloader(
            f"{stage} - {self.dl_name}",
            self.files,
            self.column_names,
            stage_split_piles=self.stage_split_piles,
            stage=stage,
            shuffle=self.shuffle,
            collate_fn=self.collate_fn,
            dataset_kwargs=self.dataset_kwargs,
            dataloader_kwargs=self.dl_kwargs,
        )
        return dl

    def train_dataloader(self) -> DataLoader:
        return self._get_dataloader("train")

    def val_dataloader(self) -> DataLoader:
        return self._get_dataloader("val")

    def test_dataloader(self) -> DataLoader:
        return self._get_dataloader("test")

def events_collate_fn(batch: tuple[WeightedDatasetBatch, dict[str, Any]]) -> WeightedBatchType:
    ds, reports = batch[0]["events"], batch[1]
    # these are the return values from the DataLoader
    return ds.X, ds.y, ds.w, ds.y_aux, reports

# can additionally pass any kwargs to the dataset and it will be forwarded to the reports dictionary
dataset_kwargs = {
    "batch_size": 128, # number of events per batch
    "imbalanced_sampler": None, # supports oversampling and undersampling
    "drop_last": True, # drop last incomplete batch
}

# custom function to process the dataset inside the DataLoader workers
# the function should be: Callable[[StackedDatasets, MLHdf5Iterator], WeightedDatasetBatch | None]
dataset_kwargs["setup_func"] = default_setup_func

dataloader_kwargs = {
    "num_workers": -1, # use all available cores
    "prefetch_factor": 2, # number of batches to prefetch by each worker
}

dm = LightningHdf5DataModule(
    dm_name, # name of the datamodule
    files, # list of hdf5 files
    features, # names of the features to load (column names in the hdf5 file)
    stage_split_piles={"train": 512, "test": 256, "val": 256}, # number of piles for each stage
    shuffle=True, # shuffle events at each epoch
    collate_fn=events_collate_fn, # collate function to handle batches
    dataset_kwargs=dataset_kwargs, # kwargs for the dataset
    dataloader_kwargs=dataloader_kwargs, # kwargs for the dataloader
)
```
