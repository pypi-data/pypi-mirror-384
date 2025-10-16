Wrapper on an iterable to support interruption & auto resume, retrying and multiprocessing.

The code is tested on Linux.

# APIs

Please refer to the signature of function.iterate_wrapper or generator.IterateWrapper for usage.

# Examples

## iterate_wrapper

```python
from typing import IO
from time import sleep

from iterwrap import iterate_wrapper

def square(f_io: IO, item: int, fn: Callable[[float], float]):
    result = fn(item)
    f_io.write(f"{result}\n")

data = list(range(10))
num_workers = 3
iterate_wrapper(
    square,
    data,
    output="output.txt",
    num_workers=num_workers,
    fn=lambda x: x * x,
)

with open("output.txt") as f:
    print(f.read()) # [0, 1, 4, 9, ..., 81]
```

## IterateWrapper

Just the same as `tqdm.tqdm`.

```python
from iterwrap import IterateWrapper

data = [1, 2, 3]
results = []
for i in IterateWrapper(data):
    results.append(i * i)
print(results) # [1, 4, 9]
```
