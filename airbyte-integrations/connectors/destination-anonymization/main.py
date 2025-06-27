#
#

import sys

from destination_anonymization import DestinationAnonymization


if __name__ == "__main__":
    DestinationAnonymization().run(sys.argv[1:])
