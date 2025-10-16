import importlib
import pkgutil
import sys
import pathlib
import tomllib
from typing import Any, Dict

from zenx.spiders import Spider


def load_config() -> Dict[str, Any] | None:
    current_dir = pathlib.Path.cwd()
    config_path = current_dir / "zenx.toml"
    if config_path.exists():
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
            return config


def discover_local_module(module_name: str):
    config = load_config()
    if not config:
        return
    project_root = pathlib.Path.cwd()
    project_name: str | Any = config.get("project")
    module_dir = project_root / project_name / module_name
    
    if not module_dir.is_dir():
        return

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    try:
        module = importlib.import_module(f"{project_name}.{module_name}")
        for _,name,_ in pkgutil.iter_modules(module.__path__):
            importlib.import_module(f".{name}", module.__name__)
    except ImportError:
        pass


def load_spider_from_file(file_path: pathlib.Path) -> str:
    """
    Loads a spider from a file and returns its name.
    """
    parent_dir = str(file_path.parent.resolve())
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    module_name = file_path.stem
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if not spec or not spec.loader:
        raise ImportError(f"Could not load spider from {file_path}")

    module = importlib.util.module_from_spec(spec)
    
    sys.modules[module_name] = module

    before_spiders = set(Spider.spider_list())
    spec.loader.exec_module(module)
    after_spiders = set(Spider.spider_list())

    new_spiders = after_spiders - before_spiders
    if not new_spiders:
        raise ImportError(f"No spider found in {file_path}. Make sure it's a subclass of zenx.spiders.Spider and has a 'name' attribute.")
    
    return list(new_spiders)[0]

