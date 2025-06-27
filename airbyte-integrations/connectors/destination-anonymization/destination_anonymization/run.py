import sys
from .destination import DestinationAnonymization


def run():
    """Entry point for the destination connector."""
    DestinationAnonymization().run(sys.argv[1:])


if __name__ == "__main__":
    run()
