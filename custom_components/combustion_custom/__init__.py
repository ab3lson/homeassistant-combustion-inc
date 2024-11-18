from datetime import timedelta
import logging
import asyncio
from homeassistant import config_entries, core
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval

from .meatnet import MeatNetManager
from .const import DOMAIN, EVENT_REFRESH

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=5)

globalMgr: MeatNetManager

async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Combustion Inc Custom component."""

    _LOGGER.info("Setting up Combustion Inc Custom component")
    try:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, cleanup)

        async def hub_refresh(event_time):
            async_dispatcher_send(hass, EVENT_REFRESH)

        # register scan interval for ArloHub
        async_track_time_interval(hass, hub_refresh, SCAN_INTERVAL)
    except Exception as e:
        _LOGGER.error("Error setting up Combustion Inc Custom component: %s", str(e))
        return False

    return True

async def async_setup_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> bool:

    try:
        mgr = MeatNetManager(hass)
        await mgr.async_start()

        global globalMgr
        globalMgr = mgr

        hass.data.setdefault(DOMAIN,{})

        hass.data[DOMAIN]["mgr"] = mgr
        hass.data[DOMAIN][entry.entry_id] = entry.data
        await hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, "sensor"))
    except Exception as e:
        _LOGGER.error("Error setting up Combustion Inc Custom component: %s", str(e))
        return False
    
    return True

async def async_unload_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> bool:

    try:
        unload_ok = all(
            await asyncio.gather(
                *[hass.config_entries.async_forward_entry_unload(entry, "sensor")]
            )
        )

        mgr = hass.data[DOMAIN]["mgr"]
        await mgr.async_stop()
        hass.data[DOMAIN].pop(entry.entry_id)
        hass.data[DOMAIN].pop("mgr")
    except Exception as e:
        _LOGGER.error("Error unloading Combustion Inc Custom component: %s", str(e))
        return False

    return True

async def cleanup(event):
    try:
        _LOGGER.info("Cleaning up Combustion Inc Custom component")
        await globalMgr.async_stop()
    except Exception as e:
        _LOGGER.error("Error cleaning up Combustion Inc Custom component: %s", str(e))
