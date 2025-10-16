#!/usr/bin/python
#
# SPDX-License-Identifier: GPL-2.0-only
# (c) 2023 Gerd Hoffmann
#
""" efi x509 certificates """
import datetime
import sys
import tempfile

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa


if sys.version_info >= (3, 13):
    import importlib.resources

    def resource_filename(module, filename):
        """
        Mimics pkg_resources.resource_filename in a way.

        Enters the context manager provided by importlib.resources.path
        and never exits it.
        """
        return str(importlib.resources.path(module, filename).__enter__())
else:
    from pkg_resources import resource_filename


# redhat: PK + KEK key
REDHAT_PK = resource_filename('virt.firmware', 'certs/redhat.com/rh-pk-kek-2014.pem')

# microsoft: KEK key
MS_KEK_2011 = resource_filename('virt.firmware', 'certs/microsoft.com/ms-kek-2011.pem')
MS_KEK_2023 = resource_filename('virt.firmware', 'certs/microsoft.com/ms-kek-2023.pem')

# microsoft: used to sign windows
MS_WIN_2011 = resource_filename('virt.firmware', 'certs/microsoft.com/windows-2011.pem')
MS_WIN_2023 = resource_filename('virt.firmware', 'certs/microsoft.com/windows-2023.pem')

# microsoft: used to sign 3rd party binaries (shim.efi, drivers).
MS_3RD_2011 = resource_filename('virt.firmware', 'certs/microsoft.com/ms-uefi-2011.pem')
MS_3RD_2023 = resource_filename('virt.firmware', 'certs/microsoft.com/ms-uefi-2023.pem')
MS_ROM_2023 = resource_filename('virt.firmware', 'certs/microsoft.com/ms-uefi-rom-2023.pem')

# for backward compatibility
MS_KEK = MS_KEK_2011
MS_WIN = MS_WIN_2011
MS_3RD = MS_3RD_2011

# linux distro ca keys
DISTRO_CA = {
    #
    # microsoft keys
    #
    'windows' : {
        'desc'  : 'Microsoft Windows',
        'certs' : [
            MS_WIN_2011,
            MS_WIN_2023,
        ],
    },
    'ms-uefi' : {
        'desc'  : 'Microsoft UEFI CA',
        'certs' : [
            MS_3RD_2011,
            MS_3RD_2023,
        ],
    },
    'ms-uefi-rom' : {
        'desc'  : 'Microsoft Option ROM UEFI CA',
        'certs' : [
            MS_ROM_2023,
        ],
    },

    #
    # redhat / rhel keys
    #
    'rhel-2014' : {
        'desc'  : 'Red Hat Enterprise Linux (obsoleted by 2020 signing key rotation)',
        'certs' : [
            resource_filename('virt.firmware', 'certs/redhat.com/redhat-2014.pem'),
        ],
    },
    'rhel' : {
        'desc'  : 'Red Hat Enterprise Linux',
        'certs' : [
            resource_filename('virt.firmware', 'certs/redhat.com/redhat-2020.pem'),
            resource_filename('virt.firmware', 'certs/redhat.com/redhat-2023.pem'),
    ],
    },
    'rh-uefi' : {
        'desc'  : 'Red Hat UEFI CA',
        'certs' : [
            resource_filename('virt.firmware', 'certs/redhat.com/rh-uefi-2024.pem'),
        ],
    },

    #
    # fedora keys
    #
    'fedora' : {
        'desc'  : 'Fedora Linux',
        'certs' : [
            resource_filename('virt.firmware', 'certs/fedoraproject.org/fedora-2020.pem'),
        ],
    },

    #
    # centos keys
    #
    'centos-2018' : {
        'desc'  : 'CentOS Stream (obsoleted by 2020 signing key rotation)',
        'certs' : [
            resource_filename('virt.firmware', 'certs/centos.org/centos-2018.pem'),
        ],
    },
    'centos' : {
        'desc'  : 'CentOS Stream',
        'certs' : [
            resource_filename('virt.firmware', 'certs/centos.org/centos-2020.pem'),
        ],
    },

    #
    # debian keys
    #
    'debian' : {
        'desc'  : 'Debian Linux',
        'certs' : [
            resource_filename('virt.firmware', 'certs/debian.org/debian-2016.pem'),
        ],
    },

    #
    # ubuntu keys
    #
    'ubuntu' : {
        'desc'  : 'Ubuntu Linux',
        'certs' : [
            resource_filename('virt.firmware', 'certs/ubuntu.com/ubuntu-2012.pem'),
        ],
    },
}

def list_distros():
    print('known distro certs:')
    for (key, val) in DISTRO_CA.items():
        print(f'  {key:12s} - {val["desc"]}')

def pk_generate(cn = 'random secure boot platform',
                org = None, city = None, state = None, country = None):
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    attrs = [
        x509.NameAttribute(x509.NameOID.COMMON_NAME, cn),
    ]
    if org:
        attrs.append(x509.NameAttribute(x509.NameOID.ORGANIZATION_NAME, org))
    if city:
        attrs.append(x509.NameAttribute(x509.NameOID.LOCALITY_NAME, city))
    if state:
        attrs.append(x509.NameAttribute(x509.NameOID.STATE_OR_PROVINCE_NAME, state))
    if country:
        attrs.append(x509.NameAttribute(x509.NameOID.COUNTRY_NAME, country))

    subject = issuer = x509.Name(attrs)
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        now
    ).not_valid_after(
        now + datetime.timedelta(days = 365 * 10)
    ).add_extension(
        x509.BasicConstraints(ca = False, path_length = None),
        critical = False,
    ).sign(key, hashes.SHA256())

    # pylint: disable=consider-using-with
    tf = tempfile.NamedTemporaryFile()
    tf.write(cert.public_bytes(serialization.Encoding.PEM))
    tf.flush()
    return tf
