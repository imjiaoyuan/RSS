import importlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_routes():
    routes = {}
    route_dir = Path(__file__).parent

    for f in sorted(route_dir.glob("*.py")):
        if f.name.startswith("_"):
            continue
        name = f.stem
        try:
            mod = importlib.import_module(f"routes.{name}")
            if hasattr(mod, "ROUTE_CONFIG") and hasattr(mod, "fetch"):
                routes[name] = {
                    "config": mod.ROUTE_CONFIG,
                    "fetch": mod.fetch,
                }
                logger.info(f"Loaded custom route: {name}")
        except Exception as e:
            logger.error(f"Failed to load custom route {name}: {e}")

    return routes
