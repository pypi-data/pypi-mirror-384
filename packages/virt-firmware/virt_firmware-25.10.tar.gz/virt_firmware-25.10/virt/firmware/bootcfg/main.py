#!/usr/bin/python3
#
# SPDX-License-Identifier: GPL-2.0-only
# (c) 2023 Gerd Hoffmann
#
""" experimental efi boot config tool """
import os
import sys
import logging
import argparse

import pefile

from virt.firmware.efi import ucs16
from virt.firmware.efi import guids
from virt.firmware.efi import devpath
from virt.firmware.efi import bootentry

from virt.firmware.bootcfg import bootcfg
from virt.firmware.bootcfg import linuxcfg

from virt.peutils import pesign


########################################################################
# main

def update_next_or_order(cfg, options, nr):
    if options.bootnext:
        cfg.set_boot_next(nr)
        if not options.dryrun:
            cfg.linux_update_next()

    if options.bootorder is not None:
        cfg.set_boot_order(nr, options.bootorder)
        if not options.dryrun:
            cfg.linux_update_order()


def firmware_loads_efi_binary(cfg, efibinary):
    if not cfg.secureboot:
        return True
    if pesign.cryptography_major < 40:
        # can't use pesign.pe_check_cert() -> play safe
        return False
    db = cfg.varstore.get_variable('db', guids.EfiImageSecurityDatabase)
    pe = pefile.PE(efibinary)
    siglist = pesign.pe_type2_signatures(pe)
    if pesign.pe_check_cert(siglist, db):
        return True
    return False


def create_boot_entry(efiuki, options):
    if options.shim:
        efishim = linuxcfg.LinuxEfiFile(options.shim)
        if efishim.device != efiuki.device:
            logging.error('shim and uki are on different filesystems')
            sys.exit(1)
        if options.cmdline:
            optdata = ucs16.from_string(efiuki.efi_filename() + ' ' + options.cmdline)
        else:
            optdata = ucs16.from_string(efiuki.efi_filename())
        entry = bootentry.BootEntry(title = ucs16.from_string(options.title),
                                    attr = bootentry.LOAD_OPTION_ACTIVE,
                                    devicepath = efishim.dev_path_file(),
                                    optdata = bytes(optdata))
    else:
        if options.cmdline:
            optdata = ucs16.from_string(options.cmdline)
            entry = bootentry.BootEntry(title = ucs16.from_string(options.title),
                                        attr = bootentry.LOAD_OPTION_ACTIVE,
                                        devicepath = efiuki.dev_path_file(),
                                        optdata = bytes(optdata))
        else:
            entry = bootentry.BootEntry(title = ucs16.from_string(options.title),
                                        attr = bootentry.LOAD_OPTION_ACTIVE,
                                        devicepath = efiuki.dev_path_file())
    return entry


def add_uki(cfg, options):
    if not options.shim and not firmware_loads_efi_binary(cfg, options.adduki):
        logging.error('shim binary needed but not found or specified')
        sys.exit(1)
    if not options.title:
        logging.error('entry title not specified')
        sys.exit(1)
    if options.cmdline and cfg.secureboot:
        logging.warning('Overriding built-in UKI cmdline is not possible'
                        ' when Secure Boot is enabled')

    efiuki = linuxcfg.LinuxEfiFile(options.adduki)
    nr = cfg.find_uki_entry(efiuki.efi_filename())
    if nr is None:
        nr = cfg.find_devpath_entry(efiuki.dev_path_file())
    if nr is not None:
        logging.info('Entry exists (Boot%04X)', nr)
    else:
        entry = create_boot_entry(efiuki, options)
        logging.info('Create new entry: %s', str(entry))
        nr = cfg.add_entry(entry)
        logging.info('Added entry (Boot%04X)', nr)
        if not options.dryrun:
            cfg.linux_write_entry(nr)

    update_next_or_order(cfg, options, nr)


def update_uki(cfg, options):
    efiuki = linuxcfg.LinuxEfiFile(options.updateuki)
    nr = cfg.find_uki_entry(efiuki.efi_filename())
    if nr is None:
        nr = cfg.find_devpath_entry(efiuki.dev_path_file())
    if nr is None:
        logging.error('No entry found for %s', options.updateuki)
        sys.exit(1)

    update_next_or_order(cfg, options, nr)


