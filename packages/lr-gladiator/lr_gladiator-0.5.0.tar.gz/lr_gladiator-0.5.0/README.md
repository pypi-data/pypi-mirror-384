# gladiator-arena

CLI + Python client for interacting with the Arena PLM.

## Install

```bash
pip install lr-gladiator
```

## Quick start

### 1) Create `login.json`

Interactive:

```bash
gladiator login
```

`login.json` is stored at `~/.config/gladiator/login.json` by default.

### 2) Queries

Get latest approved revision for an item:

```bash
gladiator latest-approved ABC-1234
```

List files on an item (defaults to latest approved):

```bash
gladiator list-files ABC-1234
```

Download files:

```bash
gladiator get-files ABC-1234 --out downloads/
```

Upload a file to the working revision

```bash
gladiator upload-file ABC-1234 ./datasheet.pdf --reference datasheet
```

## Programmatic use

```python
from gladiator import ArenaClient, load_config
client = ArenaClient(load_config())
rev = client.get_latest_approved_revision("ABC-1234")
files = client.list_files("ABC-1234", rev)
```

## Development

```bash
python -m pip install -e .[dev]
python -m build
```

## FAQ

- **Where is the config kept?** `~/.config/gladiator/login.json` (override via `GLADIATOR_CONFIG`).
