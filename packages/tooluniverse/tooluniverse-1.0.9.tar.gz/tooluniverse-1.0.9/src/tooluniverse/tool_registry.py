"""Simplified tool registry for automatic tool discovery and registration."""

import importlib
import pkgutil
import os
import json
import glob
import logging
import re
from typing import Dict, Optional

# Initialize logger for this module
logger = logging.getLogger("ToolRegistry")

# Global registries
_tool_registry = {}
_config_registry = {}
_lazy_registry: Dict[str, str] = {}  # Maps tool names to module names
_discovery_completed = False
_lazy_cache = {}

# Global error tracking
_TOOL_ERRORS = {}


def _extract_missing_package(error_msg: str) -> Optional[str]:
    """Extract package name from ImportError."""
    match = re.search(r"No module named ['\"]([^'\"]+)['\"]", error_msg)
    if match:
        return match.group(1).split(".")[0]
    return None


def mark_tool_unavailable(tool_name: str, error: Exception, module: str = None):
    """Record tool failure."""
    _TOOL_ERRORS[tool_name] = {
        "error": str(error),
        "error_type": type(error).__name__,
        "module": module,
        "missing_package": _extract_missing_package(str(error)),
    }


def get_tool_errors() -> dict:
    """Get all tool errors."""
    return _TOOL_ERRORS.copy()


def register_tool(tool_type_name=None, config=None):
    """
    Decorator to automatically register tool classes and their configs.

    Usage:
        @register_tool('CustomToolName', config={...})
        class MyTool:
            pass
    """

    def decorator(cls):
        name = tool_type_name or cls.__name__
        _tool_registry[name] = cls

        if config:
            _config_registry[name] = config
            logger.info(f"Registered tool with config: {name}")
        else:
            logger.debug(f"Registered tool: {name} -> {cls.__name__}")

        return cls

    return decorator


def register_external_tool(tool_name, tool_class):
    """Allow external registration of tool classes."""
    _tool_registry[tool_name] = tool_class
    logger.info(f"Externally registered tool: {tool_name}")


def register_config(tool_type_name, config):
    """Register a config for a tool type."""
    _config_registry[tool_type_name] = config
    logger.info(f"Registered config for: {tool_type_name}")


def get_tool_registry():
    """Get a copy of the current tool registry."""
    return _tool_registry.copy()


def get_config_registry():
    """Get a copy of the current config registry."""
    return _config_registry.copy()


def lazy_import_tool(tool_name):
    """
    Lazily import a tool by name without importing all tool modules.
    Only imports the specific module containing the requested tool.
    """
    global _tool_registry, _lazy_registry, _lazy_cache  # noqa: F824

    # If tool is already in registry, return it
    if tool_name in _tool_registry:
        return _tool_registry[tool_name]

    # If we have a lazy mapping for this tool, import its module
    if tool_name in _lazy_registry:
        module_name = _lazy_registry[tool_name]

        # Ensure we have the full module path
        if not module_name.startswith("tooluniverse."):
            full_module_name = f"tooluniverse.{module_name}"
        else:
            full_module_name = module_name

        # Only import if we haven't cached this module yet
        if full_module_name not in _lazy_cache:
            try:
                logger.debug(
                    f"Lazy importing module: {full_module_name} for tool: {tool_name}"
                )
                module = importlib.import_module(full_module_name)
                _lazy_cache[full_module_name] = module
                logger.debug(f"Successfully imported module: {full_module_name}")

                # Check if the tool is now in the registry
                if tool_name in _tool_registry:
                    logger.debug(f"Successfully lazy-loaded tool: {tool_name}")
                    return _tool_registry[tool_name]
                else:
                    logger.warning(
                        f"Tool {tool_name} not found in module {full_module_name} after import"
                    )

            except ImportError as e:
                logger.warning(f"Failed to lazy import {full_module_name}: {e}")
                mark_tool_unavailable(tool_name, e, full_module_name)
                # Remove this bad mapping so we don't try again
                del _lazy_registry[tool_name]
            except Exception as e:
                logger.warning(f"Failed to load {full_module_name}: {e}")
                mark_tool_unavailable(tool_name, e, full_module_name)
                del _lazy_registry[tool_name]
        else:
            # Module was already imported, check if tool is now available
            if tool_name in _tool_registry:
                return _tool_registry[tool_name]
            else:
                logger.warning(
                    f"Tool {tool_name} not found in already imported module {full_module_name}"
                )

    # If still not found after lazy loading attempt, return None
    # Don't fall back to full discovery as that defeats the purpose of lazy loading
    logger.debug(f"Tool {tool_name} not found in lazy registry")
    return None


