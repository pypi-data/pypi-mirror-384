#!/usr/bin/python
#
# SPDX-License-Identifier: GPL-2.0-only
# (c) 2023 Gerd Hoffmann
#
""" efi signature list encoder/decoder """

import os
import struct
import hashlib
import logging
import collections

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from virt.firmware.efi import guids
from virt.firmware.misc import cert_not_valid_before

class EfiSigList(collections.UserList):
    """  efi signature list """

    def __init__(self, data = None, guid = None, header = None):
        super().__init__()
        self.guid    = guids.parse_str(guids.NotValid)
        self.header  = b''
        self.sigsize = None
        self.x509    = None
        if data:
            self.parse_bin(data)
        elif guid:
            self.guid = guids.parse_auto(guid)
            if header:
                self.header = header

    def parse_bin(self, data):
        self.guid = guids.parse_bin(data, 0)
        (lsize, hsize, ssize) = struct.unpack_from("=LLL", data, 16)
        self.header = data[ 16 + 12 :
                            16 + 12 + hsize ]
        pos = 16 + 12 + hsize
        while pos < lsize:
            self.add_sig(guids.parse_bin(data, pos),
                         data[ pos + 16 : pos + ssize ])
            pos += ssize

    def add_sig(self, guid, data):
        if self.sigsize is None:
            self.sigsize = 16 + len(data)
        if self.sigsize != 16 + len(data):
            raise ValueError('incorrect signature size')
        if str(self.guid) == guids.EfiCertX509:
            if len(self):
                raise RuntimeError('x509 signature list not empty')
            if self.x509 is None:
                try:
                    self.x509 = x509.load_der_x509_certificate(data, default_backend())
                except ValueError:
                    logging.error("x509: failed to load certificate")
                    self.x509 = None
        sig = { 'guid' : guids.parse_auto(guid),
                'data' : data }
        self.append(sig)

    def add_cert(self, guid, filename):
        if str(self.guid) != guids.EfiCertX509:
            raise RuntimeError('incorrect siglist type guid')
        if len(self):
            raise RuntimeError('x509 signature list not empty')
        with open(filename, "rb") as f:
            pem = f.read()
        if b'-----BEGIN' in pem:
            self.x509 = x509.load_pem_x509_certificate(pem, default_backend())
        else:
            self.x509 = x509.load_der_x509_certificate(pem, default_backend())
        data = self.x509.public_bytes(serialization.Encoding.DER)
        self.add_sig(guid, data)

    def extract_cert(self, prefix = None):
        if self.x509 is None:
            return
        names = self.x509.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)
        if len(names) > 0:
            name = names[0].value
        else:
            name = hashlib.sha256(
                self.x509.public_bytes(
                    serialization.Encoding.DER)).digest().hex()

        filename = ""
        if prefix:
            filename += prefix + '-'
        filename += str(self[0]['guid']) + '-'
        filename += "".join(x for x in name if x.isalnum())
        filename += ".pem"
        if os.path.exists(filename):
            logging.info('exists: %s, skipping', filename)
            return
        logging.info('writing: %s', filename)
        with open(filename, "wb") as f:
            f.write(self.x509.public_bytes(serialization.Encoding.PEM))

    def size(self):
        if not self.sigsize:
            raise RuntimeError('signature list is empty')
        return (16 + 12 + len(self.header) +
                self.sigsize * len(self))

    def __bytes__(self):
        blob = b''
        blob += self.guid.bytes_le
        blob += struct.pack("=LLL",
                            self.size(),
                            len(self.header),
                            self.sigsize)
        blob += self.header
        for sig in list(self):
            blob += sig.get('guid').bytes_le
            blob += sig.get('data')
        return blob


class EfiSigDB(collections.UserList):
    """  efi signature database """

    def __init__(self, data = b''):
        super().__init__()
        pos = 0
        while pos < len(data):
            siglist = EfiSigList(data = data[pos:])
            self.append(siglist)
            pos += siglist.size()

    def has_cert(self, siglist):
        for item in list(self):
            if item.x509 == siglist.x509:
                logging.info('certificate already present, skipping')
                return True
        return False

    def add_cert(self, guid, filename):
        siglist = EfiSigList(guid = guids.parse_str(guids.EfiCertX509))
        siglist.add_cert(guid, filename)
        if not self.has_cert(siglist):
            self.append(siglist)

    def has_sig(self, sigtype, sigdata):
        for siglist in list(self):
            if str(siglist.guid) == sigtype:
                for item in list(siglist):
                    if item['data'] == sigdata:
                        return True
        return False

    def get_siglist(self, sigtype):
        for siglist in list(self):
            if str(siglist.guid) == sigtype:
                return siglist
        siglist = EfiSigList(guid = guids.parse_str(sigtype))
        self.append(siglist)
        return siglist

    def add_hash(self, guid, data):
        if len(data) != 32:
            raise ValueError('incorrect hash data size')
        if self.has_sig(guids.EfiCertSha256, data):
            logging.info('hash already present, skipping')
            return
        siglist = self.get_siglist(guids.EfiCertSha256)
        siglist.add_sig(guid, data)

    def add_dummy(self, guid):
        siglist = EfiSigList(guid = guids.parse_str(guids.EfiCertSha256))
        siglist.add_sig(guid, hashlib.sha256(b'').digest())
        self.append(siglist)

    def add_external_mgmt(self, guid):
        data = b'\0'
        if not self.has_sig(guids.EfiCertExternalMgmt, data):
            siglist = self.get_siglist(guids.EfiCertExternalMgmt)
            siglist.add_sig(guid, data)

    def merge(self, mdb):
        for siglist in list(mdb):
            if str(siglist.guid) == guids.EfiCertSha256:
                for item in list(siglist):
                    self.add_hash(item['guid'], item['data'])
            if str(siglist.guid) == guids.EfiCertX509:
                if not self.has_cert(siglist):
                    self.append(siglist)

    def extract_certs(self, prefix = None):
        for siglist in list(self):
            siglist.extract_cert(prefix)

    def get_cert_ts(self):
        ts = None
        for siglist in list(self):
            if siglist.x509:
                if ts is None or ts < cert_not_valid_before(siglist.x509):
                    ts = cert_not_valid_before(siglist.x509)
        return ts

    def size(self):
        size = 0
        for siglist in list(self):
            size += siglist.size()
        return size

    def __bytes__(self):
        blob = b''
        for siglist in list(self):
            blob += bytes(siglist)
        return blob
