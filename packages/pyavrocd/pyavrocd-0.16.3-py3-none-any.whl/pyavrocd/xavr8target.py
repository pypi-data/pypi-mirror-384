"""
Device Specific Classes which use AVR8Protocol implementation
"""
from logging import getLogger

from pyedbglib.protocols.avr8protocol import Avr8Protocol
from pyedbglib.util import binary

from pymcuprog.deviceinfo import deviceinfo
from pymcuprog.deviceinfo.memorynames import MemoryNames
from pymcuprog.deviceinfo.deviceinfokeys import DeviceInfoKeysAvr, DeviceMemoryInfoKeys

from pymcuprog.avr8target import TinyXAvrTarget, TinyAvrTarget,\
     MegaAvrJtagTarget, XmegaAvrTarget, AvrDevice



class XTinyXAvrTarget(TinyXAvrTarget):
    """
    Class handling sessions with TinyX AVR targets using the AVR8 generic protocol
    """
    def __init__(self, transport):
        super().__init__(transport)
        self.logger_loc = getLogger('pyavrocd.tinyxtarget')

    # The next two methods are needed because different targets access the registers
    # in different ways: TinyX and XMega have a regfile mem type, the others have to access
    # the registers as part of their SRAM address space.
    def regfile_read(self):
        """
        Reads out the AVR register file (R0::R31)

        :return: 32 bytes of register file content as bytearray
        """
        self.logger_loc.debug("Reading register file")
        return self.protocol.regfile_read()

    def regfile_write(self, regs):
        """
        Writes the AVR register file (R0::R31)

        :param data: 32 byte register file content as bytearray
        :raises ValueError: if 32 bytes are not given
        """
        self.logger_loc.debug("Writing register file")
        self.protocol.regfile_write(regs)

    def statreg_read(self):
        """
        Reads SREG

        :returns: 1 Byte of SREG
        :rtype: bytearray
        """
        return self.protocol.memory_read(Avr8Protocol.AVR8_MEMTYPE_OCD,
                                             Avr8Protocol.AVR8_MEMTYPE_OCD_SREG, 1)

    def statreg_write(self, data):
        """
        Writes SREG

        """
        self.protocol.memory_write(Avr8Protocol.AVR8_MEMTYPE_OCD,
                                       Avr8Protocol.AVR8_MEMTYPE_OCD_SREG, data)

    def stack_pointer_write(self,data):
        """
        Writes the stack pointer
        """
        self.protocol.memory_write(Avr8Protocol.AVR8_MEMTYPE_OCD, 0x18, data)

    def hardware_breakpoint_set(self, num, address):
        """
        Sets one hardware breakpoint <num>

        :param num: number of breakpoint 1-3
        :param address: Address to break at
        :type address: int
        """
        if num < 1 or num > 1:
            self.logger.error("Tried to set hardware breakpoint %d at 0x%X on JTAG target",
                                num, address)
            return 0
        resp = self.protocol.jtagice3_command_response(
            bytearray([Avr8Protocol.CMD_AVR8_HW_BREAK_SET, Avr8Protocol.CMD_VERSION0, 1, num]) +
            binary.pack_le32(address) +
            bytearray([3]))
        return self.protocol.check_response(resp)


    def hardware_breakpoint_clear(self, num):
        """
        Clears the hardware breakpoint <num>
        """
        if num < 1 or num > 1:
            self.logger.error("Tried to clear hardware breakpoint %d on JTAG target",
                                num)
            return 0
        resp = self.protocol.jtagice3_command_response(
            bytearray([Avr8Protocol.CMD_AVR8_HW_BREAK_CLEAR, Avr8Protocol.CMD_VERSION0, num]))
        return self.protocol.check_response(resp)



