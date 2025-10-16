"""
Harvester scripts

Currently only supports AVR atdf files
"""
# pylint: disable=consider-using-f-string,line-too-long

import os
import collections
import argparse
import textwrap
import pprint
from xml.etree import ElementTree

from pymcuprog.deviceinfo.memorynames import MemoryNames
from pymcuprog.deviceinfo.deviceinfokeys import DeviceMemoryInfoKeys, DeviceInfoKeysAvr

# High voltage implementations as defined on https://confluence.microchip.com/x/XVxcE
HV_IMPLEMENTATION_SHARED_UPDI = "0"
HV_IMPLEMENTATION_DEDICATED_UPDI = "1"
HV_IMPLEMENTATION_SEPARATE_PIN = "2"

def map_atdf_memory_name_to_pymcuprog_name(atdf_name):
    """
    Mapping a memory name in atdf files to the corresponding memory name used in the pymcuprog device models

    Note that the same memory can have different names in the same atdf file depending on the element used as
    definition, i.e. memory-segment element or module element
    :param atdf_name: Name of memory in atdf files
    :return: Name of memory in pymcuprog device models
    """
    pymcuprog_name = 'unknown'
    atdf_name = atdf_name.lower()
    if atdf_name in ['progmem', 'flash', 'prog']:
        pymcuprog_name = MemoryNames.FLASH
    if atdf_name in ['user_signatures', 'userrow']:
        # Datasheets actually use user_row for UPDI devices at least
        pymcuprog_name = MemoryNames.USER_ROW
    if atdf_name == 'bootrow':
        pymcuprog_name = MemoryNames.BOOT_ROW
    if atdf_name == 'eeprom':
        pymcuprog_name = MemoryNames.EEPROM
    if atdf_name in ['fuses', 'fuse']:
        pymcuprog_name = MemoryNames.FUSES
    if atdf_name in ['lockbits', 'lock']:
        pymcuprog_name = MemoryNames.LOCKBITS
    if atdf_name in ['signatures', 'sigrow']:
        pymcuprog_name = MemoryNames.SIGNATURES
    if atdf_name in ['internal_sram', 'iram']:
        pymcuprog_name = MemoryNames.INTERNAL_SRAM

    return pymcuprog_name

def determine_chiperase_effect(memoryname, architecture):
    """
    Determine if memory is erased by a chip erase

    :param memoryname: Name of memory as defined in pymcuprog.deviceinfo.memorynames
    :type memoryname: str
    :param architecture: Architecture as defined in atdf file
    :type architecture: str
    :return: Chip erase effect
    :rtype: str
    """
    if 'avr' in architecture:
        if memoryname in [MemoryNames.USER_ROW, MemoryNames.FUSES, MemoryNames.SIGNATURES, MemoryNames.INTERNAL_SRAM]:
            return 'ChiperaseEffect.NOT_ERASED'
        if memoryname in [MemoryNames.LOCKBITS, MemoryNames.FLASH]:
            return 'ChiperaseEffect.ALWAYS_ERASED'
        if memoryname in [MemoryNames.EEPROM, MemoryNames.BOOT_ROW]:
            return 'ChiperaseEffect.CONDITIONALLY_ERASED_AVR'

    return '# To be filled in manually'

def determine_isolated_erase(memoryname, architecture):
    """
    Determine if memory can be erased without side effects

    :param memoryname: Name of memory as defined in pymcuprog.deviceinfo.memorynames
    :type memoryname: str
    :param architecture: Architecture as defined in atdf file
    :type architecture: str
    :return: 'True' if memory can be erased in isolation, 'False' if not.
    :rtype: str
    """
    if 'avr' in architecture:
        if 'avr8x' in architecture and memoryname in [MemoryNames.FLASH]:
            # UPDI devices now supports isolated erase for flash
            return 'True'
        if memoryname in [MemoryNames.USER_ROW, MemoryNames.EEPROM, MemoryNames.BOOT_ROW]:
            return 'True'
        if memoryname in [MemoryNames.INTERNAL_SRAM, MemoryNames.LOCKBITS, MemoryNames.FLASH, MemoryNames.FUSES, MemoryNames.SIGNATURES]:
            return 'False'

    return '# To be filled in manually'

