#!/usr/bin/python
#
# SPDX-License-Identifier: GPL-2.0-only
# (c) 2023 Gerd Hoffmann
#
""" inspect kek updates """
import sys
import struct
import argparse

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import pkcs7, Encoding

from virt.firmware.efi import guids
from virt.firmware.efi import efivar
from virt.firmware.efi import siglist
from virt.firmware.misc import cert_not_valid_before, cert_not_valid_after

# UEFI spec allows pkcs7 signatures being used without the envelope
# which identifies them as pkcs7 signatures.  Most crypto libs will
# not parse them without the envelope though.  So add it if needed.
def wrap_pkcs7(data):
    wrap = bytes([
        0x06, 0x09,
        0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x07, 0x02,
        0xa0, 0x82,
    ])

    if wrap == data [ 4 : 17 ]:
        # envelope is present
        return data

    ret = bytes([ 0x30, 0x82 ])
    ret += (len(data) + 15).to_bytes(length=2, byteorder='big')
    ret += wrap
    ret += len(data).to_bytes(length=2, byteorder='big')
    ret += data
    return ret

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--update', dest = 'update', type = str,
                        help = 'read kek update from FILE', metavar = 'FILE')
    parser.add_argument('--pem', dest = 'pem',
                        action = 'store_true', default = False,
                        help = 'print certificates in PEM format')
    options = parser.parse_args()

    if not options.update:
        print('missing kek update file (try --help)')
        return 1

    print('inspecting ' + options.update)
    with open(options.update, 'rb') as f:
        authdata = f.read()

    # parse struct EFI_TIME + EFI_VARIABLE_AUTHENTICATION_2
    (year, month, day, hour, minute, second, ns, tz, dl) = \
        struct.unpack_from("=HBBBBBxLhBx", authdata)
    print(f'time: {year:04}-{month:02}-{day:02} {hour:02}:{minute:02}:{second:02}')
    (length, revision, certtype) = struct.unpack_from("=LHH", authdata, 16)
    guid = guids.parse_bin(authdata, 24)
    if str(guid) != guids.EfiCertPkcs7:
        raise RuntimeError('no pkcs7 signature')
    cert_data = authdata [ 40 : 16 + length ]
    data = authdata [ 16 + length : ]

    if len(cert_data) == 0:
        print('pkcs7 signature is empty')
    else:
        certs = pkcs7.load_der_pkcs7_certificates(wrap_pkcs7(cert_data))
        print('pkcs7 signature chain certificates')
        for c in certs:
            print('  certificate')
            print('    fingerprint: ' + c.fingerprint(hashes.SHA256()).hex(':'))
            print('    subject    : ' + c.subject.rfc4514_string())
            print('    issuer     : ' + c.issuer.rfc4514_string())
            print('    valid from : ' + str(cert_not_valid_before(c)))
            print('    valid to   : ' + str(cert_not_valid_after(c)))
            if options.pem:
                print(c.public_bytes(Encoding.PEM).decode())

    sigdb = siglist.EfiSigDB(data)
    print('signature database')
    for slist in sigdb:
        efivar.EfiVarList.print_siglist(slist)

    return 0

if __name__ == '__main__':
    sys.exit(main())
