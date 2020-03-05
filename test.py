from aiowiserhub import wiserHub, _LOGGER, WiserException
import logging
import asyncio
import json
import aiohttp
import time

_LOGGER.setLevel(level=logging.DEBUG)

WISERGOODIP = "YOURIPHERE"
WISERBADIP = "192.168.1.1"
WISERKEY = "YOURKEYHERE"

STARS = "*************************"


class wiserTest:
    def __init__(self, wiserip, wiserkey):
        self.wiserkey = wiserkey
        self.wiserip = wiserip

    def output(self, prt, heading=""):
        print(STARS)
        if heading != "":
            print(heading)
            print(STARS)
            print(prt)
        else:
            print(prt)
            print(STARS)

    async def async_tests(self):
        wh = wiserHub(self.wiserip, self.wiserkey)
        data = await wh.asyncGetHubData()
        if data:
            self.output("Got data from Wiser Hub")

            print("###################################################")
            print("Value Checks Section")
            print("###################################################")
            # output hub data sections
            self.output(wh.name, "WiserHub Name")
            self.output(wh.network, "Network")
            self.output(wh.system, "System")
            self.output(wh.cloud, "Cloud")
            self.output(wh.capability, "Capability")
            self.output(wh.heating, "Heating")
            self.output(wh.hotwater, "Hot Water")
            self.output(wh.devices, "Devices")
            self.output(wh.rooms, "Rooms")
            self.output(wh.thermostats, "Thermostats")
            self.output(wh.roomStats, "Room Stats")
            self.output(wh.schedules, "Schedules")
            self.output(wh.smartPlugs, "Smart Plugs")
            self.output(wh.relayNodes, "Wiser Zigbee Relay Nodes")

            # Test specific item functions
            self.output(wh.systemValue("BrandName"), "Wiser Brand System Value")
            self.output(wh.device(1), "Device 1")
            self.output(wh.room(1), "Room 1")
            self.output(wh.deviceRoom(1), "Device 1 Room")

            if wh.thermostat(1):
                self.output(wh.thermostat(1), "Thermostat 1")
            if wh.roomStat(1):
                self.output(wh.roomStat(1), "Roomstat 1")

            self.output(wh.schedule(1), "Schedule 1")
            self.output(wh.roomSchedule(1), "Room Schedule 1")

            if wh.smartPlugs:
                self.output(wh.smartPlug(wh.smartPlugs[0].get("id")), "SmartPlug 1")
                self.output(
                    wh.smartPlugMode(wh.smartPlugs[0].get("id")), "SmartPlug 1 Mode"
                )

            self.output(wh.deviceParentNode(1), "Device 1 Parent Node")

            # Next section
            self.output(wh.heatingRelayStatus(), "Heating Relay Status")
            self.output(wh.hotwaterRelayStatus, "Hot Water Relay Status")

            self.output(wh.roomSetPoint(1), "Room 1 Set Point")
            self.output(wh.roomTemperature(1), "Room 1 Displayed Temp")

            self.output(wh.homeAwayMode, "Current Operating Mode")

            print("###################################################")
            print("Set Methods Checks Section")
            print("###################################################")
            # Home Away Mode
            self.output(
                await wh.asyncSetHomeAwayMode(wh.homeAwayMode),
                "Set Home/Away to {}".format(wh.homeAwayMode),
            )
            # How Water Mode
            try:
                self.output(
                    await wh.asyncSetHotwaterMode("AUTO"), "Set Hot Water Mode to Auto"
                )
            except BaseException as ex:
                self.output(ex, "Set Hot Water Mode to Auto")
            # System Switch
            try:
                self.output(
                    await wh.asyncSetSystemSwitch("ValveProtectionEnabled", "True"),
                    "Set valve protection to enabled",
                )
            except BaseException as ex:
                self.output(ex, "Set System Switch")
            # Smart Plug
            if wh.smartPlugs:
                self.output(
                    await wh.asyncSetSmartPlugState(wh.smartPlugs[0].get("id"), "On"),
                    "Turn smart plug on",
                )
                await asyncio.sleep(5)
                self.output(
                    await wh.asyncSetSmartPlugState(wh.smartPlugs[0].get("id"), "Off"),
                    "Turn smart plug off",
                )

            print("###################################################")
            print("Error Handling Values Checks Section")
            print("###################################################")

            # Test error handling for invalid values
            self.output(wh.systemValue("NONSYSTEMVALUE"), "System Value Error Check")
            self.output(wh.device(999), "Device 999 Error Check")
            self.output(wh.room(999), "Room 999 Error Check")
            self.output(wh.deviceRoom(999), "Device Room Error Check")
            self.output(wh.thermostat(999), "Thermostat Error Check")
            self.output(wh.roomStat(999), "Room Stat Error Check")
            self.output(wh.schedule(999), "Schedule Error Check")
            self.output(wh.roomSchedule(999), "Room Schedule Error Check")
            self.output(wh.smartPlug(999), "Smart Plug Error Check")
            self.output(wh.smartPlugMode(999), "Smart Plug Mode Error Check")
            self.output(wh.deviceParentNode(999), "Device Parent Node Error Check")

            self.output(wh.heatingRelayStatus(4), "Heating Relay Status Error Check")
            self.output(wh.roomSetPoint(999), "Room 1 Set Point Error Check")
            self.output(wh.roomTemperature(999), "Room 1 Displayed Temp Error Check")

            print("###################################################")
            print("Error Set Methods Checks Section")
            print("###################################################")
            # Home Away Mode
            try:
                self.output(
                    await wh.asyncSetHomeAwayMode("AWAYHOME"),
                    "Set Home/Away to 'AWAYHOME' as Invalid Mode",
                )
            except WiserException as ex:
                self.output(ex, "Set Home/Away to 'AWAYHOME' as Invalid Mode")
            # How Water Mode
            try:
                self.output(
                    await wh.asyncSetHotwaterMode("MAGIC"),
                    "Set Hot Water Mode to 'MAGIC' as Invalid Mode",
                )
            except WiserException as ex:
                self.output(ex, "Set Hot Water Mode to 'MAGIC' as Invalid Mode")
            # System Switch
            try:
                self.output(
                    await wh.asyncSetSystemSwitch("ValveProtectionEnabled1", "True"),
                    "Set invalid system switch to enabled",
                )
            except WiserException as ex:
                self.output(ex, "Set Invalid System Switch to enabled")
            # Smart Plug
            if wh.smartPlugs:
                try:
                    self.output(
                        await wh.asyncSetSmartPlugState(999, "On"),
                        "Turn smart plug 999 on",
                    )
                except WiserException as ex:
                    self.output(ex, "Turn smart plug 999 on")
                try:
                    self.output(
                        await wh.asyncSetSmartPlugState(
                            wh.smartPlugs[0].get("id"), "One"
                        ),
                        "Turn smart plug to invalid mode",
                    )
                except WiserException as ex:
                    self.output(ex, "Turn smart plug to invalid mode")

            # All tests completed
            return True
        else:
            print("###################################################")
            print("Error getting data from hub")
            print("###################################################")
            return False


async def test():
    wh = wiserTest(WISERGOODIP, WISERKEY)
    w = await wh.async_tests()
    if w:
        wh.output("Tests Completed Successfully")
    else:
        wh.output("Tests Failed")


try:
    asyncio.run(test())
except asyncio.TimeoutError as ex:
    print("Timeout connecting to hub")

