
from pymcuprog.deviceinfo.eraseflags import ChiperaseEffect

DEVICE_INFO = {
    'name': 'attiny13',
    'architecture': 'avr8',

    # eeprom
    'eeprom_address_byte': 0x0000,
    'eeprom_size_bytes': 0x0040,
    'eeprom_page_size_bytes': 0x04,
    'eeprom_read_size_bytes': 0x01,
    'eeprom_write_size_bytes': 0x01,
    'eeprom_chiperase_effect': ChiperaseEffect.CONDITIONALLY_ERASED_AVR,
    'eeprom_isolated_erase': False,

    # flash
    'flash_address_byte': 0x0000,
    'flash_size_bytes': 0x0400,
    'flash_page_size_bytes': 0x20,
    'flash_read_size_bytes': 0x02,
    'flash_write_size_bytes': 0x20,
    'flash_chiperase_effect': ChiperaseEffect.ALWAYS_ERASED,
    'flash_isolated_erase': False,

    # fuses
    'fuses_address_byte': 0,
    'fuses_size_bytes': 0x0002,
    'fuses_page_size_bytes': 0x01,
    'fuses_read_size_bytes': 0x01,
    'fuses_write_size_bytes': 0x01,
    'fuses_chiperase_effect': ChiperaseEffect.NOT_ERASED,
    'fuses_isolated_erase': False,

    # internal_sram
    'internal_sram_address_byte': 0x0060,
    'internal_sram_size_bytes': 0x0040,
    'internal_sram_page_size_bytes': 0x01,
    'internal_sram_read_size_bytes': 0x01,
    'internal_sram_write_size_bytes': 0x01,
    'internal_sram_chiperase_effect': ChiperaseEffect.NOT_ERASED,
    'internal_sram_isolated_erase': False,

    # lockbits
    'lockbits_address_byte': 0,
    'lockbits_size_bytes': 0x0001,
    'lockbits_page_size_bytes': 0x01,
    'lockbits_read_size_bytes': 0x01,
    'lockbits_write_size_bytes': 0x01,
    'lockbits_chiperase_effect': ChiperaseEffect.ALWAYS_ERASED,
    'lockbits_isolated_erase': False,

    # signatures
    'signatures_address_byte': 0,
    'signatures_size_bytes': 3,
    'signatures_page_size_bytes': 0x01,
    'signatures_read_size_bytes': 0x01,
    'signatures_write_size_bytes': 0x00,
    'signatures_chiperase_effect': ChiperaseEffect.NOT_ERASED,
    'signatures_isolated_erase': False,

    # Some extra AVR specific fields
    'address_size': '16-bit',
    'ocd_rev' : 0,
    'ocd_base' : 0x2e,
    'eear_base' : 0x1E,
    'eear_size' : 1,
    'eecr_base' : 0x1C,
    'eedr_base' : 0x1D,
    'spmcsr_base' : 0x57,
    'osccal_base' : 0x31,
    'dwen_base' : 0x01,
    'dwen_mask' : 0x08,
    'eesave_base' : 0x00,
    'eesave_mask' : 0x40,
    'masked_registers' : [0x4e],
    'ronly_registers' : [0x26, 0x28, 0x36, 0x41, 0x46, 0x51, 0x57, 0x58, 0x5a],
    'device_id': 0x1E9007,
    'interface': 'ISP+HVSP+debugWIRE'
}