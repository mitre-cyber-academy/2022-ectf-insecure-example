/**
* @file firmware.c
* @author Jake Grycel
* @brief Example Firmware Implementation
* 
* @date 2022
* 
* This source file is part of an example system for MITRE's 2022 Embedded System CTF (eCTF).
* This code is being provided only for educational purposes for the 2022 MITRE eCTF competition,
* and may not meet MITRE standards for quality. Use this code at your own risk!
* 
* @copyright Copyright (c) 2022 The MITRE Corporation
*/

#include <stdbool.h>
#include <string.h>
#include <stdint.h>

#include "bus.h"
#include "configuration.h"
#include "uart.h"

extern uint32_t _config;

// Example bus ID definitions
#define CONTROL_ID   ((uint16_t)0)
#define NAV_ID       ((uint16_t)1)
#define GPS_ID       ((uint16_t)2)
#define AUTOPILOT_ID ((uint16_t)3)
#define ALTIMETER_ID ((uint16_t)4)

// Example message type
#define UPDATE_REQ  ((uint16_t)0)
#define RESPOND_MSG ((uint16_t)1)


/**
 * @brief Wait for Data Packet
 * 
 * Receive data packets until the expected device ID and data type are received.
 * 
 * @param device_state is a pointer to the device state.
 * @param dev_id is the bus device ID to wait for
 * @param data_type is the data packet type to wait for
 */
void wait_for_packet(DeviceState *device_state, DataPacket *data_packet, uint16_t dev_id, uint16_t data_type)
{
    init_data_packet(data_packet);
    do {
        // Get packet
        recv_data_packet(device_state, data_packet);

        // Break out if got the expected message
    } while (!(data_packet->dev_id == dev_id) && (data_packet->data_type != data_type));
}


/**
 * @brief Example Firmware Main
 */
int main()
{
    // Reference to installed flight configuration
    flight_configuration_t *configuration = (flight_configuration_t *)(&_config);

    // Device State
    DeviceState device_state;
    DataPacket data_packet;

    // Initialize the device
    init_device_state(&device_state, NAV_ID, CONTROL_ID);
    init_bus_interface();
    
    // Wait until started - The bus driver won't send messages until the device
    // is started by a privileged bus controller
    while (!device_state.running) {
        check_for_packet(&device_state, &data_packet);
    }

    // EXAMPLE: Receive a data packet from a specific device
    wait_for_packet(&device_state, &data_packet, GPS_ID, UPDATE_REQ);

    // EXAMPLE: Construct a data packet and send it to a specific device
    init_data_packet(&data_packet);
    data_packet.dev_id = AUTOPILOT_ID;
    data_packet.data_type = RESPOND_MSG;
    data_packet.data_len = 2;
    *((uint16_t *)data_packet.payload) = 0xFACE;
    send_data_packet(&device_state, &data_packet);
}
