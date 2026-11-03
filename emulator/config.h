#ifndef CONFIG_H
#define CONFIG_H

// Stompbox: encoder + footswitch, one device per box.
// Same sizing will be used on the RP2040.
#define CC_FIRMWARE_MAJOR   0
#define CC_FIRMWARE_MINOR   1
#define CC_FIRMWARE_MICRO   0

#define CC_MAX_DEVICES          1
#define CC_MAX_ACTUATORS        2
#define CC_MAX_ACTUATORGROUPS   1
// per control: the encoder can hold several parameters (push to cycle)
#define CC_MAX_ASSIGNMENTS      4
#define CC_MAX_OPTIONS_ITEMS    8
#define CC_UPDATES_FIFO_SIZE    10
// actuator pages (cc-slave expects the device config to set this)
#define MAX_PAGES               4

#endif
