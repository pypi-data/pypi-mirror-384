#!/usr/bin/python
#
# parse json dbx from
#   https://github.com/microsoft/secureboot_objects/tree/main/PreSignedObjects/DBX
#
""" parse json dbx """
import sys
import json
import logging
import argparse

from virt.firmware.efi import guids
from virt.firmware.efi import efivar
from virt.firmware.efi import siglist

from virt.firmware.varstore import jstore

def hash_siglist(hashes):
    sl = siglist.EfiSigList(guid = guids.parse_str(guids.EfiCertSha256))
    guid = guids.parse_str(guids.MicrosoftVendor)
    for h in hashes:
        sl.add_sig(guid, bytes.fromhex(h.get('authenticodeHash')))
    sdb = siglist.EfiSigDB()
    sdb.append(sl)
    return sdb

def svns_siglist(svns):
    sl = siglist.EfiSigList(guid = guids.parse_str(guids.EfiCertSha256))
    guid = guids.parse_str(guids.MicrosoftVendor)
    for s in svns:
        sl.add_sig(guid, bytes.fromhex(s.get('value')))
    sdb = siglist.EfiSigDB()
    sdb.append(sl)
    return sdb

def cert_sigdb(certificates):
    for cert in certificates:
        # 'value' has a filename, that does not exist though
        cn = cert.get('subjectName')
        print(f'# cert    : "{cn}"  [NOT HANDLED]')
        logging.debug('certificate record: %s', cert)

def main():
    parser = argparse.ArgumentParser(
        description = "parse json dbx")
    parser.add_argument('-l', '--loglevel', dest = 'loglevel', type = str, default = 'info',
                        help = 'set loglevel to LEVEL', metavar = 'LEVEL')
    parser.add_argument('-i', '--input', dest = 'input', type = str,
                        help = 'read dbx revocation list from FILE', metavar = 'FILE')
    parser.add_argument('--print-varstore', dest = 'print_varstore',
                        action = 'store_true', default = False,
                        help = 'print varstore')
    parser.add_argument('--write-varstore', dest = 'write_varstore',
                        action = 'store_true', default = False,
                        help = 'write varstore (for "virt-fw-vars --set-json $file")')

    options = parser.parse_args()
    logging.basicConfig(format = '%(levelname)s: %(message)s',
                        level = getattr(logging, options.loglevel.upper()))

    with open(options.input, "r", encoding = 'utf-8') as f:
        dbx = json.loads(f.read())

    # debug
    logging.debug('toplevel keys: %s', dbx.keys())

    # handle image hashes
    hash_sdb = {}
    for (arch, data) in dbx.get('images').items():
        hash_sdb[arch] = hash_siglist(data)
        print(f'# {arch:8}: {len(hash_sdb[arch][0]):4} entries')

    # handle SVNs
    svns = dbx.get('svns')
    if svns:
        svns_sdb = svns_siglist(svns)
        print(f'# svns    : {len(svns_sdb[0]):4} entries')

    # handle certificates [TODO]
    certificates = dbx.get('certificates')
    if certificates:
        cert_sigdb(certificates)

    # write out as json varstore (usable via 'virt-fw-vars --set-json $file')
    for (arch, sdb) in hash_sdb.items():
        sdb.merge(svns_sdb)
        v = efivar.EfiVar('dbx', data = bytes(sdb))
        varlist = efivar.EfiVarList()
        varlist['dbx'] = v
        filename = f'dbx-{arch}.json'
        if options.write_varstore:
            jstore.JsonVarStore.write_varstore(filename, varlist)
        if options.print_varstore:
            varlist.print_normal()

if __name__ == '__main__':
    sys.exit(main())
