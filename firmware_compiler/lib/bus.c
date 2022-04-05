/**
 * @file bus.c
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

#include <stdint.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>

#include "bus.h"
#include "uart.h"

/**
 * @brief Initialize Bus Interface
 */
void init_bus_interface(void)
{
    uart_init();
}

/**
 * @brief Initialize Device State
 * 
 * Set up the default privileged controller (ID 0) and assign the device ID.
 * Default start-up state is shut-down.
 * 
 * @param device_state is a pointer to the DeviceState to save the context in.
 * @param dev_id is the bus device ID to assign to this device
 */
void init_device_state(DeviceState *device_state, uint16_t dev_id, uint16_t ctrl_id)
{
    device_state->dev_id = dev_id;
    device_state->running = 0;
    memset(device_state->control_ids, 0, MAX_CONTROLLERS*sizeof(uint16_t));
    device_state->control_ids[0] = ctrl_id;
    device_state->num_controllers = 1;
}

/**
 * @brief Initialize Bus Packet
 * 
 * Zeroize a bus packet struct
 * 
 * @param bus_packet is a pointer to the BusPacket type to initialize.
 */
void init_bus_packet(BusPacket *bus_packet)
{
    memset((uint8_t *)bus_packet, 0, sizeof(BusPacket));
}

/**
 * @brief Initialize Data Packet
 * 
 * Zeroize a data packet struct.
 * 
 * @param data_packet is a pointer to the DataPacket type to initialize.
 * @param dev_id is the bus device ID to assign to this device
 */
void init_data_packet(DataPacket *data_packet)
{
    memset((uint8_t *)data_packet, 0, sizeof(DataPacket));
}

/**
 * @brief Convert BusPacket to DataPacket
 * 
 * Copy BusPacket contents to a DataPacket for receiving a data packet. The
 * BusPacket source ID is copied as the DataPacket device ID.
 * 
 * @param bus_packet is a pointer to the BusPacket type to copy from.
 * @param data_packet is a pointer to the DataPacket type to copy to.
 */
void bus_to_data_packet(BusPacket *bus_packet, DataPacket *data_packet)
{
    data_packet->dev_id = bus_packet->src_id;
    data_packet->data_type = bus_packet->data_type;
    data_packet->data_len = bus_packet->data_len;
    memcpy(data_packet->payload, bus_packet->payload, MAX_BUS_PAYLOAD_SIZE);
}

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
void data_to_bus_packet(DeviceState *device_state, DataPacket *data_packet, BusPacket *bus_packet)
{
    bus_packet->dst_id = data_packet->dev_id;
    bus_packet->src_id = device_state->dev_id;
    bus_packet->cmd = SEND_DATA;
    bus_packet->data_type = data_packet->data_type;
    bus_packet->data_len = data_packet->data_len;
    memcpy(bus_packet->payload, data_packet->payload, MAX_BUS_PAYLOAD_SIZE);
}

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
void add_control(DeviceState *device_state, uint16_t dev_id)
{
    // Check if at limit
    if (device_state->num_controllers == MAX_CONTROLLERS) {
        return;
    }

    // Check if in list
    for (int i = 0; i < device_state->num_controllers; i++) {
        if (device_state->control_ids[i] == dev_id) {
            return;
        }
    }

    // Add ID
    device_state->control_ids[device_state->num_controllers++] = dev_id;
}

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
void rm_control(DeviceState *device_state, uint16_t dev_id)
{
    int i = 0;

    // Check if at 0
    if (device_state->num_controllers == 0) {
        return;
    }

    // Check if in list
    uint8_t found = 0;
    for (i = 0; i < device_state->num_controllers; i++) {
        if (device_state->control_ids[i] == dev_id) {
            found = 1;
            break;
        }
    }

    // Exit if not in list
    if (!found) {
        return;
    }

    // Replace ID by shifting down
    for (i = i; i < (device_state->num_controllers-1); i++) {
        device_state->control_ids[i] = device_state->control_ids[i+1];
    }
    
    // Update count
    device_state->num_controllers--;
}

/**
 * @brief Handle Privileged Bus Controller Command
 * 
 * Performs the command requested by an already-authenticated privileged bus
 * controller
 * 
 * @param device_state is a pointer to the device state.
 * @param bus_packet is a pointer to the BusPacket containing the command.
 */