def determine_write_size(memoryname, pagesize, devicename):
    """
    Determine write granularity for memory

    :param memoryname: Name of memory as defined in pymcuprog.deviceinfo.memorynames
    :type memoryname: str
    :param pagesize: Page size of memory
    :type pagesize: str or int
    :return: Write granularity as string
    :rtype: str
    """
    write_size = "0x01"
    devicename = devicename.lower()
    if memoryname == 'flash':
        if (devicename.find('avr') != -1 and ((devicename.find('da') != -1) or (devicename.find('db') != -1))):
            write_size = "0x02"
        else:
            write_size = pagesize
    if memoryname == "user_row":
        if devicename.find('avr') != -1 and devicename.find('ea') != -1:
            # For AVR EA user row the complete page must be written
            write_size = pagesize
    elif memoryname == 'signatures':
        write_size = "0x00"
    return write_size

def determine_read_size(memoryname):
    """
    Determine read granularity for memory

    :param memoryname: Name of memory as defined in pymcuprog.deviceinfo.memorynames
    :type memoryname: str
    :return: Read granularity as string
    :rtype: str
    """
    # Read size is always 1 byte except for flash that can only read complete words
    readsize = "0x01"
    if memoryname in [MemoryNames.FLASH]:
        readsize = "0x02"

    return readsize

def capture_memory_segment_attributes(attributes, memories):
    """
    Capture memory attributes for memory segment

    :param attributes: Memory attributes to capture (from atdf)
    :type attributes: xml.etree.ElementTree.Element instance
    :param memories: Dictionary with memory information. Captured data will be added to this dict.
    :type memories: dict
    """
    name = attributes['name'].lower()
    size = attributes['size']
    start = attributes['start']

    try:
        pagesize = attributes['pagesize']
    except KeyError:
        pagesize = "0x01"
    # For some AVRs the ATDF gives a pagesize of fuses and lockbits equal to flash or EEPROM page size but fuses and
    # lockbits are always byte accessible.
    if name in ['fuses', 'lockbits']:
        pagesize = '0x01'
    # These names are the names used in the atdf files and might differ from the pymcuprog MemoryNames
    if name in ['progmem', 'flash', 'eeprom', 'user_signatures', 'fuses', 'lockbits', 'signatures', 'internal_sram', 'iram']:
        print_name = map_atdf_memory_name_to_pymcuprog_name(name)
        if not print_name in memories:
            memories[print_name] = {}
        if  memories[print_name].get(DeviceMemoryInfoKeys.ADDRESS) is None:
            memories[print_name][DeviceMemoryInfoKeys.ADDRESS] = start
        if  memories[print_name].get(DeviceMemoryInfoKeys.SIZE) is None or \
            memories[print_name].get(DeviceMemoryInfoKeys.SIZE) == 'UNKNOWN':
            memories[print_name][DeviceMemoryInfoKeys.SIZE] = size
        if  memories[print_name].get(DeviceMemoryInfoKeys.PAGE_SIZE) is None:
            memories[print_name][DeviceMemoryInfoKeys.PAGE_SIZE] = pagesize

def capture_register_offset(name, offset):
    """
    Wrapper to create a string definition

    :param name: register name
    :type name: str
    :param offset: register offset
    :type offset: str
    :return: string of register and offset
    :rtype: str
    """
    return capture_field("{}_base".format(name.lower()), offset)


def capture_field(field, value):
    """
    Macro to create text format field

    :param field: register name
    :type field: str
    :param value: register value
    :type value: str
    :return: string of definition
    :rtype: str
    """
    try:
        _test_value = int(value, 16)
    except (ValueError, AttributeError):
        # Can't convert string to int, assumed to be string
        return "    '{}': '{}',\n".format(field, value)
    return "    '{}': {},\n".format(field, value)

def capture_device_data_from_device_element(element):
    """
    Capture device data from a device element

    :param element: element with tag='device'
    :type element: xml.etree.ElementTree.Element instance
    :return: captured data from the device element as a string
    :rtype: str
    """
    architecture = element.attrib['architecture'].lower()
    output = capture_field('name', element.attrib['name'].lower())
    output += capture_field('architecture', architecture)
    return output

def capture_memory_segments_from_device_element(element, memories):
    """
    Capture memory segment data from a device element

    :param element: element with tag='device'
    :type element: xml.etree.ElementTree.Element instance
    :return: captured data from the device element as a string
    :rtype: str
    """
    output = ""
    for i in element.iterfind("address-spaces/address-space/memory-segment"):
        capture_memory_segment_attributes(i.attrib, memories)
    return output

