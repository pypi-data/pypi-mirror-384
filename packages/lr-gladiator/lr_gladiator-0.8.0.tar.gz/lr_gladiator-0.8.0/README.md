# gladiator-arena

CLI + Python client for interacting with the Arena PLM.

## Install

```bash
pip install lr-gladiator
```

## Quick start

### 1) Create `login.json`

Interactive login (prompts for username/password):

```bash
gladiator login
```

Non-interactive (for CI/CD):

```bash
gladiator login --username "$ARENA_USERNAME" --password "$ARENA_PASSWORD" --ci
```

By default, this stores session details at:

```
~/.config/gladiator/login.json
```

### 2) Common commands

Get the latest approved revision for an item:

```bash
gladiator latest-approved 890-1001
```

List all files on an item (defaults to the latest approved revision):

```bash
gladiator list-files 890-1001
```

Output JSON instead of a table:

```bash
gladiator list-files 890-1001 --format json
```

List the Bill of Materials (BOM) for an item:

```bash
gladiator bom 890-1001
```

Recursively expand subassemblies up to two levels deep:

```bash
gladiator bom 890-1001 --recursive --max-depth 2
```

Download attached files to a directory named after the article:

```bash
gladiator get-files 890-1001
```

Specify a different output directory:

```bash
gladiator get-files 890-1001 --out downloads/
```

Recursively download all files in the full BOM tree:

```bash
gladiator get-files 890-1001 --recursive
```

Upload or update a file on the working revision:

```bash
gladiator upload-file 890-1001 ./datasheet.pdf --category "CAD Data" --title "Datasheet"
```

### 3) Output control

Most commands support a JSON output mode.  
Example:

```bash
gladiator bom 890-1001 --output json
```

### Example sessions

#### Human-readable

```bash
$ gladiator list-files 101-1031
Files for 101-1031 rev (latest approved)
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Name                                 ┃ Size  ┃ Checksum            ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ Drawing.pdf                          │ 12345 │ d41d8cd98f00b204e…  │
└──────────────────────────────────────┴───────┴─────────────────────┘
```

#### JSON output

```bash
$ gladiator list-files 101-1031 --format json
{
  "article": "101-1031",
  "revision": "EFFECTIVE",
  "files": [
    {
      "filename": "Drawing.pdf",
      "size": 12345,
      "checksum": "d41d8cd98f00b204e9800998ecf8427e"
    }
  ]
}
```

## Programmatic use

```python
from gladiator import ArenaClient, load_config

client = ArenaClient(load_config())
rev = client.get_latest_approved_revision("890-1001")
files = client.list_files("890-1001", rev)
```

## Development

```bash
python -m pip install -e .[dev]
python -m build
```

## FAQ

- **Where is the config kept?**
  `~/.config/gladiator/login.json` (override with `GLADIATOR_CONFIG`)

- **How do I run non-interactively?**
  Pass `--ci` together with `--username` and `--password` (or use environment variables).

- **What does `--recursive` do?**
  Expands subassemblies and downloads or lists all contained items up to the given `--max-depth`.

- **How does Gladiator handle authentication?**
  It performs a `/login` call and stores the resulting `arenaSessionId` for reuse. If it expires, re-run `gladiator login`.