def build_lazy_registry(package_name=None):
    """
    Build a mapping of tool names to module names using config files and naming patterns.
    This is truly lazy - it doesn't import any modules, just creates the mapping.
    """
    global _lazy_registry  # noqa: F824

    if package_name is None:
        package_name = "tooluniverse"

    try:
        package = importlib.import_module(package_name)
        package_path = package.__path__
    except (ImportError, AttributeError):
        logger.warning(f"Could not import package {package_name}")
        return {}

    logger.debug(f"Building lazy registry for package: {package_name}")

    # Strategy 1: Parse config files for accurate mappings WITHOUT importing modules
    config_mappings = _discover_from_configs()
    config_count = 0

    for module_name, tool_classes in config_mappings.items():
        # Don't verify module exists by importing - just trust the mapping
        # The actual import will happen when the tool is first requested
        for tool_class in tool_classes:
            if tool_class not in _lazy_registry:
                _lazy_registry[tool_class] = module_name
        config_count += len(tool_classes)

    # Strategy 2: Pattern-based fallback for modules without configs
    pattern_count = 0
    for _importer, modname, _ispkg in pkgutil.iter_modules(package_path):
        if "_tool" in modname and modname not in [m for m in config_mappings.keys()]:
            # Simple pattern: module_tool -> ModuleTool, ModuleRESTTool
            base_name = modname.replace("_tool", "").replace("_", "")
            potential_names = [
                f"{base_name.title()}Tool",
                f"{base_name.title()}RESTTool",
                f"{base_name.upper()}Tool",
            ]

            for tool_name in potential_names:
                if tool_name not in _lazy_registry:
                    _lazy_registry[tool_name] = modname
                    pattern_count += 1

    logger.info(
        f"Built lazy registry: {config_count} from configs, {pattern_count} from patterns (no modules imported)"
    )
    return _lazy_registry.copy()


def _discover_from_configs():
    """
    Fully dynamic config file discovery - no hardcoded mappings.
    Automatically discovers config-to-module mappings by:
    1. Finding all JSON config files
    2. Finding all Python tool modules
    3. Smart matching between config names and module names
    """
    # Get the data directory path relative to tooluniverse module
    try:
        import tooluniverse

        package_dir = os.path.dirname(tooluniverse.__file__)
        data_dir = os.path.join(package_dir, "data")
    except ImportError:
        # Fallback: assume we're in the right directory structure
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, "data")

    if not os.path.exists(data_dir):
        logger.warning(f"Data directory not found: {data_dir}")
        return {}

    # Step 1: Get all available tool modules
    available_modules = _get_available_tool_modules()
    logger.debug(f"Found {len(available_modules)} tool modules: {available_modules}")

    tool_mapping = {}

    try:
        for json_file in glob.glob(os.path.join(data_dir, "*.json")):
            try:
                config_name = os.path.basename(json_file).replace(".json", "")

                # Step 2: Smart matching to find the best module for this config
                module_name = _smart_match_config_to_module(
                    config_name, available_modules
                )

                if not module_name:
                    logger.debug(f"No module match found for config: {config_name}")
                    continue

                # Step 3: Extract tool types from config
                with open(json_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)

                tool_types = set()
                if isinstance(config_data, list):
                    for tool_config in config_data:
                        if isinstance(tool_config, dict) and "type" in tool_config:
                            tool_types.add(tool_config["type"])
                elif isinstance(config_data, dict) and "type" in config_data:
                    tool_types.add(config_data["type"])

                if tool_types and module_name:
                    if module_name not in tool_mapping:
                        tool_mapping[module_name] = []
                    tool_mapping[module_name].extend(list(tool_types))
                    logger.debug(
                        f"Dynamic mapping: {config_name} -> {module_name} -> {tool_types}"
                    )

            except Exception as e:
                logger.debug(f"Skipped config file {json_file}: {e}")
                continue
    except Exception as e:
        logger.warning(f"Error reading config files: {e}")

    logger.debug(f"Dynamically discovered {len(tool_mapping)} modules from configs")
    return tool_mapping


def _get_available_tool_modules():
    """
    Get all available tool modules by scanning the tooluniverse package.
    """
    try:
        import tooluniverse

        package_path = tooluniverse.__path__
    except ImportError:
        logger.warning("Cannot import tooluniverse package")
        return []

    modules = []
    for _importer, modname, _ispkg in pkgutil.iter_modules(package_path):
        if "_tool" in modname or modname in [
            "compose_tool",
            "agentic_tool",
        ]:  # Include compose_tool and agentic_tool
            modules.append(modname)

    return modules


