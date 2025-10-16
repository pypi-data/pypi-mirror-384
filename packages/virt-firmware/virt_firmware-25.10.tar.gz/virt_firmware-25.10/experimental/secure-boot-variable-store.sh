#!/bin/bash
#
# create a collection of different secure boot variable store configurations
#

# args
template="${1-/usr/share/edk2/ovmf/OVMF_VARS.fd}"

ext="${template##*.}"
base="${template##*/}"
base="${base%.${ext}}"
dbx="$(echo /usr/share/edk2/ovmf/DBXUpdate-*.x64.bin)"

declare -a common
common+=("--input" "$template")
common+=("--enroll-redhat")
common+=("--secure-boot")
common+=("--set-dbx" "$dbx")
common+=("--no-microsoft")

# enable everything (this is what we ship today)
virt-fw-vars "${common[@]}" --output ${base}.secboot.${ext} \
     --distro-keys windows-2011 \
     --distro-keys windows \
     --distro-keys ms-uefi
echo "--"

# old windows boot media
virt-fw-vars "${common[@]}" --output ${base}.sb.windows.2011.${ext} \
     --distro-keys windows-2011
echo "--"

# new windows boot media
virt-fw-vars "${common[@]}" --output ${base}.sb.windows.2023.${ext} \
     --distro-keys windows
echo "--"

# generic linux (via microsoft uefi ca)
#  - There are also 2011 and 2023 UEFI CA certs.
#  - I have not yet seen a shim.efi signed with the 2023 cert.
#  - Once this changes it makes sense to split this one into
#    2011 and 2023 variants too.
virt-fw-vars "${common[@]}" --output ${base}.sb.linux.${ext} \
     --distro-keys ms-uefi
echo "--"

# redhat linux (via redhat uefi ca, not yet used)
virt-fw-vars "${common[@]}" --output ${base}.sb.rh-uefi.${ext} \
     --distro-keys rh-uefi
echo "--"

# generic linux plus redhat test builds
#  - FOR TESTING ONLY, NOT SUITABLE FOR PRODUCTION USE.
#  - Include the signing cert used for local builds and scratch builds.
#  - Allows to boot test builds with secure boot enabled.
#  - The private key for this certificate is public, everyone can sign
#    everything with this key, so this provides no security guarantees
#    whatsoever.
#  - Signing key is included in the pesign rpm package.
testcert=$(mktemp /tmp/cert-rhtest-XXXXXXXX.pem)
certutil -L -d /etc/pki/pesign-rh-test -n "Red Hat Test CA" -a | openssl x509 -text > "$testcert"
virt-fw-vars "${common[@]}" --output ${base}.sb.testbuilds.${ext} \
     --distro-keys ms-uefi \
     --add-db OvmfEnrollDefaultKeys "$testcert"
rm -f "$testcert"
