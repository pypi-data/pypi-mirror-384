#! /usr/bin/env python
# -*- coding: utf-8 -*-
# src/gladiator/cli.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
import typer
from rich import print
from rich.table import Table
from getpass import getpass
import requests
import sys
from .config import LoginConfig, save_config, load_config, save_config_raw, CONFIG_PATH
from .arena import ArenaClient, ArenaError

app = typer.Typer(add_completion=False, help="Arena PLM command-line utility")


@app.command()
def login(
    username: Optional[str] = typer.Option(
        None, "--username", envvar="GLADIATOR_USERNAME"
    ),
    password: Optional[str] = typer.Option(
        None, "--password", envvar="GLADIATOR_PASSWORD"
    ),
    base_url: Optional[str] = typer.Option(
        "https://api.arenasolutions.com/v1", help="Arena API base URL"
    ),
    verify_tls: bool = typer.Option(True, help="Verify TLS certificates"),
    non_interactive: bool = typer.Option(
        False, "--ci", help="Fail instead of prompting for missing values"
    ),
    reason: Optional[str] = typer.Option(
        "CI/CD integration", help="Arena-Usage-Reason header"
    ),
):
    """Create or update ~/.config/gladiator/login.json for subsequent commands.

    This performs a `/login` call against Arena and stores the JSON (including arenaSessionId) in login.json.
    """
    if not username and not non_interactive:
        username = typer.prompt("Email/username")
    if not password and not non_interactive:
        password = getpass("Password: ")
    if non_interactive and (not username or not password):
        raise typer.BadParameter(
            "Provide --username and --password (or set env vars) for --ci mode"
        )

    # Perform login
    sess = requests.Session()
    sess.verify = verify_tls
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Arena-Usage-Reason": reason or "gladiator/cli",
        "User-Agent": "gladiator-arena/0.1",
    }
    url = f"{(base_url or '').rstrip('/')}/login"
    resp = sess.post(
        url, headers=headers, json={"email": username, "password": password}
    )
    try:
        resp.raise_for_status()
    except Exception as e:
        typer.secho(
            f"Login failed: {e} Body: {resp.text[:400]}", fg=typer.colors.RED, err=True
        )
        raise typer.Exit(2)

    data = resp.json()

    # Merge our client settings alongside the session info into the same file (compatible with your bash scripts)
    data.update(
        {
            "base_url": base_url,
            "verify_tls": verify_tls,
            "reason": reason,
        }
    )
    save_config_raw(data)
    print(f"[green]Saved session to {CONFIG_PATH}[/green]")


def _client() -> ArenaClient:
    cfg = load_config()
    return ArenaClient(cfg)