def remove_uki(cfg, options):
    efiuki = linuxcfg.LinuxEfiFile(options.removeuki)
    nr = cfg.find_uki_entry(efiuki.efi_filename())
    if nr is None:
        nr = cfg.find_devpath_entry(efiuki.dev_path_file())
    if nr is None:
        logging.warning('No entry found for %s', options.removeuki)
        return

    logging.info('Removing entry (Boot%04X)', nr)
    cfg.remove_entry(nr)
    if not options.dryrun:
        cfg.linux_remove_entry(nr)
        cfg.linux_update_next()
        cfg.linux_update_order()


def boot_success(cfg, options):
    if cfg.bcurr in cfg.blist:
        logging.info('No update needed, BootCurrent is already in BootOrder.')
        return
    logging.info('Add BootCurrent (Boot%04X) to BootOrder', cfg.bcurr)
    cfg.set_boot_order(cfg.bcurr, 0)
    if not options.dryrun:
        cfg.linux_update_order()


def update_boot_csv(cfg, options):
    if not options.shim:
        logging.error('shim binary not specified')
        sys.exit(1)
    efishim  = linuxcfg.LinuxEfiFile(options.shim)
    shimpath = efishim.dev_path_file()

    shimdir  = os.path.dirname(options.shim)
    shimname = os.path.basename(options.shim)
    csvname  = shimname.upper() \
                     .replace('SHIM', 'BOOT') \
                     .replace('EFI','CSV')

    csvdata = ''
    # Shim fallback creates entries and adds them to BootOrder as it reads
    # BOOT.CSV, this means that the existing BootOrder must be parsed in reversed
    # order.
    for nr in reversed(cfg.blist):
        entry = cfg.bentr[nr]
        if not entry:
            continue
        if not entry.devicepath:
            continue
        if entry.devicepath != shimpath:
            continue
        args = ''
        if entry.optdata:
            args = ucs16.from_ucs16(entry.optdata)
        csvdata += f'{shimname},{entry.title},{args} ,Comment\n'

    logging.info('Updating %s/%s', shimdir, csvname)
    with open(f'{shimdir}/{csvname}', 'wb') as f:
        f.write(b'\xff\xfe')
        f.write(csvdata.encode('utf-16le'))


def add_uri(cfg, options):
    if not options.title:
        logging.error('entry title not specified')
        sys.exit(1)

    devicepath = devpath.DevicePath.uri(options.adduri)
    nr = cfg.find_devpath_entry(devicepath)
    if nr is not None:
        logging.info('Entry exists (Boot%04X)', nr)
    else:
        entry = bootentry.BootEntry(title = ucs16.from_string(options.title),
                                    attr = bootentry.LOAD_OPTION_ACTIVE,
                                    devicepath = devicepath)
        logging.info('Create new entry: %s', str(entry))
        nr = cfg.add_entry(entry)
        logging.info('Added entry (Boot%04X)', nr)
        if not options.dryrun:
            cfg.linux_write_entry(nr)

    update_next_or_order(cfg, options, nr)


def remove_entry(cfg, options):
    nr = int(options.removeentry, base = 16)
    logging.info('Removing entry (Boot%04X)', nr)
    cfg.remove_entry(nr)
    if not options.dryrun:
        cfg.linux_remove_entry(nr)
        cfg.linux_update_next()
        cfg.linux_update_order()


def process_boot_order_arg(pos):
    if pos == 'last':
        return -1
    try:
        return int(pos)
    except argparse.ArgumentTypeError as err:
        raise err
    except (TypeError, ValueError) as err:
        raise argparse.ArgumentTypeError("--boot-order must be a number or 'last'") from err

