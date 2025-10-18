import argparse
import logging
from pathlib import Path
from typing import Callable


_logger = logging.getLogger(__name__)


class StandardCLI(object):
    """
    Command-Line Interface (CLI) wrapper for customizable argument parsing.

    Simplifies the creation and usage of the DataLinks CLI by allowing to
    pass a custom callback function for additional arguments specific to an
    application. It provides a standard set of CLI arguments while enabling
    customization through user-defined groups.

    :ivar name: The name of the CLI program.
    :type name: str
    :ivar description: The description of the CLI program.
    :type description: str
    """
    def __init__(self, name="datalinks-client", description="Infer and link your data!"):
        self.name = name
        self.description = description

    def __call__(self, f) -> Callable[...,argparse.Namespace]:
        def wrapped_f() -> argparse.Namespace:
            parser = argparse.ArgumentParser(
                prog=self.name,
                description=self.description
            )
            parser.add_argument('input_data', type=Path, default="./data/",
                                help="Where to find the input data.")
            parser.add_argument('-o', '--output-folder', type=Path, default="./data-backup/",
                                help="Where to store the pickled data backup.")
            parser.add_argument('-v', '--verbose', action='store_true')

            group = parser.add_argument_group('API', "Customize the DataLinks behaviour.")
            group.add_argument('-e', '--use-embeddings', action='store_true')
            group.add_argument('-c', '--create-space', action='store_true')
            group.add_argument('-cn', '--config-normalise', type=Path, default="./config/targetCols.toml",
                                 help="Where to find the normalisation configuration.")
            group.add_argument('-bs', '--batch-size', type=int, default=0,
                            help="Limit the number of notices in each batch.")

            custom_group = parser.add_argument_group(self.name, self.description)
            # Add custom arguments to the parser
            f(custom_group)
            args = parser.parse_args()
            for arg in vars(args):
                _logger.debug("CLI arguments loaded")
                _logger.debug(f"{arg}: {getattr(args, arg)}")

            return args
        return wrapped_f


@StandardCLI()
def get_default_args(*args):
    """
    Decorator used to provide the standard DataLinks CLI.

    Usage example:
    @datalinks.cli.StandardCLI(name="Custom CLI name", description="Customized ingestion.")
    def custom_args(args_group):
        args_group.add_argument(...)

    :ivar name: The name that will be used for the custom args group.
    :type name: str
    :ivar description: The description that will be used for the custom args group.
    :type description: str
    """
    pass
