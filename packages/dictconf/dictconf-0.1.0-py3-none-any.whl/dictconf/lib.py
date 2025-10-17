import os
import re
import sys
import yaml
from typing import Any, Dict, List, Optional, Tuple

class ConfigError(Exception):
    pass

class ConfigFileNotFoundError(ConfigError, FileNotFoundError):
    pass

class InvalidOverrideError(ConfigError, ValueError):
    pass

class InterpolationError(ConfigError, KeyError):
    pass

class Config(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, value in self.items():
            if isinstance(value, dict):
                self[key] = Config(value)

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'Config' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any):
        self[name] = value

    def __delattr__(self, name: str):
        try:
            del self[name]
        except KeyError:
            raise AttributeError(f"'Config' object has no attribute '{name}'")

class ConfigLoader:
    _INTERPOLATION_PATTERN = re.compile(r'\$\{(.*?)\}')
    _MAX_INTERPOLATION_DEPTH = 5

    def __init__(self, config_dir: str):
        if not os.path.isdir(config_dir):
            raise ConfigFileNotFoundError(f"Configuration directory not found: {config_dir}")
        self.config_dir = config_dir

    def load(self, main_config_name: str, cli_args: Optional[List[str]] = None) -> Config:
        cli_args = cli_args if cli_args is not None else sys.argv[1:]
        
        main_config_path = os.path.join(self.config_dir, main_config_name)
        main_config_data = self._load_yaml(main_config_path)

        component_swaps, value_overrides_list = self._parse_cli_args(cli_args)
        
        if 'defaults' not in main_config_data:
            return self._process_legacy(main_config_data, value_overrides_list)

        effective_defaults = self._resolve_defaults(main_config_data.get('defaults', []), component_swaps)
        
        merged_config = {}
        for group, name in effective_defaults:
            component_path = os.path.join(self.config_dir, group, f"{name}.yaml")
            component_data = self._load_yaml(component_path)
            self._deep_merge(merged_config, component_data)
        
        main_values = {k: v for k, v in main_config_data.items() if k != 'defaults'}
        self._deep_merge(merged_config, main_values)

        value_overrides = self._parse_value_overrides(value_overrides_list)
        self._deep_merge(merged_config, value_overrides)
        
        resolved_config = self._resolve_interpolations(merged_config)
        
        return Config(resolved_config)

    def _process_legacy(self, base_config: Dict, overrides: List[str]) -> Config:
        cli_config = self._parse_value_overrides(overrides)
        merged_config = self._deep_merge(base_config, cli_config)
        resolved_config = self._resolve_interpolations(merged_config)
        return Config(resolved_config)

    def _load_yaml(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            raise ConfigFileNotFoundError(f"Configuration file not found at: {path}")
        except yaml.YAMLError as e:
            raise ConfigError(f"Error parsing YAML file {path}: {e}")

    @staticmethod
    def _parse_cli_args(cli_args: List[str]) -> Tuple[Dict[str, str], List[str]]:
        component_swaps = {}
        value_overrides = []
        for arg in cli_args:
            if '.' in arg:
                value_overrides.append(arg)
            elif "=" in arg:
                key, value = arg.split('=', 1)
                component_swaps[key] = value
        return component_swaps, value_overrides

    @staticmethod
    def _resolve_defaults(defaults_list: List, swaps: Dict[str, str]) -> List[Tuple[str, str]]:
        effective_defaults = []
        for item in defaults_list:
            if isinstance(item, dict):
                key = list(item.keys())[0]
                name = swaps.pop(key, item[key])
                effective_defaults.append((key, name))
        return effective_defaults

    def _resolve_interpolations(self, config: Dict[str, Any]) -> Dict[str, Any]:
        def _get_nested_value(d: Dict[str, Any], key_path: str) -> Any:
            keys = key_path.split('.')
            value = d
            for key in keys:
                try: value = value[key]
                except (KeyError, TypeError):
                    raise InterpolationError(f"Could not resolve key path for interpolation: '{key_path}'")
            return value

        def _recursive_resolve(node: Any, source: Dict[str, Any]) -> Any:
            if isinstance(node, dict):
                return {k: _recursive_resolve(v, source) for k, v in node.items()}
            if isinstance(node, list):
                return [_recursive_resolve(item, source) for item in node]
            if not isinstance(node, str):
                return node

            matches = list(self._INTERPOLATION_PATTERN.finditer(node))
            if not matches:
                return node

            if len(matches) == 1 and matches[0].group(0) == node:
                key_path = matches[0].group(1)
                return _get_nested_value(source, key_path)
            
            new_val = node
            for match in matches:
                key_path = match.group(1)
                resolved_value = str(_get_nested_value(source, key_path))
                new_val = new_val.replace(match.group(0), resolved_value)
            return new_val

        current_config = config
        for _ in range(self._MAX_INTERPOLATION_DEPTH):
            resolved_config = _recursive_resolve(current_config, current_config)
            
            if resolved_config == current_config:
                import json
                if '${' in json.dumps(resolved_config):
                    raise InterpolationError("Max interpolation depth reached; check for circular references or missing keys.")
                return resolved_config
            
            current_config = resolved_config
        
        raise InterpolationError("Max interpolation depth reached; check for circular references or missing keys.")
    
    @staticmethod
    def _parse_value_overrides(overrides: List[str]) -> Dict[str, Any]:
        config_overrides = {}
        for item in overrides:
            try:
                key_path, value_str = item.split('=', 1)
                
                if value_str.lower() == 'true': typed_value = True
                elif value_str.lower() == 'false': typed_value = False
                elif value_str.lower() == 'null': typed_value = None
                else:
                    try: typed_value = int(value_str)
                    except ValueError:
                        try: typed_value = float(value_str)
                        except ValueError: typed_value = value_str
                
                keys = key_path.split('.')
                current_level = config_overrides
                for key in keys[:-1]:
                    current_level = current_level.setdefault(key, {})
                current_level[keys[-1]] = typed_value

            except ValueError:
                raise InvalidOverrideError(f"Invalid override format: '{item}'. Must be 'key.path=value'.")
        
        return config_overrides

    @staticmethod
    def _deep_merge(base: Dict, override: Dict) -> Dict:
        for key, value in override.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                base[key] = ConfigLoader._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

def load_config(config_path: str, cli_args: Optional[List[str]] = None) -> Config:
    if os.path.isdir(config_path):
        config_dir = config_path
        main_config_name = "config.yaml"
    else:
        config_dir = os.path.dirname(config_path)
        main_config_name = os.path.basename(config_path)

    loader = ConfigLoader(config_dir)
    return loader.load(main_config_name, cli_args)