@app.command("latest-approved")
def latest_approved(
    item: str = typer.Argument(..., help="Item/article number"),
    format: Optional[str] = typer.Option(
        None, "--format", "-f", help="Output format: human (default) or json"
    ),
):
    """Print latest approved revision for the given item number."""
    try:
        rev = _client().get_latest_approved_revision(item)
        if format == "json":
            json.dump({"article": item, "revision": rev}, sys.stdout, indent=2)
            sys.stdout.write("\n")
        else:
            print(rev)
    except requests.HTTPError as e:
        typer.secho(f"Arena request failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(2)
    except ArenaError as e:
        typer.secho(str(e), fg=typer.colors.RED, err=True)
        raise typer.Exit(2)


@app.command("list-files")
def list_files(
    item: str = typer.Argument(..., help="Item/article number"),
    revision: Optional[str] = typer.Option(
        None,
        "--rev",
        help="Revision selector: WORKING | EFFECTIVE | <label> (default: EFFECTIVE)",
    ),
    format: Optional[str] = typer.Option(
        None, "--format", "-f", help="Output format: human (default) or json"
    ),
):
    try:
        files = _client().list_files(item, revision)
        if format == "json":
            json.dump(
                {"article": item, "revision": revision, "files": files},
                sys.stdout,
                indent=2,
            )
            sys.stdout.write("\n")
            return

        table = Table(title=f"Files for {item} rev {revision or '(latest approved)'}")
        table.add_column("Name")
        table.add_column("Size", justify="right")
        table.add_column("Checksum")
        for f in files:
            table.add_row(
                str(f.get("filename")), str(f.get("size")), str(f.get("checksum"))
            )
        print(table)
    except requests.HTTPError as e:
        typer.secho(f"Arena request failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(2)
    except ArenaError as e:
        typer.secho(str(e), fg=typer.colors.RED, err=True)
        raise typer.Exit(2)


@app.command("bom")
def bom(
    item: str = typer.Argument(..., help="Item/article number (e.g., 890-1001)"),
    revision: Optional[str] = typer.Option(
        None,
        "--rev",
        help='Revision selector: WORKING, EFFECTIVE (default), or label (e.g., "B2")',
    ),
    output: str = typer.Option(
        "table", "--output", help='Output format: "table" (default) or "json"'
    ),
    recursive: bool = typer.Option(
        False, "--recursive/--no-recursive", help="Recursively expand subassemblies"
    ),
    max_depth: Optional[int] = typer.Option(
        None,
        "--max-depth",
        min=1,
        help="Maximum recursion depth (1 = only children). Omit for unlimited.",
    ),
):
    """List the BOM lines for an item revision."""
    try:
        lines = _client().get_bom(
            item, revision, recursive=recursive, max_depth=max_depth
        )

        if output.lower() == "json":
            print(json.dumps({"count": len(lines), "results": lines}, indent=2))
            return

        title_rev = revision or "(latest approved)"
        table = Table(title=f"BOM for {item} rev {title_rev}")
        table.add_column("Line", justify="right")
        table.add_column("Qty", justify="right")
        table.add_column("Number")
        table.add_column("Name")
        table.add_column("RefDes")

        for ln in lines:
            lvl = int(ln.get("level", 0) or 0)
            indent = "  " * lvl  # 2 spaces per level
            table.add_row(
                str(ln.get("lineNumber") or ""),
                str(ln.get("quantity") or ""),
                str(ln.get("itemNumber") or ""),
                f"{indent}{str(ln.get('itemName') or '')}",
                str(ln.get("refDes") or ""),
            )
        print(table)
    except requests.HTTPError as e:
        typer.secho(f"Arena request failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(2)
    except ArenaError as e:
        typer.secho(str(e), fg=typer.colors.RED, err=True)
        raise typer.Exit(2)


@app.command("get-files")
def get_files(
    item: str = typer.Argument(..., help="Item/article number"),
    revision: Optional[str] = typer.Option(
        None, "--rev", help="Revision (default: latest approved)"
    ),
    out: Optional[Path] = typer.Option(
        None,
        "--out",
        help="Output directory (default: a folder named after the item number)",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive/--no-recursive",
        help="Recursively download files from subassemblies",
    ),
    max_depth: Optional[int] = typer.Option(
        None,
        "--max-depth",
        min=1,
        help="Maximum recursion depth for --recursive (1 = only direct children).",
    ),
):
    try:
        out_dir = out or Path(item)  # article numbers are never files; safe as dir name
        if recursive:
            paths = _client().download_files_recursive(
                item, revision, out_dir=out_dir, max_depth=max_depth
            )
        else:
            paths = _client().download_files(item, revision, out_dir=out_dir)

        for p in paths:
            print(str(p))
    except requests.HTTPError as e:
        typer.secho(f"Arena request failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(2)
    except ArenaError as e:
        typer.secho(str(e), fg=typer.colors.RED, err=True)
        raise typer.Exit(2)


@app.command("upload-file")
def upload_file(
    item: str = typer.Argument(...),
    file: Path = typer.Argument(...),
    reference: Optional[str] = typer.Option(
        None, "--reference", help="Optional reference string"
    ),
    title: Optional[str] = typer.Option(
        None,
        "--title",
        help="Override file title (default: filename without extension)",
    ),
    category: str = typer.Option(
        "CAD Data", "--category", help='File category name (default: "CAD Data")'
    ),
    file_format: Optional[str] = typer.Option(
        None, "--format", help="File format (default: file extension)"
    ),
    description: Optional[str] = typer.Option(
        None, "--desc", help="Optional description"
    ),
    primary: bool = typer.Option(
        False, "--primary/--no-primary", help="Mark association as primary"
    ),
    edition: str = typer.Option(
        "1",
        "--edition",
        help="Edition number when creating a new association (default: 1)",
    ),
):
    """If a file with the same filename exists: update its content (new edition).
    Otherwise: create a new association on the WORKING revision (requires --edition)."""
    try:
        result = _client().upload_file_to_working(
            item,
            file,
            reference,
            title=title,
            category_name=category,
            file_format=file_format,
            description=description,
            primary=primary,
            edition=edition,
        )
        print(json.dumps(result, indent=2))
    except requests.HTTPError as e:
        typer.secho(f"Arena request failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(2)
    except ArenaError as e:
        typer.secho(str(e), fg=typer.colors.RED, err=True)


if __name__ == "__main__":
    app()
