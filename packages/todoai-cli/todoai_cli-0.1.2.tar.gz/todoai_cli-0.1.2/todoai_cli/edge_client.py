import sys
from typing import Optional

from todoforai_edge.edge import TODOforAIEdge
from todoforai_edge.config import Config


async def init_edge(cli_api_url: Optional[str], saved_default_api_url: Optional[str], saved_default_api_key: Optional[str]) -> TODOforAIEdge:
    """
    Build and validate the Edge client using URL priority:
      1) cli_api_url (argument)
      2) saved_default_api_url (from CLI config)
      3) env via Config()
      4) Config default
    
    And API key priority:
      1) saved_default_api_key (from CLI config)
      2) env via Config()
    """
    cfg = Config()
    
    # URL priority: CLI arg > saved config > env > default
    if cli_api_url:
        cfg.api_url = cli_api_url
    elif saved_default_api_url:
        cfg.api_url = saved_default_api_url
    # else: keep env/default from Config()
    
    # API key priority: saved config > env
    key_source = None
    if saved_default_api_key:
        cfg.api_key = saved_default_api_key
        key_source = "saved-config"
    elif cfg.api_key:
        key_source = "env"
    
    if not cfg.api_key:
        print("❌ Please set TODOFORAI_API_KEY (or TODO4AI_API_KEY) environment variable", file=sys.stderr)
        print("   Or use: todoai_cli --set-default-api-key YOUR_API_KEY", file=sys.stderr)
        sys.exit(1)
    
    edge = TODOforAIEdge(cfg)
    result = await edge.validate_api_key()
    if not result.get("valid"):
        err = result.get("error", "Unknown error")
        print(f"❌ API key validation failed: {err}", file=sys.stderr)
        sys.exit(1)
    return edge