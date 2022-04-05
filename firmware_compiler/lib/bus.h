/**
 * @file bus.h
 * @author Jake Grycel
 * @brief Avionic Firmware Bus Interface Driver
 * @date 2022
 * 
 * This source file is part of an example system for MITRE's 2022 Embedded System CTF (eCTF).
 * This code is being provided only for educational purposes for the 2022 MITRE eCTF competition,
 * and may not meet MITRE standards for quality. Use this code at your own risk!
 * 
 * @copyright Copyright (c) 2022 The MITRE Corporation
 */

#ifndef __BUS_H__
#define __BUS_H__


/**
 * Includes
 */
#include <stdint.h>
#include <stdlib.h>
#include <stdbool.h>
#include "bus.h"
#include "uart.h"


/**
 * Macros
 */
#define MAX_BUS_PAYLOAD_SIZE 128
#define MAX_CONTROLLERS 128


/**
 * Structs / Enums
 */

// Bus Commands
enum BusCommand {
    SHUTDOWN = 0,
    START = 1,
    ADD_CTRL = 2,
    RM_CTRL = 3,
    SEND_DATA = 4
};

// Bus Packet
typedef struct {
    uint16_t dst_id;
    uint16_t src_id;
    uint16_t cmd;
    uint16_t data_type;
    uint16_t data_len;
    uint8_t  payload[MAX_BUS_PAYLOAD_SIZE];
} BusPacket;

// Data Packet
typedef struct {
    uint16_t dev_id;
    uint16_t data_type;
    uint16_t data_len;
    uint8_t  payload[MAX_BUS_PAYLOAD_SIZE];
} DataPacket;

// Device State
typedef struct {
    uint16_t dev_id;
    uint8_t running;
    uint8_t num_controllers;
    uint16_t control_ids[MAX_BUS_PAYLOAD_SIZE];
} DeviceState;


/**
 * Function Prototypes
 */

/**
 * @brief Initialize Bus Interface
 */
void init_bus_interface(void);

/**
 * @brief Initialize Device State
 * 
 * Set up the default privileged controller (ID 0) and assign the device ID.
 * Default start-up state is shut-down.
 * 
 * @param device_state is a pointer to the DeviceState to save the context in.
 * @param dev_id is the bus device ID to assign to this device
 * @param ctrl_id is the starting privileged bus controller ID
 */
void init_device_state(DeviceState *device_state, uint16_t dev_id, uint16_t ctrl_id);

/**
 * @brief Initialize Bus Packet
 * 
 * Zeroize a bus packet struct
 * 
 * @param bus_packet is a pointer to the BusPacket type to initialize.
 */
void init_bus_packet(BusPacket *bus_packet);

/**
 * @brief Initialize Data Packet
 * 
 * Zeroize a data packet struct.
 * 
 * @param data_packet is a pointer to the DataPacket type to initialize.
 * @param dev_id is the bus device ID to assign to this device
 */
void init_data_packet(DataPacket *data_packet);

/**
 * @brief Convert BusPacket to DataPacket
 * 
 * Copy BusPacket contents to a DataPacket for receiving a data packet. The
 * BusPacket source ID is copied as the DataPacket device ID.
 * 
 * @param bus_packet is a pointer to the BusPacket type to copy from.
 * @param data_packet is a pointer to the DataPacket type to copy to.
 */
void bus_to_data_packet(BusPacket *bus_packet, DataPacket *data_packet);

/**
 * @brief Convert DataPacket to BusPacket
 * 
 * Copy DataPacket contents to a BusPacket for sending a data packet. The
 * DataPacket device ID is copied to the BusPacket destination ID.
 * 
 * @param device_state is a pointer to the DeviceState to get the source ID from.
 * @param bus_packet is a pointer to the BusPacket type to copy from.
 * @param data_packet is a pointer to the DataPacket type to copy to.
 */
void data_to_bus_packet(DeviceState *device_state, DataPacket *data_packet, BusPacket *bus_packet);

/**
 * @brief Add Privileged Bus Controller
 * 
 * Adds the requested ID to the device state privileged bus controller list. If
 * there are no more controller slots available, or the requested device is
 * already in the list, no action is performed.
 * 
 * @param device_state is a pointer to the device state.
 * @param dev_id is the device ID to add as a controller.
 */