def capture_module_element(element):
    """
    Capture data from a module element

    This function will return data captured from the module element but will also check if the module
    element contains info about an UPDI fuse (fuse to configure a shared UPDI pin)
    :param element: element with tag='module'
    :type element: xml.etree.ElementTree.Element instance
    :return: tuple of
    * output - captured module element data as a string
    * found_updi_fuse - True if the module element contained info about an UPDI fuse
    :rtype: tuple
    """
    output = ""
    found_updi_fuse = False
    for i in element.iterfind("instance/register-group"):
        name = i.attrib['name']
        offset = "0x{:08X}".format(int(i.attrib['offset'], 16))
        if i.attrib['name'] == 'SYSCFG':
            output += capture_register_offset(name, offset)
            output += capture_register_offset('OCD', "0x{:08X}".format(int(offset, 16) + 0x80))
        if i.attrib['name'] == 'NVMCTRL':
            output += capture_register_offset(name, offset)
    for i in element.iterfind("instance/signals/signal"):
        if i.attrib['group'] == 'UPDI' and i.attrib['pad'] is not None:
            output += capture_field('prog_clock_khz', '900')
            found_updi_fuse = True
    return output, found_updi_fuse

def capture_memory_module_element(element, memories):
    """
    Capture memory information from a memory module element

    :param element: Element with tag='module'
    :type element: xml.etree.ElementTree.Element instance
    :param memories: Dictionary with memory information. Captured memory information will be added to this
        dictionary
    :type memories: dict
    """
    memoryname = map_atdf_memory_name_to_pymcuprog_name(element.attrib['name'])
    if not memoryname in memories:
        # Discovered new memory, add it to the dictionary
        memories[memoryname] = {}
        # All memories defined as memory modules in the device element can be read and written a single byte at a time
        memories[memoryname][DeviceMemoryInfoKeys.READ_SIZE] = "0x01"
        memories[memoryname][DeviceMemoryInfoKeys.PAGE_SIZE] = "0x01"
        if memoryname in ['sigrow']:
            # Signatures can't be written at all
            memories[memoryname][DeviceMemoryInfoKeys.WRITE_SIZE] = "0x00"
        else:
            memories[memoryname][DeviceMemoryInfoKeys.WRITE_SIZE] = "0x01"
    for rg in element.iterfind("instance/register-group"):
        # Offset is found in the module instance register group
        memories[memoryname][DeviceMemoryInfoKeys.ADDRESS] = rg.attrib['offset']
    for rg in element.iterfind("register-group"):
        # Size is found in the module register group
        if 'size' in rg.attrib:
            memories[memoryname][DeviceMemoryInfoKeys.SIZE] = rg.attrib['size']
            if element.attrib['name'].lower() in ['userrow']:
                # For user row set the page size equal to the size since this makes most sense when printing memory
                # content and when erasing, even though the write granularity is one byte
                memories[memoryname][DeviceMemoryInfoKeys.PAGE_SIZE] = rg.attrib['size']
        else:
            if memories[memoryname].get(DeviceMemoryInfoKeys.SIZE) is None:
                memories[memoryname][DeviceMemoryInfoKeys.SIZE] = "UNKNOWN"

def capture_signature_from_property_groups_element(element):
    """
    Capture signature (Device ID) data from a property-group element

    :param element: element with tag='property-groups'
    :type element: xml.etree.ElementTree.Element instance
    :return: bytearray with 3 bytes of Device ID data
    :rtype: bytearray
    """
    signature = bytearray(3)
    for i in element.findall('property-group/property'):
        if i.attrib['name'] == 'SIGNATURE0':
            signature[0] = int(i.attrib['value'], 16)
        if i.attrib['name'] == 'SIGNATURE1':
            signature[1] = int(i.attrib['value'], 16)
        if i.attrib['name'] == 'SIGNATURE2':
            signature[2] = int(i.attrib['value'], 16)
    return signature

def capture_eesave_from_register_group(element):
    """
    Capture the fuse address of the EESAVE bit from a register-group element

    :param element: element with tag='register-group'
    :type element: xml.etree.ElementTree.Element instance
    :return: fuse address where EESAVE is located
    :rtype: int
    """
    for reg in element.findall('register'):
        off = reg.attrib['offset']
        for bf in reg.findall('bitfield'):
            if bf.attrib['name'].lower() == 'eesave':
                return off
    return None

