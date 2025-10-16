#!/usr/bin/python
#
# SPDX-License-Identifier: GPL-2.0-only
# (c) 2023 Gerd Hoffmann
#
""" misc utility functions """
import array
import datetime

# python crc32c implementation
poly = 0x82F63B78
table = array.array('L')

for byte in range(256):
    crc = 0
    for bit in range(8):
        if (byte ^ crc) & 1:
            crc = (crc >> 1) ^ poly
        else:
            crc >>= 1
        byte >>= 1
    table.append(crc)

def crc32c(blob):
    value = 0xffffffff
    for b in blob:
        value = table[(int(b) ^ value) & 0xff] ^ (value >> 8)
    return 0xffffffff - value

def cert_not_valid_before(cert):
    try:
        # cryptography 42.0.0 & newer
        ts = cert.not_valid_before_utc
    except AttributeError:
        ts = cert.not_valid_before
        ts = datetime.datetime.combine(ts.date(), ts.time(),
                                       datetime.timezone.utc)
    return ts

def cert_not_valid_after(cert):
    try:
        # cryptography 42.0.0 & newer
        ts = cert.not_valid_after_utc
    except AttributeError:
        ts = cert.not_valid_after
        ts = datetime.datetime.combine(ts.date(), ts.time(),
                                       datetime.timezone.utc)
    return ts
