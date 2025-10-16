#! /usr/bin/env python
# -*- coding: utf-8 -*-
# src/gladiator/config.py
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field

CONFIG_HOME = Path(os.environ.get("GLADIATOR_CONFIG_HOME", Path.home() / ".config" / "gladiator"))
CONFIG_PATH = Path(os.environ.get("GLADIATOR_CONFIG", CONFIG_HOME / "login.json"))

class LoginConfig(BaseModel):
    # Primary connection settings
    base_url: str = Field("https://api.arenasolutions.com/v1", description="Arena REST API base URL")
    verify_tls: bool = True

    # Auth options
    api_key: Optional[str] = None  # not used by Arena v1 but kept for future
    username: Optional[str] = None
    password: Optional[str] = None

    # Session from `/login`
    arena_session_id: Optional[str] = Field(None, alias="arenaSessionId")
    workspace_id: Optional[int] = Field(None, alias="workspaceId")
    workspace_name: Optional[str] = Field(None, alias="workspaceName")
    workspace_request_limit: Optional[int] = Field(None, alias="workspaceRequestLimit")
    reason: Optional[str] = None

    class Config:
        populate_by_name = True


def save_config_raw(data: Dict[str, Any], path: Path = CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    try:
        os.chmod(path, 0o600)
    except PermissionError:
        pass


def save_config(cfg: LoginConfig, path: Path = CONFIG_PATH) -> None:
    save_config_raw(cfg.model_dump(by_alias=True))


def load_config(path: Path = CONFIG_PATH) -> LoginConfig:
    with open(path, "r") as f:
        raw = json.load(f)
    return LoginConfig(**raw)