# Combustion Inc Intergration for Home Assistant

This integration will setup a single [Combustion Inc.](https://combustion.inc) hub with one device for every probe that it detects. Each probe will come with 21 sensors.

The sensors will all move to the unavalaible state if HA doesn't recieve any BLE announcement data within 15s. This will allow you to hide cards by state for when the probe(s) are turned off.

The intergration will use the local bluetooth MeatNet as needed. It will prefer the probe directly, unless there is a better signal being broadcast by a MeatNet repeater.

## Installation

## Credits
This integration is just a wrapper around the excellent python library [combustion_ble](https://github.com/legrego/combustion_ble). All of the heavy lifting is done by that library, and simply exposed as sensors here.
