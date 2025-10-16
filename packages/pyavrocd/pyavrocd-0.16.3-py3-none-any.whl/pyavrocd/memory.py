"""
Memory module for the AVR GDB server
"""

# args, logging
from logging import getLogger

# debugger modules
from pyavrocd.errors import  FatalError
from pyavrocd.deviceinfo.devices.alldevices import dev_name

class Memory():
    """
    This class is responsible for access to all kinds of memory, for loading the flash memory,
    and for managing the flash cache.

    Flash cache is implemented as a growing bytearray. We start always at 0x0000 and fill empty
    spaces by 0xFF. _flashmem_start_prog points always to the first address from which we need to
    program flash memory. Neither the end of the flash cache nor _flashmem_start_prog need to be
    aligned with multi_page_size (page_size multiplied by buffers_per_flash_page).
    When programming, we will restart at a lower address or add 0xFF at the end.
    If the attribute lazy is set, then flashing is done leaving the bytes not fitting in a page
    unprogrammed. One can finalize loading when calling flash_pages with the lazy attribute set to False.
    """

    def __init__(self, dbg, mon):
        self.logger = getLogger('pyavrocd.memory')
        self.dbg = dbg
        self.mon = mon
        self._flash = bytearray() # bytearray starting at 0x0000
        # some device info that is needed throughout
        self._flash_start = self.dbg.memory_info.memory_info_by_name('flash')['address']
        self._flash_page_size = self.dbg.memory_info.memory_info_by_name('flash')['page_size']
        self._flash_size = self.dbg.memory_info.memory_info_by_name('flash')['size']
        self._multi_buffer = self.dbg.device_info.get('buffers_per_flash_page',1)
        self._masked_registers = self.dbg.device_info.get('masked_registers',[])
        self._ronly_registers = self.dbg.device_info.get('ronly_registers',[])
        self._multi_page_size = self._multi_buffer*self._flash_page_size
        self._sram_start = self.dbg.memory_info.memory_info_by_name('internal_sram')['address']
        self._sram_size = self.dbg.memory_info.memory_info_by_name('internal_sram')['size']
        self._eeprom_start = self.dbg.memory_info.memory_info_by_name('eeprom')['address']
        self._eeprom_size = self.dbg.memory_info.memory_info_by_name('eeprom')['size']
        self._flashmem_start_prog = 0
        self.lazy_loading = False
        self.programming_mode = False

    def init_flash(self):
        """
        Initialize flash by emptying it.
        """
        self._flash = bytearray()
        self._flashmem_start_prog = 0

    def is_flash_empty(self):
        """
        Return true if flash cache is empty.
        """
        return len(self._flash) == 0

    def flash_filled(self):
        """
        Return how many bytes have already be filled.
        """
        return len(self._flash)

    def readmem(self, addr, size):
        """
        Read a chunk of memory and return a bytestring or bytearray.
        The parameter addr and size should be hex strings.
        """
        iaddr, method, _ = self.mem_area(addr)
        isize = int(size, 16)
        return method(iaddr, isize)

    def writemem(self, addr, data):
        """
        Write a chunk of memory and return a reply string.
        The parameter addr should be a hex string.
        """
        iaddr, _, method = self.mem_area(addr)
        if not data:
            return "OK"
        response = method(iaddr, data)
        self.logger.debug("Result of writing: %s", response)
        if response is None:
            return "OK"
        return "E13"

    def mem_area(self, addr):
        """
        This function returns a triple consisting of the real address as an int, the read,
        and the write method. If illegal address section, give error message and return
        (0, lambda aadr, num: bytes([0xFF]*num), lambda *x: 'E13').
        For fuses, lockbits, signatures, and user signatures, access requests are ignored and
        dummy values are returned. The only exception is if one wants to write the signature
        bytes. In this case, it is compared with the signature of the MCU and a fatal error
        is raised when the signatures differ. This can be used to check for the right MCU
        by including the directive '#include <avr/signature.h>' in the source file.
        """
        addr_section = "00"
        if len(addr) == 6:
            if addr[0] == '8':
                addr_section = addr[:2]
                addr = addr[2:]
        iaddr = int(addr,16)
        self.logger.debug("Address section: %s",addr_section)
        if addr_section == "00": # flash
            if self.programming_mode:
                return(iaddr, self.flash_read, self.flash_write)
            return(iaddr, self.flash_read, lambda *x: 'E13')
        if addr_section == "80": # ram
            if not self.programming_mode:
                return(iaddr, self.sram_masked_read, self.sram_masked_write)
        if addr_section == "81": # eeprom
            return(iaddr, self.eeprom_read, self.eeprom_write)
        if addr_section == "82": # fuse
            self.logger.error("Fuses cannot be accessed: request ignored")
            return (0, lambda addr, num: bytes([0xFF]*num), lambda *x: None)
            #if self.programming_mode and self.dbg.get_iface() in ['jtag', 'updi']:
            #    return(iaddr, self.fuse_read, self.fuse_write)
        if addr_section == "83": #  lock
            self.logger.error("Lock bits cannot be accessed: request ignored")
            return (0, lambda addr, num: bytes([0xFF]*num), lambda *x: None)
            #if (self.programming_mode and self.dbg.get_iface() == 'jtag') or \
            #    self.dbg.get_iface() == 'updi':
            #    return(iaddr, self.lock_read, self.lock_write)
        if addr_section == "84": # signature
            self.logger.error("Signatures cannot be accessed: request ignored")
            return (0, lambda addr, num: bytes([0xFF]*num), self.compare_signatures)
            #if (self.programming_mode and self.dbg.get_iface() in ['jtag', 'updi']) \
            #  or self.dbg.get_iface() == 'debugwire':
            #    return(iaddr, self.sig_read, lambda *x: 'E13')
        if addr_section == "85":  # user signature
            self.logger.error("User signature cannot be accessed: request ignored")
            return (0, lambda addr, num: bytes([0xFF]*num), lambda *x: None)
            #if self.dbg.get_iface() in ['jtag', 'updi']:
            #    return(iaddr, self.usig_read, self.usig_write)
        self.logger.error("Illegal memtype in memory access operation at %s: %s",
                              addr, addr_section)
        return (0, lambda addr, num: bytes([0xFF]*num), lambda *x: 'E13')

    def sram_masked_read(self, addr, size):
        """
        Read a chunk from SRAM but leaving  out any masked registers. In theory,
        one could use the "Memory Read Masked" method of the AVR8 Generic protocol.
        However, there is no Python method implemented that does that for you.
        For this reason, we do it here step by step.
        """
        end = addr + size
        data = bytearray()
        for mr in sorted(self._masked_registers):
            if mr >= end or addr >= end:
                break
            if mr < addr:
                continue
            if addr < mr:
                data.extend(self.dbg.sram_read(addr, mr - addr))
            data.append(0x00)
            addr = mr + 1
        if addr < end:
            data.extend(self.dbg.sram_read(addr, end - addr))
        return data

    def sram_masked_write(self, addr, data):
        """
        Write a chunk to SRAM but leaving  out any read-only registers. If there is an
        attempt to write to a read-only register, spew out a warning message.
        """
        start = addr
        end = addr + len(data)
        for rr in sorted(self._ronly_registers):
            if rr >= end or addr >= end:
                break
            if rr < addr:
                continue
            if addr < rr:
                # write to SRAM from addr up to rr-1
                self.dbg.sram_write(addr, data[addr-start:rr-start])
            self.logger.warning("Not writing to 0x%X because it is write-protected", rr)
            addr = rr + 1
        if addr < end:
            # write remaining data
            self.dbg.sram_write(addr, data[addr-start:end-start])

    def flash_read(self, addr, size):
        """
        Read flash contents from cache that had been constructed during loading the file.
        It is faster and circumvents the problem that with some debuggers only page-sized
        access is possible. If there is nothing in the cache or it is explicitly disallowed,
        fall back to reading the flash page-wise (which is the only way supported by mEDBG).
        """
        self.logger.debug("Trying to read %d bytes starting at 0x%X", size, addr)
        if not self.mon.is_debugger_active():
            self.logger.error("Cannot read from memory when OCD is disabled")
            return bytearray([0xFF]*size)
        if self.mon.is_cache() and addr + size <= self.flash_filled():
            return self._flash[addr:addr+size]
        baseaddr = (addr // self._flash_page_size) * self._flash_page_size
        endaddr = addr + size
        pnum = ((endaddr - baseaddr) +  self._flash_page_size - 1) // self._flash_page_size
        self.logger.debug("No cache, request %d pages starting at 0x%X", pnum, baseaddr)
        response = bytearray()
        for p in range(pnum):
            response +=  self.dbg.flash_read(baseaddr + (p * self._flash_page_size),
                                                  self._flash_page_size)
        self.logger.debug("Response from page read: %s", response)
        response = response[addr-baseaddr:addr-baseaddr+size]
        return response

    def flash_read_word(self, addr):
        """
        Read one word at an even address from flash (LSB first!) and return it as a word value.
        """
        return(int.from_bytes(self.flash_read(addr, 2), byteorder='little'))

    #pylint: disable=useless-return
    def flash_write(self, addr, data):
        """
        This writes an arbitrary chunk of data to flash. If addr is lower than len(self._flash),
        the cache is cleared. This should do the right thing when loading is implemented with
        X-records.
        """
        if addr < len(self._flash):
            self.init_flash()
        self.store_to_cache(addr, data)
        self.flash_pages()
        return None

    def store_to_cache(self, addr, data):
        """
        Store chunks into the flash cache. Programming will take place later.
        """
        self.logger.debug("store_to_cache at %X", addr)
        if addr < len(self._flash):
            raise FatalError("Overlapping  flash areas at 0x%X" % addr)
        self._flash.extend(bytearray([0xFF]*(addr - len(self._flash) )))
        self._flash.extend(data)
        self.logger.debug("%s", self._flash)

    def flash_pages(self):
        """
        Write pages to flash memory, starting at _flashmem_start_prog up to len(self._flash)-1.
        Since programming takes place in chunks of size self._multi_page_size, beginning and end
        needs to be adjusted. At the end, we may add some 0xFFs.
        If mon.is_read_before_write() is true (read before write), the we will read a page
        before it is written.
        If it is nothing new, we skip. Otherwise, when "jtag", we check whether the page is blank.
        If not, the we need to erase this page by temporarily leaving progmode.
        This out of the way, we program.
        Optionally, after writing, we check whether we were successful.
        """
        startaddr = (self._flashmem_start_prog // self._multi_page_size) * self._multi_page_size
        if self.lazy_loading:
            roundup = 0
        else:
            roundup = self._multi_page_size - 1
        stopaddr = ((len(self._flash) + roundup) // self._multi_page_size) * self._multi_page_size
        pgaddr = startaddr
        give_info = stopaddr-startaddr > 2048
        proged = 0
        next_mile_stone = 2000
        self.logger.info("Flashing at 0x%X, length: %u ...", pgaddr, stopaddr-startaddr)
        while pgaddr < stopaddr:
            self.logger.debug("Flashing page starting at 0x%X", pgaddr)
            pagetoflash = self._flash[pgaddr:pgaddr + self._multi_page_size]
            currentpage = bytearray([])
            if self.mon.is_read_before_write() and not self.mon.is_erase_before_load():
                # interestingly, it is faster to read single pages than a multi-page chunk!
                for p in range(self._multi_buffer):
                    currentpage += self.dbg.flash_read(pgaddr+(p*self._flash_page_size),
                                                           self._flash_page_size, prog_mode=True)
            self.logger.debug("pagetoflash: %s", pagetoflash.hex())
            self.logger.debug("currentpage: %s", currentpage.hex())
            if currentpage[:len(pagetoflash)] == pagetoflash:
                self.logger.debug("Skip flashing page because already flashed at 0x%X", pgaddr)
            else:
                if not self.mon.is_erase_before_load() and (not currentpage or \
                  not self.dbg.device.avr.is_blank(currentpage)):
                    # will erase if necessary and return True if it did
                    self.logger.debug("Will now erase ...")
                    if self.dbg.device.erase_page(pgaddr, self.programming_mode):
                        self.logger.debug("Page at 0x%x erased", pgaddr)
                self.logger.debug("Flashing now from 0x%X to 0x%X", pgaddr, pgaddr+len(pagetoflash))
                pagetoflash.extend(bytearray([0xFF]*(self._multi_page_size-len(pagetoflash))))
                flashmemtype = self.dbg.device.avr.memtype_write_from_string('flash')
                # program flash page only when 'pagetoflash' is not blank
                # or memory has not been erased beforehand
                if not self.dbg.device.avr.is_blank(pagetoflash) or not self.mon.is_erase_before_load():
                    self.dbg.device.avr.write_memory_section(flashmemtype,
                                                                pgaddr,
                                                                pagetoflash,
                                                                self._flash_page_size,
                                                                allow_blank_skip=
                                                                self._multi_buffer == 1)
                # verify flash programming when verification is requested AND
                # (the pagetoflash is not blank or memory has not been erased before loading)
                if self.mon.is_verify() and (not self.dbg.device.avr.is_blank(pagetoflash) or \
                                                 not self.mon.is_erase_before_load()):
                    readbackpage = bytearray([])
                    for p in range(self._multi_buffer):
                        readbackpage += self.dbg.flash_read(pgaddr+(p*self._flash_page_size),
                                                                     self._flash_page_size,
                                                                      prog_mode=True)
                    self.logger.debug("pagetoflash: %s", pagetoflash.hex())
                    self.logger.debug("readback: %s", readbackpage.hex())
                    if readbackpage != pagetoflash:
                        raise FatalError("Flash verification error on page 0x{:X}".format(pgaddr))
            pgaddr += self._multi_page_size
            proged += self._multi_page_size
            if give_info and proged >= next_mile_stone:
                next_mile_stone += 2000
                self.logger.info("%d bytes flashed", proged)
        if self.lazy_loading:
            self._flashmem_start_prog = pgaddr
        else:
            self._flashmem_start_prog = len(self._flash)
        self.logger.info("... flashing done")

    def memory_map(self):
        """
        Return a memory map in XML format. Include registers, IO regs, and EEPROM in SRAM area
        """
        return ('l<memory-map><memory type="ram" start="0x{0:X}" length="0x{1:X}"/>' + \
                             '<memory type="flash" start="0x{2:X}" length="0x{3:X}">' + \
                             '<property name="blocksize">0x{4:X}</property>' + \
                             '</memory></memory-map>').format(0 + 0x800000, \
                              # (0x10000 + self._eeprom_start + self._eeprom_size),
                              0x60000, # is needed to read the other memory areas as well
                              self._flash_start, self._flash_size, self._multi_page_size)

    def fuse_read(self, addr, size):
        """
        Read fuses (does not work with debugWIRE)
        """
        try:
            resp = self.dbg.read_fuse(addr, size)
        except Exception as e:
            self.logger.error("Error reading fuses: %s", e)
            return bytearray([0xFF]*size)
        return bytearray(resp)

    def fuse_write(self, addr, data):
        """
        Write fuses (does not work with debugWIRE)
        """
        try:
            self.dbg.write_fuse(addr, data)
        except Exception as e:
            self.logger.error("Error writing fuses: %s", e)
            return 'E13'
        return None

    def lock_read(self, addr, size):
        """
        Read lock bits (does not work with debugWIRE)
        """
        try:
            resp = self.dbg.read_lock(addr, size)
        except Exception as e:
            self.logger.error("Error reading lockbits: %s", e)
            return bytearray([0xFF]*size)
        return bytearray(resp)

    def lock_write(self, addr, data):
        """
        Write lock bits (does not work with debugWIRE)
        """
        try:
            self.dbg.write_lock(addr, data)
        except Exception as e:
            self.logger.error("Error writing lockbits: %s", e)
            return 'E13'
        return None

    def sig_read(self, addr, size):
        """
        Read signature in a liberal way, i.e., throwing no errors
        """
        try:
            resp = self.dbg.read_sig(addr, size)
        except Exception as e:
            self.logger.error("Error reading the signature: %s", e)
            return bytearray([0xFF]*size)
        return bytearray(resp)

    def compare_signatures(self, addr, data):
        """
        Compare signature supplied by ELF file with the one specified on
        the command-line of the GDB server. If mismatch, report Fatal Error
        """
        _dummy = addr
        filesig = (data[2]<<16) + (data[1]<<8) + data[0]
        if filesig != self.dbg.device_info['device_id']:
            raise FatalError("File compiled for %s, current MCU is: %s" %
                                 (dev_name.get(filesig, "Unknown"),
                                    dev_name[self.dbg.device_info['device_id']]))
        self.logger.info("MCU signature read and verified")

    def usig_read(self, addr, size):
        """
        Read contents of user signature (does not work with debugWIRE)
        """
        try:
            resp = self.dbg.read_usig(addr, size)
        except Exception as e:
            self.logger.error("Error reading the user signature: %s", e)
            return bytearray([0xFF]*size)
        return bytearray(resp)

    def usig_write(self, addr, data):
        """
        Write user signature (does not work with debugWIRE)
        """
        try:
            self.dbg.write_usig(addr, data)
        except Exception as e:
            self.logger.error("Error writing the user signature: %s", e)
            return 'E13'
        return None

    def eeprom_read(self, address, numbytes):
        """
        Read EEPROM content from the AVR
        Needs to be handled here because depending on programm_mode, different memtypes have to be used

        :param address: absolute address to start reading from
        :param numbytes: number of bytes to read
        """
        self.logger.debug("Reading %d bytes from EEPROM at %X", numbytes, address)
        # The debugger protocols (via pymcuprog) use memory-types with zero-offsets
        # So the offset is subtracted here (and added later in the debugger)
        offset = (self.dbg.memory_info.memory_info_by_name('eeprom'))['address']
        return self.dbg.device.read(self.dbg.memory_info.memory_info_by_name('eeprom'), address-offset,
                                        numbytes, self.programming_mode)

    def eeprom_write(self, address, data):
        """
        Write EEPROM content to the AVR
        Needs to be handled here because depending on programm_mode, different memtypes have to be used

        :param address: absolute address in EEPROM to start writing
        :param data: content to store to EEPROM
        """
        self.logger.debug("Writing %d bytes to EEPROM at %X", len(data), address)
        # The debugger protocols (via pymcuprog) use memory-types with zero-offsets
        # So the offset is subtracted here (and added later in the debugger)
        offset = (self.dbg.memory_info.memory_info_by_name('eeprom'))['address']
        return self.dbg.device.write(self.dbg.memory_info.memory_info_by_name('eeprom'), address-offset,
                                         data, self.programming_mode)