class XTinyAvrTarget(TinyAvrTarget):
    """
    Implements Tiny AVR (debugWIRE) functionality of the AVR8 protocol
    """

    def __init__(self, transport):
        super().__init__(transport)
        self.logger_loc = getLogger('pyavrocd.tinytarget')

        # next lines are copied from TinyXAvrTarget
        if transport.device.product_string.lower().startswith('edbg'):
            # This is a workaround for FW3G-158 which has not been fixed for EDBG (fixed in common,
            # but no new EDBG firmware has/will be built)
            self.max_read_chunk_size = 256

    def setup_debug_session(self, **kwargs):
        """
        Sets up a debugging session on an Tiny AVR (debugwire)
        """
        _dummy = kwargs
        self.protocol.set_variant(Avr8Protocol.AVR8_VARIANT_TINYOCD)
        self.protocol.set_function(Avr8Protocol.AVR8_FUNC_DEBUGGING)
        self.protocol.set_interface(Avr8Protocol.AVR8_PHY_INTF_DW)

    #pylint: disable=arguments-differ
    def memtype_read_from_string(self, memtype_string):
        """
        Maps from a string to an AVR memtype taking into account the constraints for
        memory in the NVM mode for reading.
        """
        memtype = AvrDevice.memtype_read_from_string(memtype_string)
        if memtype == Avr8Protocol.AVR8_MEMTYPE_CALIBRATION_SIGNATURE:
            memtype = Avr8Protocol.AVR8_MEMTYPE_SIGNATURE
        return memtype

    def memtype_write_from_string(self, memtype_string):
        """
        Maps from a string to an avr8 memtype for writes

        :param memtype_string: Friendly name of memory
        :type memtype_string: str
        :returns: Memory type identifier as defined in the protocol
        :rtype: int
        """
        return self.memtype_read_from_string(memtype_string)

    def switch_to_progmode(self):
        """
        In general, we would switch to programming mode. However, for debugWIRE,
        prog mode or deb mode do not make a difference.
        """
        #self.protocol.enter_progmode()

    def switch_to_debmode(self):
        """
        In general, we would switch to debugging mode. However, for debugWIRE,
        prog mode or deb mode do not make a difference.
        """
        #self.protocol.leave_progmode()

    def attach(self):
        """
        For debugWIRE, we will attach to the OCD just once.
        """
        self.protocol.attach()

    def setup_config(self, device_info):
        """
        Sets up the device config for a tiny AVR device

        :param device_info: Target device information as returned
                            by deviceinfo.deviceinfo.getdeviceinfo
        :type device_info: dict
        """
        if device_info is None:
            device_info = {}

        # Parse the device info for memory descriptions
        device_memory_info = deviceinfo.DeviceMemoryInfo(device_info)

        flash_info = device_memory_info.memory_info_by_name(MemoryNames.FLASH)
        eeprom_info = device_memory_info.memory_info_by_name(MemoryNames.EEPROM)
        sram_info = device_memory_info.memory_info_by_name(MemoryNames.INTERNAL_SRAM)
        # Extract settings
        fl_page_size = flash_info[DeviceMemoryInfoKeys.PAGE_SIZE]
        fl_size = flash_info[DeviceMemoryInfoKeys.SIZE]
        fl_base = flash_info[DeviceMemoryInfoKeys.ADDRESS]
        sram_base = sram_info[DeviceMemoryInfoKeys.ADDRESS]
        ee_page_size = eeprom_info[DeviceMemoryInfoKeys.PAGE_SIZE]
        ee_size = eeprom_info[DeviceMemoryInfoKeys.SIZE]
        ocd_addr = device_info.get(DeviceInfoKeysAvr.OCD_BASE)
        ocd_rev = device_info.get('ocd_rev')
        pagebuffers_per_flash_block = device_info.get('buffers_per_flash_page',1)
        eear_size = device_info.get('eear_size')
        eearh_addr = device_info.get('eear_base') + eear_size - 1
        eearl_addr = device_info.get('eear_base')
        eecr_addr = device_info.get('eecr_base')
        eedr_addr = device_info.get('eedr_base')
        spmcsr_addr = device_info.get('spmcsr_base')
        osccal_addr = device_info.get('osccal_base')

        # Setup device structure and write to tool
        # TINY_FLASH_PAGE_BYTES (2@0x00)
        devdata = bytearray([fl_page_size & 0xff, 0])
        # TINY_FLASH_BYTES (4@0x02)
        devdata += bytearray([fl_size & 0xFF, (fl_size >> 8) & 0xFF,
                                  (fl_size >> 16) & 0xFF, (fl_size >> 24) & 0xFF])
        # TINY_FLASH_BASE (4@0x06)
        devdata += bytearray([fl_base & 0xFF, (fl_base >> 8) & 0xFF,
                                  (fl_base >> 16) & 0xFF, (fl_base >> 24) & 0xFF])
        # TINY_BOOT_BASE (4@0x0A)
        boot_base = fl_size - fl_page_size # as is done for MegaAvr
        devdata += bytearray([boot_base & 0xFF, (boot_base >> 8) & 0xFF,
                                  (boot_base >> 16) & 0xFF, (boot_base >> 24) & 0xFF])
        # TINY_SRAM_BASE (2@0x0E)
        devdata += bytearray([sram_base & 0xff, (sram_base >> 8) & 0xff])
        # TINY_EEPROM_BYTES (2@0x10)
        devdata += bytearray([ee_size & 0xff, (ee_size >> 8) & 0xff])
        # TINY_EEPROM_PAGE_BYTES (1@0x12)
        devdata += bytearray([ee_page_size])
        # TINY_OCD_REVISION (1@0x13)
        devdata += bytearray([ocd_rev])
        # TINY_PAGEBUFFERS_PER_FLASH_BLOCK
        devdata += bytearray([pagebuffers_per_flash_block])
        # 3 byte gap (3@0x15)
        devdata += bytearray([0, 0, 0])
        # TINY_OCD_MODULE_ADDRESS (1@0x18)
        devdata += bytearray([ocd_addr & 0xff])
        # TINY_EEARH_BASE (1@0x19)
        devdata += bytearray([eearh_addr & 0xFF])
        # TINY_EEARL_BASE (1@0x1A)
        devdata += bytearray([eearl_addr & 0xFF])
        # TINY_EECR_BASE (1@0x1B)
        devdata += bytearray([eecr_addr & 0xFF])
        # TINY_EEDR_BASE (1@0x1C)
        devdata += bytearray([eedr_addr & 0xFF])
        # TINY_SPMCSR_BASE (1@0x1D)
        devdata += bytearray([spmcsr_addr & 0xFF])
        # TINY_OSCCAL_BASE (1@0x1E)
        devdata += bytearray([osccal_addr & 0xFF])

        self.logger_loc.debug("Write all device data: %s",
                              [devdata.hex()[i:i+2] for i in range(0, len(devdata.hex()), 2)])
        self.protocol.write_device_data(devdata)


    def statreg_read(self):
        """
        Reads out SREG

        :return: 1 byte of status register
        """
        return self.protocol.memory_read(Avr8Protocol.AVR8_MEMTYPE_SRAM, 0x5F, 1)


    def statreg_write(self, data):
        """
        Writes byte to SREG
        :param: 1 byte of data

        """
        return self.protocol.memory_write(Avr8Protocol.AVR8_MEMTYPE_SRAM, 0x5F, data)


    def regfile_read(self):
        """
        Reads out the AVR register file (R0::R31)

        :return: 32 bytes of register file content as bytearray
        """
        return self.protocol.memory_read(Avr8Protocol.AVR8_MEMTYPE_SRAM, 0, 32)

    def regfile_write(self, regs):
        """
        Writes the AVR register file (R0::R31)

        :param data: 32 byte register file content as bytearray
        :raises ValueError: if 32 bytes are not given
        """
        return self.protocol.memory_write(Avr8Protocol.AVR8_MEMTYPE_SRAM, 0, regs)

    def stack_pointer_read(self):
        """
        Reads the stack pointer

        :returns: Stack pointer
        :rtype: bytearray
        """
        return self.protocol.memory_read(Avr8Protocol.AVR8_MEMTYPE_SRAM, 0x5D, 0x02)

    def stack_pointer_write(self, data):
        """
        Writes the stack pointer

        :param data: 2 byte as bytearray
        :raises ValueError: if 2 bytes are not given
        """
        return self.protocol.memory_write(Avr8Protocol.AVR8_MEMTYPE_SRAM, 0x5D, data)

    def hardware_breakpoint_set(self, num, address):
        """
        Sets one hardware breakpoint <num>

        :param num: number of breakpoint 1-3
        :param address: Address to break at
        :type address: int
        """
        self.logger.error("Tried to set hardware breakpoint %d at 0x%X on debugWIRE target",
                              num, address)
        return 0


    def hardware_breakpoint_clear(self, num):
        """
        Clears the hardware breakpoint <num>
        """
        self.logger.error("Tried to clear hardware breakpoint %d on debugWIRE target",
                              num)
        return 0


    def breakpoint_clear(self):
        """
        Is needed in stop_debugging - should not be there!
        """
        return 0