def capture_bootrst_from_register_group(element):
    """
    Capture the fuse address of the BOOTRST bit from a register-group element

    :param element: element with tag='register-group'
    :type element: xml.etree.ElementTree.Element instance
    :return: fuse address where BOOTRST is located
    :rtype: int
    """
    for reg in element.findall('register'):
        off = reg.attrib['offset']
        for bf in reg.findall('bitfield'):
            if bf.attrib['name'].lower() == 'bootrst':
                return off
    return None

def capture_dwen_from_register_group(element):
    """
    Capture the fuse address of the DWEN bit from a register-group element

    :param element: element with tag='register-group'
    :type element: xml.etree.ElementTree.Element instance
    :return: fuse address where DWEN is located
    :rtype: int
    """
    for reg in element.findall('register'):
        off = reg.attrib['offset']
        for bf in reg.findall('bitfield'):
            if bf.attrib['name'].lower() == 'dwen':
                return off
    return None

def capture_ocden_from_register_group(element):
    """
    Capture the fuse address of the OCDEN bit from a register-group element

    :param element: element with tag='register-group'
    :type element: xml.etree.ElementTree.Element instance
    :return: fuse address where OCDEN is located
    :rtype: int
    """
    for reg in element.findall('register'):
        off = reg.attrib['offset']
        for bf in reg.findall('bitfield'):
            if bf.attrib['name'].lower() == 'ocden':
                return off
    return None


def get_flash_offset(element):
    """
    Fetch flash memory offset from element

    :param element: Element with tag='property-groups'
    :type element: xml.etree.ElementTree.Element instance
    :return: Flash offset as string
    :rtype: str
    """
    flash_offset = "0x00000000"
    for i in element.iterfind("property-group/property"):
        if i.attrib['name'] == 'PROGMEM_OFFSET':
            flash_offset = i.attrib['value']
    return flash_offset

def get_hv_implementation(element):
    """
    Fetch High Voltage implementation from element

    :param element: Element with tag='property-groups'
    :type element: xml.etree.ElementTree.Element instance
    :return: High Voltage implementation as string (defined on https://confluence.microchip.com/x/XVxcE)
    :rtype: str
    """
    hv_implementation = None
    for i in element.iterfind("property-group/property"):
        if i.attrib['name'] == 'HV_IMPLEMENTATION':
            hv_implementation = i.attrib['value']

    return hv_implementation

def get_ocd_rev(element):
    """
    Fetch data about OCD revision
    :param element: Element with tag='property-groups'
    :type element: xml.etree.ElementTree.Element instance
    :return: ocd address and revision as string
    :rtype: str
    """
    ocd_rev = None
    for i in element.iterfind("property-group/property"):
        if i.attrib['name'] == 'OCD_REVISION':
            ocd_rev = i.attrib['value']
    return ocd_rev

def get_ocd_base(element):
    """
    Fetch data about OCD address (I/O reg address)
    :param element: Element with tag='property-groups'
    :type element: xml.etree.ElementTree.Element instance
    :return: ocd address and revision as string
    :rtype: str
    """
    ocd_base = None
    for i in element.iterfind("property-group/property"):
        if i.attrib['name'] == 'OCD_DATAREG':
            ocd_base = i.attrib['value']
    return ocd_base

def get_buf_per_page(element):
    """
    Fetch data about buffer per page
    :param element: Element with tag='property-groups'
    :type element: xml.etree.ElementTree.Element instance
    :return: ocd address and revision as string
    :rtype: str
    """
    bufpp = None
    for i in element.iterfind("property-group/property"):
        if i.attrib['name'] == 'BUFFERS_PER_FLASH_PAGE':
            bufpp = i.attrib['value']
    return bufpp


def determine_address_size(flash_offset):
    """
    Determine number of address bits needed for Flash

    :param flash_offset: Flash offset from atdf
    :type flash_offset: str
    :return: Address size ('16-bit' or '24-bit')
    :rtype: str
    """
    address_size = '16-bit'
    if flash_offset is not None:
        flash_offset = int(flash_offset, 16)
        if flash_offset > 0xFFFF:
            address_size = '24-bit'
    return address_size

