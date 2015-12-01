# -*- coding: utf-8 -*-

__author__ = 'Sergey Sobko'

from argparse import ArgumentParser
from copy import deepcopy
from plistlib import readPlist, writePlist
from pprint import pprint
from uuid import uuid4

SYSTEM_CONFIGURATION_PLIST = '/Library/Preferences/SystemConfiguration/preferences.plist'

SECTION_NETWORKSERVICES = 'NetworkServices'
SECTION_INTERFACE = 'Interface'
SECTION_DEVICENAME = 'DeviceName'
SECTION_USERDEFINEDNAME = 'UserDefinedName'
SECTION_SETS = 'Sets'
SECTION_NETWORK = 'Network'
SECTION_GLOBAL = 'Global'
SECTION_IPV4 = 'IPv4'
SECTION_SERVICEORDER = 'ServiceOrder'
SECTION_SERVICE = 'Service'


def get_configuration():
    return readPlist(SYSTEM_CONFIGURATION_PLIST)


def write_configuration(configuration):
    writePlist(configuration, SYSTEM_CONFIGURATION_PLIST)


def create_uuid():
    return str(uuid4()).upper()


def get_adapter_by_name(configuration, adapter_name):
    network_services = configuration.get(SECTION_NETWORKSERVICES, {})

    for service_uuid, service_dict in network_services.iteritems():
        interface_section = service_dict.get(SECTION_INTERFACE, {})
        device_name = interface_section.get(SECTION_DEVICENAME)

        if adapter_name == device_name:
            return service_dict

    return None


def create_adapter_from_another(configuration, src_adapter_name, dst_adapter_name, dst_user_defined_name):
    src_adapter = deepcopy(get_adapter_by_name(configuration, src_adapter_name))

    if not src_adapter:
        return None

    dst_adapter_uuid = create_uuid()

    network_services = configuration.setdefault(SECTION_NETWORKSERVICES, {})

    interface = src_adapter.setdefault(SECTION_INTERFACE, {})

    interface.update({
        SECTION_DEVICENAME: dst_adapter_name,
        SECTION_USERDEFINEDNAME: dst_user_defined_name
    })

    network_services[dst_adapter_uuid] = src_adapter
    network_services[dst_adapter_uuid][SECTION_USERDEFINEDNAME] = dst_user_defined_name

    configuration_set_id = configuration[SECTION_SETS].keys()[0]

    network_set_section = configuration[SECTION_SETS][configuration_set_id][SECTION_NETWORK]

    network_set_section \
        .setdefault(SECTION_GLOBAL, {}).setdefault(SECTION_IPV4, {}).setdefault(SECTION_SERVICEORDER, []) \
        .append(dst_adapter_uuid)

    network_set_section.setdefault(SECTION_SERVICE)[dst_adapter_uuid] = {
        '__LINK__': '/NetworkServices/{dst_adapter_uuid}'.format(
            dst_adapter_uuid=dst_adapter_uuid
        )
    }

    return configuration


def main():
    argument_parser = ArgumentParser(description='OS X Networking Helpers')

    argument_parser.add_argument('src_interface', help='Source interface (e.g, en0)')
    argument_parser.add_argument('dst_interface', help='Destination interface (e.g, vboxnet0)')
    argument_parser.add_argument('dst_interface_name',
                                 help='Destination interface (e.g, VirtualBox Host-Only Adapter)')

    args = argument_parser.parse_args()

    configuration = get_configuration()

    configuration = create_adapter_from_another(
        configuration,
        args.src_interface,
        args.dst_interface,
        args.dst_interface_name
    )

    pprint(configuration)

    try:
        write_configuration(configuration)

    except OSError as ex:
        print 'Cannot write configuration file: {ex}'.format(ex=ex.message)


if __name__ == '__main__':
    main()
