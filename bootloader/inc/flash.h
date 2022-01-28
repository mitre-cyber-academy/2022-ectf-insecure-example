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

#ifndef FLASH_H
#define FLASH_H

#include <stdint.h>

// Flash properties
#define FLASH_START        ((uint32_t)0x00000000)
#define FLASH_PAGE_SIZE    ((uint32_t)0x00000400)
#define FLASH_END          ((uint32_t)0x00040000)

// Function Prototypes

/**
 * @brief Erases a block of flash.
 * 
 * @param addr is the starting address of the block of flash to erase.
 * @return 0 on success, or -1 if an invalid block address was specified or the 
 * block is write-protected.
 */
int32_t flash_erase_page(uint32_t addr);

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
int32_t flash_write_word(uint32_t data, uint32_t addr);

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
int32_t flash_write(uint32_t *data, uint32_t addr, uint32_t count);

#endif // FLASH_H