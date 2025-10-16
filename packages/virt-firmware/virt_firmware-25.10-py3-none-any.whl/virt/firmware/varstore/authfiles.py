#!/usr/bin/python
#
# SPDX-License-Identifier: GPL-2.0-only
# (c) 2024 Gerd Hoffmann
#
""" secure boot databases in *.auth files """
import os
import struct
import logging

from virt.firmware.efi import guids
from virt.firmware.efi import ucs16
from virt.firmware.efi import efivar

SECUREBOOT_DATABASE_NAMES = ('PK', 'KEK', 'db', 'dbx')

class AuthFilesVarStore:
    """ secure boot databases in *.auth files """

    def __init__(self, dirname = None):
        self.dirname = dirname
        self.varlist = efivar.EfiVarList()
        if self.dirname:
            self.read_files()

    @staticmethod
    def probe(dirname):
        if not os.path.isdir(dirname):
            return False
        if not os.path.isfile(f'{dirname}/PK.auth'):
            return False
        return True

    def read_files(self):
        logging.info('reading secureboot db varstore from %s', self.dirname)
        for name in SECUREBOOT_DATABASE_NAMES:
            filename = f'{self.dirname}/{name}.auth'
            if not os.path.exists(filename):
                continue
            logging.info('reading %s', filename)
            with open(filename, "rb") as f:
                blob = f.read()
            var = efivar.EfiVar(ucs16.from_string(name),
                                authdata = blob)
            self.varlist[name] = var

    def get_varlist(self):
        return self.varlist

    @staticmethod
    def empty_auth_header():
        """ EFI_VARIABLE_AUTHENTICATION_2 """
        length    = 24
        revision  = 0x0200
        certtype  = 0x0EF1  # WIN_CERT_TYPE_EFI_GUID
        pkcs7guid = guids.parse_str(guids.EfiCertPkcs7)
        blob      = b''
        blob     += struct.pack("=LHH", length, revision, certtype)
        blob     += pkcs7guid.bytes_le
        return blob

    @staticmethod
    def write_varstore(dirname, varlist):
        logging.info('writing secureboot db varstore to %s', dirname)
        if not os.path.exists(dirname):
            os.mkdir(dirname)
        if not os.path.isdir(dirname):
            raise RuntimeError(f'{dirname} exists but is not a directory')
        dummy_header = AuthFilesVarStore.empty_auth_header()
        for name in SECUREBOOT_DATABASE_NAMES:
            var = varlist.get(name)
            if var is None:
                continue
            filename = f'{dirname}/{name}.auth'
            logging.info('writing %s', filename)
            with open(filename, "wb") as f:
                f.write(var.bytes_time())
                f.write(dummy_header)
                f.write(var.data)