void add_control(DeviceState *device_state, uint16_t dev_id);

/**
 * @brief Remove Privileged Bus Controller
 * 
 * Removes the requested ID from the device state privileged bus controller
 * list. If there are no controllers, or the requested device is not in the
 * list, no action is performed.
 * 
 * @param device_state is a pointer to the device state.
 * @param dev_id is the device ID to remove as a controller.
 */
void rm_control(DeviceState *device_state, uint16_t dev_id);

/**
 * @brief Handle Privileged Bus Controller Command
 * 
 * Performs the command requested by an already-authenticated privileged bus
 * controller
 * 
 * @param device_state is a pointer to the device state.
 * @param bus_packet is a pointer to the BusPacket containing the command.
 */
void handle_control_message(DeviceState *device_state, BusPacket *bus_packet);

/**
 * @brief Check for Incoming Packets
 * 
 * Checks if a BusPacket is available over UART and handles the packet. If the
 * packet is not destined for this device, or was sent from this device, no
 * action is performed. If the packet is from a valid bus controller, the
 * privileged action is performed. Otherwise, the BusPacket is converted to a
 * DataPacket.
 * 
 * @param device_state is a pointer to the device state.
 * @param data_packet is a pointer to the DataPacket to fill.
 * 
 * @return bool indicates if a DataPacket was returned to the caller
 */
bool check_for_packet(DeviceState *device_state, DataPacket *data_packet);

/**
 * @brief Send Bus Packet
 * 
 * Send a bus packet over the bus. If device is not running, this function
 * will wait until it is.
 * 
 * @param device_state is a pointer to the device state.
 * @param bus_packet is a pointer to the BusPacket to send.
 */
void wait_send_bus_packet(DeviceState *device_state, BusPacket *bus_packet);

/**
 * @brief Receive Data Packet
 * 
 * Receive a data packet from the bus. If the device is not running, or controller
 * messages are received, keep receiving until getting a Data Packet.
 * will wait until it is.
 * 
 * @param device_state is a pointer to the device state.
 * @param data_packet is a pointer to the DataPacket to save.
 */
void recv_data_packet(DeviceState *device_state, DataPacket *data_packet);

/**
 * @brief Send Add Controller Packet
 * 
 * Send a packet to a specified device to add a device as a bus controller
 * 
 * ONLY ACCEPTED IF THIS DEVICE IS A CONTROLLER ON THE RECIPIENT
 * 
 * @param device_state is a pointer to the device state.
 * @param dst_id is the device ID to send the command to.
 * @param target_id is the device ID to add as a controller.
 */
void send_add_control(DeviceState *device_state, uint16_t dst_id, uint16_t target_id);

/**
 * @brief Send Remove Controller Packet
 * 
 * Send a packet to a specified device to remove a device as a bus controller
 * 
 * ONLY ACCEPTED IF THIS DEVICE IS A CONTROLLER ON THE RECIPIENT
 * 
 * @param device_state is a pointer to the device state.
 * @param dst_id is the device ID to send the command to.
 * @param target_id is the device ID to remove as a controller.
 */
void send_rm_control(DeviceState *device_state, uint16_t dst_id, uint16_t target_id);

/**
 * @brief Send Device Start Packet
 * 
 * Send a packet to a specified device to enable it.
 * 
 * ONLY ACCEPTED IF THIS DEVICE IS A CONTROLLER ON THE RECIPIENT
 * 
 * @param device_state is a pointer to the device state.
 * @param dst_id is the device ID to start.
 */
void send_start(DeviceState *device_state, uint16_t dst_id);

/**
 * @brief Send Device Shutdown Packet
 * 
 * Send a packet to a specified device to disable it.
 * 
 * ONLY ACCEPTED IF THIS DEVICE IS A CONTROLLER ON THE RECIPIENT
 * 
 * @param device_state is a pointer to the device state.
 * @param dst_id is the device ID to shutdown.
 */
void send_shutdown(DeviceState *device_state, uint16_t dst_id);

/**
 * @brief Send Data Packet Packet
 * 
 * Send a data packet to a specific device
 * 
 * @param device_state is a pointer to the device state.
 * @param data_packet is a pointer to the DataPacket type to send.
 */
void send_data_packet(DeviceState *device_state, DataPacket *data_packet);

#endif // __BUS_H__