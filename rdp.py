# coding: utf8

import pyb
import stm

# cmsis/devinc/stm32f405xx.h
# Peripheral memory map
PERIPH_BASE = 0x40000000
AHB1PERIPH_BASE = PERIPH_BASE + 0x00020000
FLASH = AHB1PERIPH_BASE + 0x3C00
# Bits definition for FLASH_OPTCR register
FLASH_OPTCR_OPTLOCK = 0x00000001
FLASH_OPTCR_OPTSTRT = 0x00000002
# Bits definition for FLASH_SR register
FLASH_SR_SOP = 0x00000002
FLASH_SR_WRPERR = 0x00000010
FLASH_SR_PGAERR = 0x00000020
FLASH_SR_PGPERR = 0x00000040
FLASH_SR_PGSERR = 0x00000080
FLASH_SR_BSY = 0x00010000
# Bits definition for FLASH_CR register
FLASH_CR_LOCK = 0x80000000

# cmsis/devinc/stm32f405xx.h
# FLASH Registers: typedef struct FLASH_TypeDef
FLASH_ACR = 0x00      # FLASH access control register
FLASH_KEYR = 0x04     # FLASH key register
FLASH_OPTKEYR = 0x08  # FLASH option key register
FLASH_SR = 0x0C       # FLASH status register
FLASH_CR = 0x10       # FLASH control register
FLASH_OPTCR = 0x14    # FLASH option control register
FLASH_OPTCR1 = 0x14   # FLASH option control register 1

# stm32f4xx_hal_def.h
HAL_OK = 0x00
HAL_MAX_DELAY = 0xFFFFFFFF

# hal/inc/stm32f4xx_hal_flash.h
OPTCR_BYTE0_ADDRESS = 0x40023C14  # OPTCR register byte 0 (Bits[7:0]) base address
OPTCR_BYTE1_ADDRESS = 0x40023C15  # OPTCR register byte 1 (Bits[15:8]) base address
# Bits definition for FLASH_OPTCR register
# FLASH Keys
FLASH_OPT_KEY1 = 0x08192A3B
FLASH_OPT_KEY2 = 0x4C5D6E7F
# FLASH Flag definition
FLASH_FLAG_BSY = FLASH_SR_BSY        # FLASH Busy flag
FLASH_FLAG_OPERR = FLASH_SR_SOP      # FLASH operation Error flag
FLASH_FLAG_WRPERR = FLASH_SR_WRPERR  # FLASH Write protected error flag
FLASH_FLAG_PGAERR = FLASH_SR_PGAERR  # FLASH Programming Alignment error flag
FLASH_FLAG_PGPERR = FLASH_SR_PGPERR  # FLASH Programming Parallelism error flag
FLASH_FLAG_PGSERR = FLASH_SR_PGSERR  # FLASH Programming Sequence error flag
FLASH_FLAG_RDERR = 0x00000100        # Read Protection error flag (PCROP)

# hal/src/stm32f4xx_hal_flash.c
# hal/src/stm32f4xx_hal_flash_ex.c
HAL_FLASH_TIMEOUT_VALUE = 50000

# stm32f4xx_hal_flash_ex.h
# FLASH Option Bytes Read Protection
OB_RDP_LEVEL_0 = 0xAA  # No protection
OB_RDP_LEVEL_1 = 0x55  # Read protection of the memory
OB_RDP_LEVEL_2 = 0xCC  # Full chip protection

# cmsis/devinc/stm32f4xx.h
# Flag status
RESET = 0


# hal/src/stm32f4xx_hal_flash_ex.c
def get_rdp():
    '''Returns the FLASH Read Protection level: 0, 1 or 2.'''

    value = stm.mem8[OPTCR_BYTE1_ADDRESS]

    return {OB_RDP_LEVEL_0: 0,
            OB_RDP_LEVEL_1: 1,
            OB_RDP_LEVEL_2: 2}.get(value, 0)


# hal/src/stm32f4xx_hal_flash_ex.c
def set_rdp(level):
    '''Set the FLASH Read Protection level.

    This parameter can be one of the following values:

    - 0: No protection
    - 1: Read protection of the memory
    - 2: Full chip protection

    WARNING: When enabling level 2 it's no more possible to go back to level 1 or 0.
    '''

    value = {0: OB_RDP_LEVEL_0,
             1: OB_RDP_LEVEL_1,
             2: OB_RDP_LEVEL_2}.get(level)
    if value is None:
        raise Exception('Read Protection level should be 0, 1 or 2, but %r',
                        level)
    if not HAL_FLASH_OB_Unlock():
        return False
    if not FLASH_WaitForLastOperation(HAL_FLASH_TIMEOUT_VALUE):
        return False

    stm.mem8[OPTCR_BYTE1_ADDRESS] = value

    if not HAL_FLASH_OB_Launch():
        return False
    if not HAL_FLASH_OB_Lock():
        return False

    return True


# hal/src/stm32f4xx_hal_flash.c
def HAL_FLASH_OB_Unlock():
    '''Unlock the FLASH control register access'''
    if stm.mem32[FLASH + FLASH_OPTCR] & FLASH_OPTCR_OPTLOCK != RESET:
        stm.mem32[FLASH + FLASH_OPTKEYR] = FLASH_OPT_KEY1
        stm.mem32[FLASH + FLASH_OPTKEYR] = FLASH_OPT_KEY2
        return True
    else:
        return False


# hal/src/stm32f4xx_hal_flash.c
def HAL_FLASH_OB_Lock():
    '''Locks the FLASH control register access'''
    stm.mem32[FLASH + FLASH_CR] |= FLASH_CR_LOCK
    return True


# hal/src/stm32f4xx_hal_flash.c
def HAL_FLASH_OB_Launch():
    '''Launch the option byte loading.'''
    stm.mem8[OPTCR_BYTE0_ADDRESS] |= FLASH_OPTCR_OPTSTRT
    return FLASH_WaitForLastOperation(HAL_FLASH_TIMEOUT_VALUE)


# hal/inc/stm32f4xx_hal_flash.h
def __HAL_FLASH_GET_FLAG(flag):
    return FLASH_SR & flag


# hal/src/stm32f4xx_hal_flash.c
def FLASH_WaitForLastOperation(timeout):
    tickstart = pyb.millis()
    while (__HAL_FLASH_GET_FLAG(FLASH_FLAG_BSY) != RESET):
        if (timeout != HAL_MAX_DELAY):
            if (timeout == 0 or (pyb.millis() - tickstart) > timeout):
                return False
    if __HAL_FLASH_GET_FLAG(FLASH_FLAG_OPERR | FLASH_FLAG_WRPERR |
                            FLASH_FLAG_PGAERR | FLASH_FLAG_PGPERR |
                            FLASH_FLAG_PGSERR | FLASH_FLAG_RDERR) != RESET:
        # FLASH_SetErrorCode()
        return False
    return True
