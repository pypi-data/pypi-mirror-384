from rushclis import RushCli

from ilbuilder_cli.add import add
from ilbuilder.version import __version__


class Cli(RushCli):
    def __init__(self):
        super().__init__("ilbuilder", __version__)

        add(self)