class XMegaAvrJtagTarget(MegaAvrJtagTarget):
    """
    Implements Mega AVR (JTAG) functionality of the AVR8 protocol
    """

    def __init__(self, transport):
        super().__init__(transport)
        self.logger_loc = getLogger('pyavrocd.megatarget')

    #pylint: disable=arguments-differ
    def memtype_read_from_string(self, memtype_string):
        """
        Maps from a string to an AVR memtype taking into account the constraints for
        memory in the NVM mode for reading.
        """
        memtype = AvrDevice.memtype_read_from_string(memtype_string)
        if memtype == Avr8Protocol.AVR8_MEMTYPE_CALIBRATION_SIGNATURE:
            memtype = Avr8Protocol.AVR8_MEMTYPE_SIGNATURE
        return memtype

    def memtype_write_from_string(self, memtype_string):
        """
        Maps from a string to an AVR memtype taking into account the constraints for
        memory in the NVM mode for writing.
        """
        return self.memtype_read_from_string(memtype_string)

    def switch_to_progmode(self):
        """
        This is a horrible kludge to get safe mode switches on
        SNAP and PICkit4. On these tools, you HAVE TO restart the
        session in order to get safe mode switching. Everything else
        leads to interesting errors.
        """
        self.protocol.detach()
        self.deactivate_physical()
        self.activate_physical()
        self.protocol.enter_progmode()

    def switch_to_debmode(self):
        """
        Similar thing, but worse. You have to enter and leave progmode
        in order to make a safe transition to debug mode. The attach
        function often does not work!
        """
        self.switch_to_progmode()
        self.protocol.leave_progmode()

    def attach(self):
        """
        For JTAG targets, the methods 'switch_to_progmode' and 'switch_to_debmode' make
        sure that we are attached. So this is a no-op.
        """

    def setup_debug_session(self, clkprg=200, clkdeb=1000):
        """
        Sets up a programming session on an Mega AVR (JTAG)
        """
        self.logger.debug("Setting up debug session for JTAG target")
        self.protocol.set_variant(Avr8Protocol.AVR8_VARIANT_MEGAOCD)
        self.protocol.set_function(Avr8Protocol.AVR8_FUNC_DEBUGGING)
        self.protocol.set_interface(Avr8Protocol.AVR8_PHY_INTF_JTAG)
        self.protocol.set_le16(Avr8Protocol.AVR8_CTXT_PHYSICAL, Avr8Protocol.AVR8_PHY_MEGA_PRG_CLK, clkprg)
        self.protocol.set_le16(Avr8Protocol.AVR8_CTXT_PHYSICAL, Avr8Protocol.AVR8_PHY_MEGA_DBG_CLK, clkdeb)

    # setup_config is done in the super class
    # However, it seems to be wrong. Instead of IO register addresses RAM addresses
    # are used. I guess the version below is the correct one!
    def setup_config(self, device_info):
        """
        Sets up the device config for a tiny AVR device

        :param device_info: Target device information as returned
                            by deviceinfo.deviceinfo.getdeviceinfo
        :type device_info: dict
        """
        if device_info is None:
            device_info = {}

        # Parse the device info for memory descriptions
        device_memory_info = deviceinfo.DeviceMemoryInfo(device_info)

        flash_info = device_memory_info.memory_info_by_name(MemoryNames.FLASH)
        eeprom_info = device_memory_info.memory_info_by_name(MemoryNames.EEPROM)
        sram_info = device_memory_info.memory_info_by_name(MemoryNames.INTERNAL_SRAM)
        # Extract settings
        fl_page_size = flash_info[DeviceMemoryInfoKeys.PAGE_SIZE]
        fl_size = flash_info[DeviceMemoryInfoKeys.SIZE]
        fl_base = flash_info[DeviceMemoryInfoKeys.ADDRESS]
        sram_base = sram_info[DeviceMemoryInfoKeys.ADDRESS]
        ee_page_size = eeprom_info[DeviceMemoryInfoKeys.PAGE_SIZE]
        ee_size = eeprom_info[DeviceMemoryInfoKeys.SIZE]
        ocd_addr = device_info.get(DeviceInfoKeysAvr.OCD_BASE)
        ocd_rev = device_info.get('ocd_rev')
        pagebuffers_per_flash_block = device_info.get('buffers_per_flash_page',1)
        eear_size = device_info.get('eear_size')
        eearh_addr = device_info.get('eear_base') + eear_size - 1
        eearl_addr = device_info.get('eear_base')
        eecr_addr = device_info.get('eecr_base')
        eedr_addr = device_info.get('eedr_base')
        spmcsr_addr = device_info.get('spmcsr_base')
        osccal_addr = device_info.get('osccal_base')

        # Setup device structure and write to tool

        # TMEGA_FLASH_PAGE_BYTES (2@0x00)
        devdata = bytearray([fl_page_size & 0xff, (fl_page_size >> 8) & 0xff])

        # TMEGA_FLASH_BYTES (4@0x02)
        devdata += bytearray([fl_size & 0xFF, (fl_size >> 8) & 0xFF,
                                  (fl_size >> 16) & 0xFF, (fl_size >> 24) & 0xFF])

        # TMEGA_FLASH_BASE (4@0x06)
        devdata += bytearray([fl_base & 0xFF, (fl_base >> 8) & 0xFF,
                                  (fl_base >> 16) & 0xFF, (fl_base >> 24) & 0xFF])

        # TMEGA_BOOT_BASE (4@0x0A)
        boot_base = fl_size - fl_page_size # as is done for MegaAvr
        devdata += bytearray([boot_base & 0xFF, (boot_base >> 8) & 0xFF,
                                  (boot_base >> 16) & 0xFF, (boot_base >> 24) & 0xFF])

        # TMEGA_SRAM_BASE (2@0x0E)
        devdata += bytearray([sram_base & 0xff, (sram_base >> 8) & 0xff])

        # TMEGA_EEPROM_BYTES (2@0x10)
        devdata += bytearray([ee_size & 0xff, (ee_size >> 8) & 0xff])

        # TMEGA_EEPROM_PAGE_BYTES (1@0x12)
        devdata += bytearray([ee_page_size])

        # TMEGA_OCD_REVISION (1@0x13)
        devdata += bytearray([ocd_rev])

        # TMEGA_PAGEBUFFERS_PER_FLASH_BLOCK
        devdata += bytearray([pagebuffers_per_flash_block])

        # 3 byte gap (3@0x15)
        devdata += bytearray([0, 0, 0])

        # TMEGA_OCD_MODULE_ADDRESS (1@0x18)
        devdata += bytearray([ocd_addr & 0xff])

        # TMEGA_EEARH_BASE (1@0x19)
        devdata += bytearray([eearh_addr & 0xFF])

        # TMEGA_EEARL_BASE (1@0x1A)
        devdata += bytearray([eearl_addr & 0xFF])

        # TMEGA_EECR_BASE (1@0x1B)
        devdata += bytearray([eecr_addr & 0xFF])

        # TMEGA_EEDR_BASE (1@0x1C)
        devdata += bytearray([eedr_addr & 0xFF])

        # TMEGA_SPMCSR_BASE (1@0x1D)
        devdata += bytearray([spmcsr_addr & 0xFF])

        # TMEGA_OSCCAL_BASE (1@0x1E)
        devdata += bytearray([osccal_addr & 0xFF])

        self.logger_loc.debug("Write all device data: %s",
                              [devdata.hex()[i:i+2] for i in range(0, len(devdata.hex()), 2)])
        self.protocol.write_device_data(devdata)



    def regfile_read(self):
        """
        Reads out the AVR register file (R0::R31)

        :return: 32 bytes of register file content as bytearray
        """
        return self.protocol.memory_read(Avr8Protocol.AVR8_MEMTYPE_SRAM, 0, 32)

    def regfile_write(self, regs):
        """
        Writes the AVR register file (R0::R31)

        :param data: 32 byte register file content as bytearray
        :raises ValueError: if 32 bytes are not given
        """
        return self.protocol.memory_write(Avr8Protocol.AVR8_MEMTYPE_SRAM, 0, regs)

    def statreg_read(self):
        """
        Reads out SREG

        :return: 1 byte of status register
        """
        return self.protocol.memory_read(Avr8Protocol.AVR8_MEMTYPE_SRAM, 0x5F, 1)


    def statreg_write(self, data):
        """
        Writes byte to SREG
        :param: 1 byte of data

        """
        return self.protocol.memory_write(Avr8Protocol.AVR8_MEMTYPE_SRAM, 0x5F, data)

    def stack_pointer_read(self):
        """
        Reads the stack pointer

        :returns: Stack pointer
        :rtype: bytearray
        """
        return self.protocol.memory_read(Avr8Protocol.AVR8_MEMTYPE_SRAM, 0x5D, 0x02)

    def stack_pointer_write(self, data):
        """
        Writes the stack pointer

        :param data: 2 byte as bytearray
        :raises ValueError: if 2 bytes are not given
        """
        return self.protocol.memory_write(Avr8Protocol.AVR8_MEMTYPE_SRAM, 0x5D, data)

    def hardware_breakpoint_set(self, num, address):
        """
        Sets one hardware breakpoint <num>

        :param num: number of breakpoint 1-3
        :param address: Address to break at
        :type address: int
        """
        if num < 1 or num > 3:
            self.logger.error("Tried to set hardware breakpoint %d at 0x%X on JTAG target",
                                num, address)
            return 0
        resp = self.protocol.jtagice3_command_response(
            bytearray([Avr8Protocol.CMD_AVR8_HW_BREAK_SET, Avr8Protocol.CMD_VERSION0, 1, num]) +
            binary.pack_le32(address) +
            bytearray([3]))
        return self.protocol.check_response(resp)


    def hardware_breakpoint_clear(self, num):
        """
        Clears the hardware breakpoint <num>
        """
        if num < 1 or num > 3:
            self.logger.error("Tried to clear hardware breakpoint %d on JTAG target",
                                num)
            return 0
        resp = self.protocol.jtagice3_command_response(
            bytearray([Avr8Protocol.CMD_AVR8_HW_BREAK_CLEAR, Avr8Protocol.CMD_VERSION0, num]))
        return self.protocol.check_response(resp)

    def breakpoint_clear(self):
        """
        Is needed in stop_debugging and will clear all hardware breakpoints
        """
        for hwbp in range(1,4):
            self.hardware_breakpoint_clear(hwbp)