void handle_control_message(DeviceState *device_state, BusPacket *bus_packet)
{
    switch (bus_packet->cmd) {
        case SHUTDOWN:
            device_state->running = 0;
            break;
        case START:
            device_state->running = 1;
            break;
        case ADD_CTRL:
            add_control(device_state, *((uint16_t *)(bus_packet->payload)));
            break;
        case RM_CTRL:
            rm_control(device_state, *((uint16_t *)(bus_packet->payload)));
            break;
    }
}

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
bool check_for_packet(DeviceState *device_state, DataPacket *data_packet)
{
    BusPacket bus_packet;

    // Check if bytes are available
    if (!uart_avail(HOST_UART)) {
        return false;
    }

    // Read packet from bus
    uart_read(HOST_UART, (uint8_t *)(&bus_packet), sizeof(BusPacket));

    // Check routing
    if (bus_packet.src_id == device_state->dev_id) {
        // Discard if the message is from this device
        return false;
    } else if (bus_packet.dst_id != device_state->dev_id) {
        // Discard if the message is not for this device
        return false;
    }

    // Check if source ID is in the controllers list
    uint8_t control_message = 0;
    for (int i = 0; i < device_state->num_controllers; i++) {
        if (bus_packet.src_id == device_state->control_ids[i]) {
            control_message = 1;
            break;
        }
    }

    // Check if command is in the privileged command list
    if (control_message) {
        if ((bus_packet.cmd == SHUTDOWN)
        || (bus_packet.cmd == START)
        || (bus_packet.cmd == ADD_CTRL)
        || (bus_packet.cmd == RM_CTRL)) {
            handle_control_message(device_state, &bus_packet);
            return false;
        }
    }

    // Check if running
    if (!device_state->running) {
        return false;
    }

    // Handle data packet
    bus_to_data_packet(&bus_packet, data_packet);
    return true;
}

/**
 * @brief Send Bus Packet
 * 
 * Send a bus packet over the bus. If device is not running, this function
 * will wait until it is.
 * 
 * @param device_state is a pointer to the device state.
 * @param bus_packet is a pointer to the BusPacket to send.
 */
void wait_send_bus_packet(DeviceState *device_state, BusPacket *bus_packet)
{
    DataPacket temp_dp;

    // Wait until running
    if (!device_state->running) {
        check_for_packet(device_state, &temp_dp);
    }

    // Send the packet
    uart_write(HOST_UART, (uint8_t *)bus_packet, sizeof(BusPacket));
}

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
void recv_data_packet(DeviceState *device_state, DataPacket *data_packet)
{
    // Wait until running
    while (!check_for_packet(device_state, data_packet));
}

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
void send_add_control(DeviceState *device_state, uint16_t dst_id, uint16_t target_id)
{
    // Create and format bus packet
    BusPacket bus_packet;
    init_bus_packet(&bus_packet);
    bus_packet.src_id = device_state->dev_id;
    bus_packet.dst_id = dst_id;
    bus_packet.cmd = ADD_CTRL;
    bus_packet.data_type = 0;
    bus_packet.data_len = 2;
    memcpy(&(bus_packet.payload), (uint8_t *)(&target_id), 2);

    // Send packet
    wait_send_bus_packet(device_state, &bus_packet);
}

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
void send_rm_control(DeviceState *device_state, uint16_t dst_id, uint16_t target_id)
{
    // Create and format bus packet
    BusPacket bus_packet;
    init_bus_packet(&bus_packet);
    bus_packet.src_id = device_state->dev_id;
    bus_packet.dst_id = dst_id;
    bus_packet.cmd = RM_CTRL;
    bus_packet.data_type = 0;
    bus_packet.data_len = 2;
    memcpy(&(bus_packet.payload), (uint8_t *)(&target_id), 2);

    // Send packet
    wait_send_bus_packet(device_state, &bus_packet);
}

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
void send_start(DeviceState *device_state, uint16_t dst_id)
{
    // Create and format bus packet
    BusPacket bus_packet;
    init_bus_packet(&bus_packet);
    bus_packet.src_id = device_state->dev_id;
    bus_packet.dst_id = dst_id;
    bus_packet.cmd = START;
    bus_packet.data_type = 0;
    bus_packet.data_len = 0;

    // Send packet
    wait_send_bus_packet(device_state, &bus_packet);
}

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
void send_shutdown(DeviceState *device_state, uint16_t dst_id)
{
    // Create and format bus packet
    BusPacket bus_packet;
    init_bus_packet(&bus_packet);
    bus_packet.src_id = device_state->dev_id;
    bus_packet.dst_id = dst_id;
    bus_packet.cmd = SHUTDOWN;
    bus_packet.data_type = 0;
    bus_packet.data_len = 0;

    // Send packet
    wait_send_bus_packet(device_state, &bus_packet);
}

/**
 * @brief Send Data Packet Packet
 * 
 * Send a data packet to a specific device
 * 
 * @param device_state is a pointer to the device state.
 * @param data_packet is a pointer to the DataPacket type to send.
 */
void send_data_packet(DeviceState *device_state, DataPacket *data_packet)
{
    // Create and format bus packet
    BusPacket bus_packet;
    data_to_bus_packet(device_state, data_packet, &bus_packet);

    // Send packet
    wait_send_bus_packet(device_state, &bus_packet);
}