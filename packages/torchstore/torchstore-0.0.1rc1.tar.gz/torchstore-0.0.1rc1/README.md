# TorchStore

A storage solution for PyTorch tensors with distributed tensor support.

TorchStore provides a distributed, asynchronous tensor storage system built on top of
Monarch actors. It enables efficient storage and retrieval of PyTorch tensors across
multiple processes and nodes with support for various transport mechanisms including
RDMA when available.

Key Features:
- Distributed tensor storage with configurable storage strategies
- Asynchronous put/get operations for tensors and arbitrary objects
- Support for PyTorch state_dict serialization/deserialization
- Multiple transport backends (RDMA, regular TCP) for optimal performance
- Flexible storage volume management and sharding strategies

> ⚠️ **Early Development Warning** TorchStore is currently in an experimental
> stage. You should expect bugs, incomplete features, and APIs that may change
> in future versions. The project welcomes bugfixes, but to make sure things are
> well coordinated you should discuss any significant change before starting the
> work. It's recommended that you signal your intention to contribute in the
> issue tracker, either by filing a new issue or by claiming an existing one.

## Installation

### Env Setup
```bash
conda create -n torchstore python=3.12
pip install torch

git clone git@github.com:meta-pytorch/monarch.git
python monarch/scripts/install_nightly.py

git clone git@github.com:meta-pytorch/torchstore.git
cd torchstore
pip install -e .
```


### Development Installation

To install the package in development mode:

```bash
# Clone the repository
git clone https://github.com/your-username/torchstore.git
cd torchstore

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e '.[dev]'
```

### Regular Installation

To install the package directly from the repository:

```bash
pip install git+https://github.com/your-username/torchstore.git
```

Once installed, you can import it in your Python code:

```python
import torchstore
```

Note: Setup currently assumes you have a working conda environment with both torch & monarch (this is currently a todo).

## Usage

```python
import torch
import asyncio
import torchstore as ts

async def main():

    # Create a store instance
    await ts.initialize()

    # Store a tensor
    await ts.put("my_tensor", torch.randn(3, 4))

    # Retrieve a tensor
    tensor = await ts.get("my_tensor")


if __name__ == "__main__":
    asyncio.run(main())

```

### Resharding Support with DTensor

```python
import torchstore as ts
from torch.distributed._tensor import distribute_tensor, Replicate, Shard
from torch.distributed.device_mesh import init_device_mesh

async def place_dtensor_in_store():
    device_mesh = init_device_mesh("cpu", (4,))
    tensor = torch.arange(4)
    dtensor = distribute_tensor(tensor, device_mesh, placements=[Shard(1)])

    # Store a tensor
    await ts.put("my_tensor", dtensor)


async def fetch_dtensor_from_store()
    # You can now fetch arbitrary shards of this tensor from any rank e.g.
    device_mesh = init_device_mesh("cpu", (2,2))
    tensor = torch.rand(4)
    dtensor = distribute_tensor(
        tensor,
        device_mesh,
        placements=[Replicate(), Shard(0)]
    )

    # This line copies the previously stored dtensor into local memory.
    await ts.get("my_tensor", dtensor)

def run_in_parallel(func):
    # just for demonstrative purposes
    return func

if __name__ == "__main__":
    ts.initialize()
    run_in_parallel(place_dtensor_in_store)
    run_in_parallel(fetch_dtensor_from_store)
    ts.shutdown()

# checkout out tests/test_resharding.py for more e2e examples with resharding DTensor.
```

# Testing

Pytest is used for testing. For an examples of how to run tests (and get logs), see:
`TORCHSTORE_LOG_LEVEL=DEBUG pytest -vs --log-cli-level=DEBUG tests/test_models.py::test_main`

## License

Torchstore is BSD-3 licensed, as found in the [LICENSE](LICENSE) file.
