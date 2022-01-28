/**
 * @file flash.h
 * @author Kyle Scaplen
 * @brief Bootloader flash memory interface implementation.
 * @date 2022
 * 
 * This source file is part of an example system for MITRE's 2022 Embedded System CTF (eCTF).
 * This code is being provided only for educational purposes for the 2022 MITRE eCTF competition,
 * and may not meet MITRE standards for quality. Use this code at your own risk!
 * 
 * @copyright Copyright (c) 2022 The MITRE Corporation
 */

#include <stdbool.h>
#include <stdint.h>

#include "driverlib/flash.h"
#include "inc/hw_flash.h"
#include "inc/hw_types.h"

#include "flash.h"

/**
 * @brief Erases a block of flash.
 * 
 * @param addr is the starting address of the block of flash to erase.
 * @return 0 on success, or -1 if an invalid block address was specified or the 
 * block is write-protected.
 */
int32_t flash_erase_page(uint32_t addr)
{
    // Erase page containing this address
    return FlashErase(addr & ~(FLASH_PAGE_SIZE - 1));
} 

/**
 * @brief Writes a word to flash.
 * 
 * This function writes a single word to flash memory. The flash address must
 * be a multiple of 4.
 * 
 * @param data is the value to write.
 * @param addr is the location to write to.
 * @return 0 on success, or -1 if an error occurs.
 */
int32_t flash_write_word(uint32_t data, uint32_t addr)
{
    // check address is a multiple of 4
    if ((addr & 0x3) != 0) {
        return -1;
    }

    // Clear the flash access and error interrupts.
    HWREG(FLASH_FCMISC) = (FLASH_FCMISC_AMISC | FLASH_FCMISC_VOLTMISC | FLASH_FCMISC_INVDMISC | FLASH_FCMISC_PROGMISC);

    // Set the address
    HWREG(FLASH_FMA) = addr & FLASH_FMA_OFFSET_M;

    // Set the data
    HWREG(FLASH_FMD) = data;

    // Set the memory write key and the write bit
    HWREG(FLASH_FMC) = FLASH_FMC_WRKEY | FLASH_FMC_WRITE;

    // Wait for the write bit to get cleared
    while(HWREG(FLASH_FMC) & FLASH_FMC_WRITE);

    // Return an error if an access violation occurred.
    if(HWREG(FLASH_FCRIS) & (FLASH_FCRIS_ARIS | FLASH_FCRIS_VOLTRIS | FLASH_FCRIS_INVDRIS | FLASH_FCRIS_PROGRIS)) {
        return -1;
    }

    // Success
    return 0;
}


/**
 * @brief Writes data to flash.
 * 
 * This function writes a sequence of words to flash memory. Because the flash 
 * is written one word at a time, the starting address must be a multiple of 4.
 * 
 * @param data is a pointer to the data to be written.
 * @param addr is the starting address in flash to be written to.
 * @param count is the number of words to be written.
 * @return 0 on success, or -1 if an error occurs.
 */
int32_t flash_write(uint32_t *data, uint32_t addr, uint32_t count)
{
    int i;
    int status;

    // check address and count are multiples of 4
    if ((addr & 0x3) != 0) {
        return -1;
    }

    // Loop over the words to be programmed.
    for (i = 0; i < count; i++) {
        status = flash_write_word(data[i], addr);

        if (status == -1) {
            return -1;
        }

        addr += 4;
    }

    // Success
    return(0);
}
