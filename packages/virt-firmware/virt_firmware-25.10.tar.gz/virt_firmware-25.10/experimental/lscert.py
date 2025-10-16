#!/usr/bin/python
#
# SPDX-License-Identifier: GPL-2.0-only
# (c) 2023 Gerd Hoffmann
#
""" list certificates """
import os
import sys
import glob
import argparse

from cryptography import x509
from cryptography.hazmat.backends import default_backend

from virt.firmware.misc import cert_not_valid_before, cert_not_valid_after

attr_override = {
    x509.NameOID.EMAIL_ADDRESS : 'email'
}

def ls_files(flist, verbose, basename = False):
    plen = 0
    for filename in flist:
        pname = filename
        if basename:
            pname = '  ' + os.path.basename(pname)
        plen = max(plen, len(pname))

    for filename in flist:
        # read filename
        with open(filename, 'rb') as f:
            blob = f.read()
        if b'-----BEGIN' in blob:
            cert = x509.load_pem_x509_certificate(blob, default_backend())
        else:
            cert = x509.load_der_x509_certificate(blob, default_backend())

        pname = filename
        if basename:
            pname = '  ' + os.path.basename(pname)

        if verbose:
            # verbose
            name = cert.subject.rfc4514_string(attr_override)
            ds = str(cert_not_valid_before(cert)).split()[0]
            de = str(cert_not_valid_after(cert)).split()[0]
            print(f'{pname:{plen}s}: {ds} - {de}  {name}')

        else:
            # compact
            cn = cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0]
            ys = cert_not_valid_before(cert).year
            ye = cert_not_valid_after(cert).year
            print(f'{pname:{plen}s}: {ys} - {ye}  {cn.value}')

def ls_dirs(dlist, verbose):
    for item in dlist:
        flist = glob.glob(f'{item}/*')
        if len(flist) > 0:
            print(f'{item}:')
            ls_files(flist, verbose, basename = True)

def main():
    parser = argparse.ArgumentParser(
        description = 'list certificates')
    parser.add_argument('-v', '--verbose', dest = 'verbose',
                        action = 'store_true', default = False,
                        help = 'print more certificate details')
    parser.add_argument("FILES", nargs='*',
                        help="List of PE files to dump")
    options = parser.parse_args()

    flist = []
    dlist = []

    for item in options.FILES:
        if os.path.isfile(item):
            flist += (item,)
        elif os.path.isdir(item):
            dlist += (item,)

    if len(flist) > 0:
        ls_files(flist, options.verbose)
    if len(dlist) > 0:
        ls_dirs(dlist, options.verbose)

if __name__ == '__main__':
    sys.exit(main())
