#!/usr/bin/python
# promoted out of experimental
""" compat wrapper for virt-fw-measure """
import sys
from virt.firmware.measure import main

if __name__ == '__main__':
    sys.exit(main())