def harvest_from_file(filename):
    #pylint: disable=too-many-statements,too-many-branches,too-many-locals
    """
    Harvest parameters from a file

    :param filename: path to file to parse
    :type filename: str
    :return: list of parameters
    :rtype: str
    """
    xml_iter = ElementTree.iterparse(filename)
    output = ""
    device_fields = ""
    extra_fields = "\n    # Some extra AVR specific fields\n"
    crit_fields = []
    interfaces = []
    shared_updi = False
    progmem_offset = None
    hv_implementation = None
    # These are all needed for DebugWIRE MCUs
    ocd_base = None
    ocd_rev = None
    eear_base = None
    eear_size = None
    eecr_base = None
    eedr_base = None
    spmcsr_base = None
    osccal_base = None
    dwen_base = None
    dwen_mask = None
    ocden_base = None
    ocden_mask = None
    bootrst_base = None
    bootrst_mask = None
    eesave_base = None
    eesave_mask = None
    buf_per_page = None

    memories = {}
    masked = []
    ronly = []
    for event, elem in xml_iter:
        if event == 'end':
            if elem.tag == 'device':
                devicename = elem.attrib['name']
                # Note module elements are part of the device element so the memories represented by modules will
                # already be collected when reaching end of device element
                capture_memory_segments_from_device_element(elem, memories)
                device_fields += capture_device_data_from_device_element(elem)
                architecture = elem.attrib['architecture'].lower()
            if elem.tag == 'module':
                # Some memories are defined as module elements (in addition to memory segments). These module
                # definitions are preferred as they give more accurate size definitions for some memories like fuses
                # and lockbits.
                if elem.attrib['name'].lower() in ['sigrow', 'fuse', 'fuses', 'lock', 'userrow']:
                    capture_memory_module_element(elem, memories)
                module, found_updi_fuse = capture_module_element(elem)
                extra_fields += module
                if found_updi_fuse:
                    shared_updi = True
            if elem.tag == 'interface':
                interfaces.append(elem.attrib['name'])
            if elem.tag == 'property-groups':
                signature = capture_signature_from_property_groups_element(elem)
                progmem_offset = get_flash_offset(elem)
                hv_implementation = get_hv_implementation(elem)
                ocd_rev = get_ocd_rev(elem)
                ocd_base = get_ocd_base(elem)
                if ocd_base and (int(ocd_base,16) + 0x20) not in masked:
                    masked.append(int(ocd_base,16) + 0x20)
                buf_per_page = get_buf_per_page(elem)
            if elem.tag == 'register':
                if elem.attrib['name'].lower() in ['eear', 'eearl']:
                    eear_base = int(elem.attrib['offset'],16) - 0x20
                    eear_size = int(elem.attrib['size'])
                if elem.attrib['name'].lower() == 'eecr':
                    eecr_base = int(elem.attrib['offset'],16) - 0x20
                if elem.attrib['name'].lower() == 'eedr':
                    eedr_base = int(elem.attrib['offset'],16) - 0x20
                if elem.attrib['name'].lower() == 'spmcsr' or \
                   elem.attrib['name'].lower() == 'spmcr':
                    spmcsr_base = int(elem.attrib['offset'],16)
                if elem.attrib['name'].lower() in ['osccal', 'osccal0', 'fosccal', 'sosccala']:
                    osccal_base = int(elem.attrib['offset'],16) - 0x20
                if elem.attrib.get('ocd-rw',"RW") in ["", "W"]:
                    crit_fields.append(elem.attrib['name'] +  \
                                        ("-Wonly" if (elem.attrib.get('ocd-rw',"RW") == "W") else ""))
                    if int(elem.attrib['offset'],16) not in masked:
                        masked.append(int(elem.attrib['offset'],16))
                else:
                    if elem.attrib.get('ocd-rw',"RW") == "R":
                        if int(elem.attrib['offset'],16) not in ronly:
                            ronly.append(int(elem.attrib['offset'],16))
                    if elem.attrib['name'] in [ 'DWDR', 'MONDR', 'OCDR', 'EUDR', 'UDR', 'UDR0',
                                                        'UDR1', 'UDR2', 'UDR3', 'UDR4', 'SPDR',
                                                        'SPDR0', 'SPDR1', 'SPDR2', 'LINDAT',
                                                        'UEDATX', 'UPDATX', 'DAC', 'DACL', 'DACH']:
                        crit_fields.append(elem.attrib['name'] + "-R/W")
            if elem.tag == 'bitfield':
                if elem.attrib['name'].lower() == 'dwen':
                    dwen_mask = elem.attrib['mask']
                if elem.attrib['name'].lower() == 'ocden':
                    ocden_mask = elem.attrib['mask']
                if elem.attrib['name'].lower() == 'bootrst':
                    bootrst_mask = elem.attrib['mask']
                if elem.attrib['name'].lower() == 'eesave':
                    eesave_mask = elem.attrib['mask']

            if elem.tag == 'register-group':
                if capture_bootrst_from_register_group(elem) is not None:
                    bootrst_base = capture_bootrst_from_register_group(elem)
                if capture_dwen_from_register_group(elem) is not None:
                    dwen_base = capture_dwen_from_register_group(elem)
                if capture_ocden_from_register_group(elem) is not None:
                    ocden_base = capture_ocden_from_register_group(elem)
                if capture_eesave_from_register_group(elem) is not None:
                    eesave_base = capture_eesave_from_register_group(elem)


    extra_fields += capture_field('address_size', determine_address_size(progmem_offset))
    if not shared_updi and 'ISP' not in interfaces:
        extra_fields += capture_field(DeviceInfoKeysAvr.PROG_CLOCK_KHZ, '1800')

    hv_comment = None
    if not hv_implementation:
        if shared_updi:
            hv_implementation = HV_IMPLEMENTATION_SHARED_UPDI
            hv_comment = f"    # Missing hv_implementation property in ATDF file\n    # Defaulting to {hv_implementation} for devices with UPDI fuse\n"
        else:
            hv_implementation = HV_IMPLEMENTATION_DEDICATED_UPDI
            hv_comment = f"    # Missing hv_implementation property in ATDF file\n    # Defaulting to {hv_implementation} for devices without UPDI fuse\n"

    if 'ISP' not in interfaces:
        if hv_comment:
            extra_fields += hv_comment
        extra_fields += capture_field(DeviceInfoKeysAvr.HV_IMPLEMENTATION, hv_implementation)

    if ocd_rev:
        extra_fields += "    'ocd_rev' : " + ocd_rev + ",\n"
    if ocd_base:
        extra_fields += "    'ocd_base' : " + ocd_base + ",\n"
    if eear_base:
        extra_fields += "    'eear_base' : " + "0x%02X" % eear_base + ",\n"
    if eear_size:
        extra_fields += "    'eear_size' : " + "%d" % eear_size + ",\n"
    if eecr_base:
        extra_fields += "    'eecr_base' : " + "0x%02X" % eecr_base + ",\n"
    if eedr_base:
        extra_fields += "    'eedr_base' : " + "0x%02X" % eedr_base + ",\n"
    if spmcsr_base:
        extra_fields += "    'spmcsr_base' : " + "0x%02X" % spmcsr_base + ",\n"
    if osccal_base:
        extra_fields += "    'osccal_base' : " + "0x%02X" % osccal_base + ",\n"
    if dwen_base:
        extra_fields += "    'dwen_base' : " + "%s" % dwen_base + ",\n"
    if dwen_mask:
        extra_fields += "    'dwen_mask' : " + "%s" % dwen_mask + ",\n"
    if ocden_base:
        extra_fields += "    'ocden_base' : " + "%s" % ocden_base + ",\n"
    if ocden_mask:
        extra_fields += "    'ocden_mask' : " + "%s" % ocden_mask + ",\n"
    if bootrst_base:
        extra_fields += "    'bootrst_base' : " + "%s" % bootrst_base + ",\n"
    if bootrst_mask:
        extra_fields += "    'bootrst_mask' : " + "%s" % bootrst_mask + ",\n"
    if eesave_base:
        extra_fields += "    'eesave_base' : " + "%s" % eesave_base + ",\n"
    if eesave_mask:
        extra_fields += "    'eesave_mask' : " + "%s" % eesave_mask + ",\n"
    if buf_per_page:
        extra_fields += "    'buffers_per_flash_page' : " + "%s" % buf_per_page + ",\n"
    if masked:
        extra_fields += "    'masked_registers' : [{}],\n".format(', '.join(hex(x) for x in sorted(masked)))
    if ronly:
        extra_fields += "    'ronly_registers' : [{}],\n".format(', '.join(hex(x) for x in sorted(ronly)))


    #pylint: disable=used-before-assignment
    extra_fields += capture_field(DeviceInfoKeysAvr.DEVICE_ID,
                            "0x{:02X}{:02X}{:02X}".format(signature[0], signature[1], signature[2]))

    # Replace "flash start" with "progmem_offset"
    if progmem_offset and int(progmem_offset, 16) > 0:
        memories[MemoryNames.FLASH][DeviceMemoryInfoKeys.ADDRESS] = progmem_offset

    # Build the output
    output += device_fields
    sorted_memories = collections.OrderedDict(sorted(memories.items()))
    for memory in sorted_memories:
        output += "\n    # {}\n".format(memory)
        output += capture_field('{}_{}_byte'.format(memory, DeviceMemoryInfoKeys.ADDRESS),
                                sorted_memories[memory][DeviceMemoryInfoKeys.ADDRESS])
        output += capture_field('{}_{}_bytes'.format(memory, DeviceMemoryInfoKeys.SIZE),
                                sorted_memories[memory][DeviceMemoryInfoKeys.SIZE])
        output += capture_field('{}_{}_bytes'.format(memory, DeviceMemoryInfoKeys.PAGE_SIZE),
                                sorted_memories[memory][DeviceMemoryInfoKeys.PAGE_SIZE])
        output += "    '{}_{}_bytes': {},\n".format(memory,
                                                    DeviceMemoryInfoKeys.READ_SIZE,
                                                    determine_read_size(memory))
        output += "    '{}_{}_bytes': {},\n".format(memory,
                                                    DeviceMemoryInfoKeys.WRITE_SIZE,
                                                    determine_write_size(memory,
                                                                         sorted_memories[memory][DeviceMemoryInfoKeys.PAGE_SIZE],
                                                                         devicename))
        output += "    '{}_{}': {},\n".format(memory, DeviceMemoryInfoKeys.CHIPERASE_EFFECT, determine_chiperase_effect(memory, architecture))
        output += "    '{}_{}': {},\n".format(memory, DeviceMemoryInfoKeys.ISOLATED_ERASE, determine_isolated_erase(memory, architecture) and 'ISP' not in interfaces)

    output += extra_fields
    output += "    'interface': '" + '+'.join(interfaces) + "'\n"
    return output, crit_fields