# pylint: disable=too-many-boolean-expressions,too-many-branches,too-many-statements
def main():
    parser = argparse.ArgumentParser(
        description = 'Show and manage uefi boot entries.')

    parser.add_argument('-l', '--loglevel', dest = 'loglevel', type = str, default = 'info',
                        help = 'set loglevel to LEVEL', metavar = 'LEVEL')
    parser.add_argument('--vars', dest = 'varsfile', type = str,
                        help = 'read edk2 vars from FILE', metavar = 'FILE')
    parser.add_argument('--show', dest = 'show',
                        action = 'store_true', default = False,
                        help = 'print boot configuration')
    parser.add_argument('-v', '--verbose', dest = 'verbose',
                        action = 'store_true', default = False,
                        help = 'print more details')

    group = parser.add_argument_group('update unified kernel image (UKI) boot entries')
    group.add_argument('--add-uki', dest = 'adduki', type = str,
                       help = 'add boot entry for UKI image FILE', metavar = 'FILE')
    group.add_argument('--update-uki', dest = 'updateuki', type = str,
                       help = 'update boot entry for UKI image FILE', metavar = 'FILE')
    group.add_argument('--remove-uki', dest = 'removeuki', type = str,
                       help = 'remove boot entry for UKI image FILE', metavar = 'FILE')
    group.add_argument('--cmdline', dest = 'cmdline', type = str,
                       help = 'override UKIs cmdline when adding boot entry '
                       '(ignored when Secure Boot is enabled)', metavar = 'CMDLINE')
    group.add_argument('--boot-ok', '--boot-successful', dest = 'bootok',
                       action = 'store_true', default = False,
                       help = 'boot is successful, add BootCurrent to BootOrder.')
    group.add_argument('--update-csv', dest = 'updatecsv',
                       action = 'store_true', default = False,
                       help = 'update BOOT.CSV')

    group = parser.add_argument_group('update other boot entries')
    group.add_argument('--add-uri', dest = 'adduri', type = str,
                       help = 'add boot entry to netboot URI', metavar = 'URI')
    group.add_argument('--remove-entry', dest = 'removeentry', type = str,
                       help = 'add remove entry NNNN', metavar = 'NNNN')

    group = parser.add_argument_group('options for boot entry updates')
    group.add_argument('--once', '--boot-next', dest = 'bootnext',
                       action = 'store_true', default = False,
                       help = 'boot added/updated entry once (using BootNext)')
    group.add_argument('--boot-order', dest = 'bootorder', type = process_boot_order_arg,
                       help = 'place added/updated entry at POS in BootOrder (0 is first)',
                       metavar = 'POS')
    group.add_argument('--dry-run', dest = 'dryrun',
                       action = 'store_true', default = False,
                       help = 'do not actually update the configuration')
    group.add_argument('--title', dest = 'title', type = str,
                       help = 'label the entry with TITLE', metavar = 'TITLE')
    group.add_argument('--shim', dest = 'shim', type = str,
                       help = 'use shim binary FILE', metavar = 'FILE')

    group = parser.add_argument_group('print system information')
    group.add_argument('--print-loader', dest = 'printloader',
                       action = 'store_true', default = False,
                       help = 'print boot loader name')

    options = parser.parse_args()

    logging.basicConfig(format = '%(levelname)s: %(message)s',
                        level = getattr(logging, options.loglevel.upper()))

    # sanity checks
    if options.varsfile and (options.adduki or
                             options.updateuki or
                             options.removeuki or
                             options.bootok or
                             options.updatecsv or
                             options.adduri or
                             options.removeentry or
                             options.printloader):
        logging.error('operation not supported for edk2 varstores')
        sys.exit(1)

    # read info
    if options.varsfile:
        cfg = bootcfg.VarStoreEfiBootConfig(options.varsfile)
        loader = None
    else:
        cfg = linuxcfg.LinuxEfiBootConfig()
        loader = cfg.linux_loader_info()

    # find shim if needed
    if not options.shim and (options.adduki or
                             options.updatecsv):
        osinfo = linuxcfg.LinuxOsInfo()
        options.shim = osinfo.shim_path()

    # apply updates
    if options.adduki:
        add_uki(cfg, options)
    elif options.updateuki:
        update_uki(cfg, options)
    elif options.removeuki:
        remove_uki(cfg, options)
    elif options.bootok:
        boot_success(cfg, options)
        if options.updatecsv and options.shim:
            update_boot_csv(cfg, options)
    elif options.updatecsv:
        update_boot_csv(cfg, options)
    elif options.adduri:
        add_uri(cfg, options)
    elif options.removeentry:
        remove_entry(cfg, options)
    elif options.printloader:
        if loader:
            print(str(loader))
        else:
            print('unknown')
    else:
        # default action
        options.show = True

    # print info
    if options.show:
        cfg.print_cfg(options.verbose)

    return 0

if __name__ == '__main__':
    sys.exit(main())
