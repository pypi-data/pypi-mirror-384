# guardpycfn

Python bindings for AWS CloudFormation Guard powered by Rust + pyo3.

## Build (local)

```bash
# Requires Rust toolchain and maturin
pip install maturin
maturin develop  # builds and installs into current Python env

# Notes:
# - Uses PyO3 0.22 with abi3 (py>=3.9) so Python 3.13 is supported
# - If building against a specific interpreter, use: maturin develop --python $(which python)
```

## Usage

```python
import guardpycfn
res = guardpycfn.validate_with_guard("AWSTemplateFormatVersion: '2010-09-09'\nResources: {}\n", None)
print(res)
```

## Next steps
- Link to Guard engine (guard-ffi or internal crates)
- Map Guard results to structured matches
- Package wheels for macOS/Linux via maturin

