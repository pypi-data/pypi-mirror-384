#!/bin/sh
#
# create uefi variable update for KEK to enroll the 2023 microsoft key
#
# instructiony by microsoft
#   https://github.com/microsoft/secureboot_objects/wiki/OEM-Certificate-Key-Rolling
#
# Requires: efitools
# Requires: python3-virt-firmware
# Requires: virt-sb-certs
#

########################################################################

# taken from the instructions above
TIMESTAMP="2010-03-06 19:17:21"
CERTGUID="8be4df61-93ca-11d2-aa0d-00e098032b8c"

# the 2023 microsoft kek certificate
CERTFILE="/usr/share/virt-sb-certs/microsoft.com/ms-kek-2023.pem"

# config
BASENAME="KEK2023"

########################################################################

# step #1 -- create *.forsig file
echo "# creating ${BASENAME}.forsig"
(
    set -ex
    virt-fw-sigdb \
        --add-cert "$CERTGUID" "$CERTFILE" \
        --output "${BASENAME}.esl"
    sign-efi-sig-list -a -t "$TIMESTAMP" -o \
                      KEK "${BASENAME}.esl" "${BASENAME}.forsig"
)
echo "# ok"

# step #2 -- [manual] get detached pkcs7 signature from signing server

# step #3 -- create uefi variable update binary using the signature
if test ! -f "${BASENAME}.signed"; then
    echo "# missing: ${BASENAME}.signed"
else
    echo "# creating ${BASENAME}.auth"
    (
        set -ex
        sign-efi-sig-list -a -t "$TIMESTAMP" -i "${BASENAME}.signed" \
                          KEK "${BASENAME}.esl" "${BASENAME}.auth"
    )
    echo "# ok"
fi
