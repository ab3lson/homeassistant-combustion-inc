import threading
import time
from bleak import BleakScanner
from combustion_ble.ble_manager import BluetoothMode
from combustion_ble.device_manager import DeviceManager
from combustion_ble.devices.device import Device
from combustion_ble.devices.probe import Probe
from combustion_ble.devices.meat_net_node import MeatNetNode

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import dispatcher_send

from .const import EVENT_DISCOVERED

class MeatNetManager:

    hass: HomeAssistant
    devices: dict[str, Device] = {}
    thread: threading.Thread
    running: False
    deviceManager: DeviceManager
    scanner: BleakScanner

    def __init__(self, hass: HomeAssistant):
        self.hass = hass

    def worker(self):

        while self.running:
            time.sleep(0.5)

            devices = self.deviceManager.get_devices()
            for device in devices:
                id = device.unique_identifier
                if self.devices.get(id) is None:
                    try:
                        dispatcher_send(self.hass, EVENT_DISCOVERED, device)
                        self.devices[id] = device
                    except:
                        pass
    
    async def async_start(self) -> None:

        if (DeviceManager.shared is not None):
            self.deviceManager = DeviceManager.shared
        else:
            self.deviceManager = DeviceManager()

        self.deviceManager.enable_meatnet()
        detection_callback = await self.deviceManager.init_bluetooth(mode=BluetoothMode.PASSIVE)

        self.scanner = BleakScanner(detection_callback=detection_callback)
        await self.scanner.start()

        self.thread = threading.Thread(target=self.worker)
        self.running = True
        self.thread.start()
        
    async def async_stop(self) -> None:

        try:
            self.running = False
            await self.deviceManager.async_stop()
            await self.scanner.stop()
            self.thread.join(2)
            self.devices.clear()
        except:
            pass
