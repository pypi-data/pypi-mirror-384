from gladiator.config import LoginConfig
from gladiator.arena import ArenaClient

def test_client_instantiates():
    cfg = LoginConfig(arena_subdomain="dummy", api_key="x")
    ArenaClient(cfg)
