/**
 * @file configuration.h
 * @author Jake Grycel
 * @brief Avionic Firmware Flight Configuration Definitions
 * @date 2022
 * 
 * This source file is part of an example system for MITRE's 2022 Embedded System CTF (eCTF).
 * This code is being provided only for educational purposes for the 2022 MITRE eCTF competition,
 * and may not meet MITRE standards for quality. Use this code at your own risk!
 * 
 * @copyright Copyright (c) 2022 The MITRE Corporation
 */


#ifndef __CONFIG_H__
#define __CONFIG_H__

#include <stdint.h>

// This will support a max-size configuration
#define MAX_PAYLOAD_SIZE 63380

// Flight configuration data structure
typedef struct {
    uint16_t flight_id;
    uint8_t departure_name[1024];
    uint8_t destination_name[1024];
    int64_t departure_latitude;
    int64_t departure_longitude;
    int64_t destination_latitude;
    int64_t destination_longitude;
    uint8_t secret[64];
    uint32_t payload_size;
    uint8_t payload[MAX_PAYLOAD_SIZE];
} flight_configuration_t;


#endif