class XXmegaAvrTarget(XmegaAvrTarget):
    """
    Implements XMEGA (PDI) functionality of the AVR8 protocol
    """

    def __init__(self, transport):
        super().__init__(transport)
        self.logger_loc = getLogger('pyavrocd.xmegatarget')


    def setup_debug_session(self):
        """
        Sets up a debugging session on an XMEGA AVR
        """
        self.protocol.set_variant(Avr8Protocol.AVR8_VARIANT_XMEGA)
        self.protocol.set_function(Avr8Protocol.AVR8_FUNC_DEBUGGING)
        self.protocol.set_interface(Avr8Protocol.AVR8_PHY_INTF_PDI)

    # The next two methods are needed because different targets access the registers
    # in different ways: TinyX and XMega have a regfile mem type, the others have to access
    # the registers as part of their SRAM address space.
    def regfile_read(self):
        """
        Reads out the AVR register file (R0::R31)

        :return: 32 bytes of register file content as bytearray
        """
        self.logger_loc.debug("Reading register file")
        return self.protocol.regfile_read()

    def regfile_write(self, regs):
        """
        Writes the AVR register file (R0::R31)

        :param data: 32 byte register file content as bytearray
        :raises ValueError: if 32 bytes are not given
        """
        self.logger_loc.debug("Writing register file")
        return self.protocol.regfile_write(regs)
