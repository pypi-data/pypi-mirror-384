[description]

The virt-fw-sigdb utility can create, modify and print EFI signature
databases.  This is the format used by UEFI firmware to store lists of
certificates and authenticode hashes for binaries in EFI variables
like 'PK', 'KEK', 'db' and 'dbx'.

Usually signature databases are embedded in EFI variable stores, so
for most use cases you'll probably should check out the
virt-fw-vars(1) utility instead of this.

The exception to this rule is the list of root CA certificates for TLS
connections which can be passed from the host via qemu to OVMF using
the etc/edk2/https/cacerts fw_cfg file.

[examples]

.TP
Print system root CA database
virt-fw-sigdb --print \\
    --input /etc/pki/ca-trust/extracted/edk2/cacerts.bin

[author]

Gerd Hoffmann <kraxel@redhat.com>