def main():
    """
    Main function for the harvest utility
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
    Harvests device data from a device data file (.atdf) for one device.

    The harvested data can be used to populate a device file in deviceinfo.devices
        '''))

    parser.add_argument("filename",
                        help="name (and path) of file to harvest data from or path to folder with atdf files"
                        )

    parser.add_argument('-i', '-interface', dest='interface',
                            help = "consider only ATDF files that mention this interface")

    arguments = parser.parse_args()

    if arguments.filename.lower().endswith('.atdf'):
        dict_content, _ = harvest_from_file(arguments.filename)
        if arguments.interface is None or arguments.interface.lower() in dict_content.lower():
            content = "\nfrom pymcuprog.deviceinfo.eraseflags import ChiperaseEffect\n\n"
            content += "DEVICE_INFO = {{\n{}}}".format(dict_content)
            print(content)
    else:
        all_critical_fields = []
        for file in os.listdir(arguments.filename):
            if os.path.splitext(file)[1].lower() != ".atdf":
                print("Skipping %s" %  file)
                continue
            print("Parsing %s" % os.path.splitext(file)[0])
            dict_content, crit_fields = harvest_from_file(arguments.filename + '/' + file)
            all_critical_fields.append([ os.path.splitext(file)[0],
                                             sorted(crit_fields)])
            if arguments.interface is None or arguments.interface.lower() in dict_content.lower():
                content = "\nfrom pymcuprog.deviceinfo.eraseflags import ChiperaseEffect\n\n"
                content += "DEVICE_INFO = {{\n{}}}".format(dict_content)
                with open(os.path.splitext(file)[0].lower() + '.py', 'w', encoding='utf-8') as f:
                    f.write(content)
        with open("critical-fields.txt", 'w', encoding='utf-8') as f:
            pprint.pp(sorted(all_critical_fields), stream=f)


if __name__ == "__main__":
    main()
