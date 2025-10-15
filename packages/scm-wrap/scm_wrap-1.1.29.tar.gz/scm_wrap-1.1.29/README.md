# scm-wrap

Source Code Management module wrapper. This module aims to wrap access to Git, Subversion and other SCMs repositories.

## Installation
```sh
pip install .
```

## Usage
```python
from scmwrap.repo import GitRepo
from pathlib import Path

repo = GitRepo("https://example.com/test-project.git", Path("/tmp/test-project"), [])
repo.checkout()
repo.list_files()
```

## Contributing
See `CONTRIBUTING.md`.
