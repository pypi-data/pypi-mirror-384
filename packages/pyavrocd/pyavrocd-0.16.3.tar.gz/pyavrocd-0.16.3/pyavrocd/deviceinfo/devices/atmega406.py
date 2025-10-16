
from pymcuprog.deviceinfo.eraseflags import ChiperaseEffect

DEVICE_INFO = {
    'name': 'atmega406',
    'architecture': 'avr8',

    # eeprom
    'eeprom_address_byte': 0x0000,
    'eeprom_size_bytes': 0x0200,
    'eeprom_page_size_bytes': 0x04,
    'eeprom_read_size_bytes': 0x01,
    'eeprom_write_size_bytes': 0x01,
    'eeprom_chiperase_effect': ChiperaseEffect.CONDITIONALLY_ERASED_AVR,
    'eeprom_isolated_erase': True,

    # flash
    'flash_address_byte': 0x0000,
    'flash_size_bytes': 0xa000,
    'flash_page_size_bytes': 0x80,
    'flash_read_size_bytes': 0x02,
    'flash_write_size_bytes': 0x80,
    'flash_chiperase_effect': ChiperaseEffect.ALWAYS_ERASED,
    'flash_isolated_erase': True,

    # fuses
    'fuses_address_byte': 0,
    'fuses_size_bytes': 0x0002,
    'fuses_page_size_bytes': 0x01,
    'fuses_read_size_bytes': 0x01,
    'fuses_write_size_bytes': 0x01,
    'fuses_chiperase_effect': ChiperaseEffect.NOT_ERASED,
    'fuses_isolated_erase': True,

    # internal_sram
    'internal_sram_address_byte': 0x0100,
    'internal_sram_size_bytes': 0x0800,
    'internal_sram_page_size_bytes': 0x01,
    'internal_sram_read_size_bytes': 0x01,
    'internal_sram_write_size_bytes': 0x01,
    'internal_sram_chiperase_effect': ChiperaseEffect.NOT_ERASED,
    'internal_sram_isolated_erase': True,

    # lockbits
    'lockbits_address_byte': 0,
    'lockbits_size_bytes': 0x0001,
    'lockbits_page_size_bytes': 0x01,
    'lockbits_read_size_bytes': 0x01,
    'lockbits_write_size_bytes': 0x01,
    'lockbits_chiperase_effect': ChiperaseEffect.ALWAYS_ERASED,
    'lockbits_isolated_erase': True,

    # signatures
    'signatures_address_byte': 0,
    'signatures_size_bytes': 3,
    'signatures_page_size_bytes': 0x01,
    'signatures_read_size_bytes': 0x01,
    'signatures_write_size_bytes': 0x00,
    'signatures_chiperase_effect': ChiperaseEffect.NOT_ERASED,
    'signatures_isolated_erase': True,

    # Some extra AVR specific fields
    'address_size': '16-bit',
    'prog_clock_khz': 1800,
    # Missing hv_implementation property in ATDF file
    # Defaulting to 1 for devices without UPDI fuse
    'hv_implementation': 1,
    'ocd_rev' : 3,
    'ocd_base' : 0x31,
    'eear_base' : 0x21,
    'eear_size' : 2,
    'eecr_base' : 0x1F,
    'eedr_base' : 0x20,
    'spmcsr_base' : 0x57,
    'osccal_base' : 0x46,
    'ocden_base' : 0x01,
    'ocden_mask' : 0x02,
    'bootrst_base' : 0x00,
    'bootrst_mask' : 0x08,
    'eesave_base' : 0x00,
    'eesave_mask' : 0x40,
    'masked_registers' : [0x51],
    'ronly_registers' : [0x20, 0x23, 0x35, 0x36, 0x3b, 0x3c, 0x60, 0x62, 0x7a, 0xb9, 0xbc, 0xe0, 0xe1, 0xe2, 0xe3, 0xe5, 0xf2, 0xf8],
    'device_id': 0x1E9507,
    'interface': 'HVPP+JTAG'
}