def _smart_match_config_to_module(config_name, available_modules):
    """
    Smart matching algorithm to find the best module for a config file.
    Uses multiple strategies in order of preference.
    """
    # Strategy 1: Direct name matching
    # "chembl_tools" -> "chem_tool"
    if config_name.endswith("_tools"):
        candidate = config_name.replace("_tools", "_tool")
        if candidate in available_modules:
            return candidate

    # Strategy 2: Exact match
    # "chem_tool" -> "chem_tool"
    if config_name in available_modules:
        return config_name

    # Strategy 3: Fuzzy matching based on keywords
    # Extract key parts from config name and match with modules
    config_parts = set(config_name.replace("_", " ").split())

    best_match = None
    best_score = 0

    for module in available_modules:
        module_parts = set(module.replace("_", " ").split())

        # Calculate similarity score
        common_parts = config_parts & module_parts
        if common_parts:
            score = len(common_parts) / max(len(config_parts), len(module_parts))
            if score > best_score:
                best_score = score
                best_match = module

    # Only return match if score is reasonably high
    if best_score > 0.3:  # At least 30% similarity
        return best_match

    # Strategy 4: Pattern-based matching for known patterns
    patterns = [
        # FDA patterns
        ("fda", "openfda_tool"),
        ("clinicaltrials", "ctg_tool"),
        ("clinical_trials", "ctg_tool"),
        ("opentargets", "graphql_tool"),
        ("monarch", "restful_tool"),
        ("url_fetch", "url_tool"),
        ("europe_pmc", "europe_pmc_tool"),
        ("semantic_scholar", "semantic_scholar_tool"),
        # ChEMBL pattern
        ("chembl", "chem_tool"),
    ]

    for pattern, module in patterns:
        if pattern in config_name and module in available_modules:
            return module

    return None


def auto_discover_tools(package_name=None, lazy=True):
    """
    Automatically discover and import all tool modules.
    If lazy=True, only builds the mapping without importing any modules.
    If lazy=False, imports all tool modules immediately.
    """
    global _discovery_completed

    if package_name is None:
        package_name = "tooluniverse"

    # In lazy mode, just build the registry without importing anything
    if lazy:
        if not _lazy_registry:
            build_lazy_registry(package_name)
            logger.debug(
                f"Lazy discovery complete. Registry contains {len(_lazy_registry)} tool mappings (no modules imported)"
            )
        return _tool_registry.copy()

    # Return cached registry if full discovery already done
    if _discovery_completed:
        return _tool_registry.copy()

    try:
        package = importlib.import_module(package_name)
        package_path = package.__path__
    except (ImportError, AttributeError):
        logger.warning(f"Could not import package {package_name}")
        return _tool_registry.copy()

    logger.info(
        f"Auto-discovering tools in package: {package_name} (lazy={lazy}) - importing ALL modules"
    )

    # Import all tool modules (non-lazy mode)
    imported_count = 0
    for _importer, modname, _ispkg in pkgutil.iter_modules(package_path):
        if "_tool" in modname or modname in ["compose_tool", "agentic_tool"]:
            try:
                importlib.import_module(f"{package_name}.{modname}")
                logger.debug(f"Imported tool module: {modname}")
                imported_count += 1
            except ImportError as e:
                logger.warning(f"Could not import {modname}: {e}")

    _discovery_completed = True
    logger.info(
        f"Full discovery complete. Imported {imported_count} modules, registered {len(_tool_registry)} tools"
    )
    return _tool_registry.copy()


def get_tool_class_lazy(tool_name):
    """
    Get a tool class by name, using lazy loading if possible.
    Only imports the specific module needed, not all modules.
    """
    # First try lazy import
    tool_class = lazy_import_tool(tool_name)
    if tool_class:
        return tool_class

    # If lazy loading fails and we haven't done full discovery yet,
    # check if the tool exists in the current registry
    if tool_name in _tool_registry:
        return _tool_registry[tool_name]

    # As a last resort, if full discovery hasn't been done, do it
    # But this should be rare with a properly configured lazy registry
    if not _discovery_completed:
        logger.warning(
            f"Tool {tool_name} not found in lazy registry, falling back to full discovery"
        )
        auto_discover_tools(lazy=False)
        return _tool_registry.get(tool_name)

    return None
