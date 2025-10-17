import importlib.util
import sys

from ziplime.config.base_algorithm_config import BaseAlgorithmConfig


class AlgorithmFile:

    def __init__(self, algorithm_file: str, algorithm_config_file: str | None = None):
        def noop(*args, **kwargs):
            pass

        with open(algorithm_file, "r") as f:
            self.algorithm_text = f.read()

        module_name = "ziplime.ziplime_algorithm"  # TODO: check if we need to modify this
        spec = importlib.util.spec_from_file_location(module_name, algorithm_file)
        if spec and spec.loader:
            # Create a module based on the spec
            module = importlib.util.module_from_spec(spec)

            # Register the module in sys.modules so it can be found by other modules
            sys.modules[module_name] = module

            # Execute the module in its own namespace
            spec.loader.exec_module(module)
        else:
            raise Exception(f"No module found: {algorithm_file}")

        self.initialize = module.__dict__.get("initialize", noop)
        self.handle_data = module.__dict__.get("handle_data", noop)
        self.before_trading_start = module.__dict__.get("before_trading_start", noop)
        # Optional analyze function, gets called after run
        self.analyze = module.__dict__.get("analyze", noop)
        custom_config_class = None
        for name, obj in module.__dict__.items():
            # Check if it's a class
            if isinstance(obj, type):
                # Check if it's a subclass of base_class but not base_class itself
                if issubclass(obj, BaseAlgorithmConfig) and obj != BaseAlgorithmConfig:
                    custom_config_class = obj
                    break
        if custom_config_class is None:
            custom_config_class = BaseAlgorithmConfig
        if algorithm_file is not None:
            with open(algorithm_config_file, "r") as f:
                config = custom_config_class.model_validate_json(f.read())
        else:
            config = custom_config_class.model_validate({})

        self.config = config
