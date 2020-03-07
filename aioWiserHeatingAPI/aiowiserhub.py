"""
# Wiser API Facade

Angelosantagata@gmail.com


https://github.com/asantaga/wiserheatingapi


This API Facade allows you to communicate with your wiserhub. This API is used by the homeassistant integration available at  https://github.com/asantaga/wiserHomeAssistantPlatform
"""
import aiohttp
import aiofiles
import asyncio
import json
import logging
import os

_LOGGER = logging.getLogger(__name__)

HOMEAWAY = ["HOME", "AWAY"]
TEMP_MINIMUM = 5
TEMP_MAXIMUM = 30
TEMP_OFF = -20
TIMEOUT = 10

WISERHUBURL = "http://{}/data/"
#Api paths
WISERDATA = "domain/"
WISERHOTWATER = "Hotwater/{}"
WISERNETWORK = "network/"
WISERPLUG = "SmartPlug/{}"
WISERROOM = "Room/{}"
WISERSCHEDULE = "Schedule/{}"
WISERSYSTEM = "System/{}"
WISERV2SCHEDULE = "schedules/{}"
WISERV2API = "v2/"



class WiserException(Exception):
    """Base class for exceptions in this module."""

    def __init__(self, status, message):
        self.status = status
        self.message = message


class WiserHubException(WiserException):
    pass


class wiserHub:
    """
    Wiser Hub representation of a hub device, thermostat devices (iTRV and RoomStats), schedules, config switches
    and smart plugs
    """

    def __init__(self, host, api_key, api_version = 1):
        """Setup session and host information"""
        self.host = host
        self.api_key = api_key
        self.headers = {
            "SECRET": self.api_key,
            "Content-Type": "application/json;charset=UTF-8",
        }
        self._api_version = api_version
        self._cloud = {}
        self._capability = {}
        self._devices = {}
        self._device2roomMap = {}
        self._heating = {}
        self._hotwater = {}
        self._network = {}
        self._nodeMap = {}
        self._rooms = {}
        self._roomstats = {}
        self._system = {}
        self._thermostats = {}
        self._schedules = {}
        self._smartplugs = {}
        self._switches = {}

    def _toWiserTemp(self, temp):
        """
        Converts from temperature to wiser hub format
        param temp: The temperature to convert
        return: Integer
        """
        temp = int(temp * 10)
        return temp

    def _fromWiserTemp(self, temp):
        """
        Conerts from wiser hub temperature format to decimal value
        param temp: The wiser temperature to convert
        return: Float
        """
        temp = round(temp / 10, 1)
        return temp

    def _checkTempRange(self, temp):
        """
        Validates temperatures are within the allowed range for the wiser hub
        param temp: The temperature to check
        return: Boolean
        """
        if temp != TEMP_OFF and (temp < TEMP_MINIMUM or temp > TEMP_MAXIMUM):
            return False
        else:
            return True

    async def request(self, mode="get", path="", json=None):
        """Make a request to the Wiser Hub."""
        url = WISERHUBURL.format(self.host) + WISERDATA + path

        timeout = aiohttp.ClientTimeout(total=TIMEOUT)

        try:
            if mode == "get":
                async with aiohttp.request(
                    url=url, method=mode, headers=self.headers, timeout=timeout
                ) as resp:
                    assert resp.status == 200
                    hubData = await resp.json()
                    if hubData:
                        if hubData.get("Cloud"):
                            self._cloud = hubData.get("Cloud")
                        if hubData.get("Device"):
                            self._devices = hubData.get("Device")
                        if hubData.get("DeviceCapabilityMatrix"):
                            self._capability = hubData.get("DeviceCapabilityMatrix")
                        if hubData.get("HeatingChannel"):
                            self._heating = hubData.get("HeatingChannel")
                        if hubData.get("HotWater"):    
                            self._hotwater = hubData.get("HotWater")
                        if hubData.get("Room"):
                            self._rooms = hubData.get("Room")
                        if hubData.get("RoomStat"):
                            self._roomstats = hubData.get("RoomStat")
                        if hubData.get("Schedule"):
                            self._schedules = hubData.get("Schedule")   
                        if hubData.get("SmartPlug"):
                            self._smartplugs = hubData.get("SmartPlug")
                        if hubData.get("SmartValve"):
                            self._thermostats = hubData.get("SmartValve")
                        if hubData.get("System"):
                            self._system = hubData.get("System")
                            
                        # Populate device to room mapping
                        for room in self._rooms:
                            roomStatId = room.get("RoomStatId")
                            if roomStatId is not None:
                                self._device2roomMap[roomStatId] = {
                                    "roomId": room.get("id"),
                                    "roomName": room.get("Name"),
                                }
                            if room.get("SmartValveIds") is not None:
                                for valveId in room.get("SmartValveIds"):
                                    self._device2roomMap[valveId] = {
                                        "roomId": room.get("id"),
                                        "roomName": room.get("Name"),
                                    }

                        # Populate node map
                        for device in self._devices:
                            if device.get("ProductType") in ["Controller", "SmartPlug"]:
                                deviceName = "Unknown"
                                nodeId = device.get("NodeId")
                                if nodeId is not None:
                                    if device.get("ProductType") == "Controller":
                                        deviceName = "Wiser Hub"
                                    elif device.get("ProductType") == "SmartPlug":
                                        deviceName = self.smartPlug(device.get("id"))[
                                            "Name"
                                        ]
                                    self._nodeMap[nodeId] = {
                                        "deviceId": device.get("id"),
                                        "productType": device.get("ProductType"),
                                        "deviceName": deviceName,
                                    }

                        #Get network info
                        url = WISERHUBURL.format(self.host) + WISERNETWORK + path
                        async with aiohttp.request(
                            url=url, method=mode, headers=self.headers, timeout=timeout
                        ) as resp:
                            assert resp.status == 200
                            hubData = await resp.json()
                            if hubData and hubData.get("Station"):
                                self._network = hubData
                        return True
                    else:
                        return False
                        
            elif mode == "patch":
                async with aiohttp.request(
                    url=url,
                    method=mode,
                    headers=self.headers,
                    timeout=timeout,
                    json=json,
                ) as resp:
                    assert resp.status == 200
                    return resp.status
                    
        except AssertionError as ex:
            _LOGGER.debug("Wiser Hub returned an error response")
            if resp.status == 401:
                raise WiserHubException("AuthenticationError", "Authentication error.  Check secret key.")
            elif resp.status == 404:
                raise WiserHubException("InvalidAPICall", "Api path not found.")
            else:
                raise WiserHubException("APIError", "Unknown API or connection error.")
        except AttributeError as ex:
            _LOGGER.debug("Data not returned from Wiser Hub")
            raise WiserHubException("NoData", "Data not returned from Wiser Hub")
        except aiohttp.ClientConnectionError as ex:
            _LOGGER.debug("Connection error trying to update from Wiser Hub")
            raise WiserHubException("ConnectionError", "Connection error trying to update from Wiser Hub")
        except asyncio.TimeoutError as ex:
            _LOGGER.debug(
                "Timed out trying to update from Wiser Hub.  Error {}".format(ex)
            )
            raise WiserHubException("TimeoutError", "Timed out trying to update from Wiser Hub")

    async def asyncGetHubData(self):
        return await self.request()

    @property
    def name(self):
        try:
            return self._network.get("Station").get("NetworkInterface").get("HostName")
        except (KeyError, AttributeError):
            return None
            
    @property
    def network(self):
        return self._network

    @property
    def system(self):
        return self._system

    def systemValue(self, sysValueKey):
        try:
            return self._system.get(sysValueKey)
        except KeyError:
            return None

    @property
    def cloud(self):
        return self._cloud

    @property
    def capability(self):
        return self._capability

    @property
    def heating(self):
        return self._heating

    @property
    def hotwater(self):
        return self._hotwater

    @property
    def devices(self):
        return self._devices

    def device(self, deviceId):
        for device in self._devices:
            if device.get("id") == deviceId:
                return device

    def deviceRoom(self, deviceId):
        try:
            return self._device2roomMap[deviceId]
        except KeyError:
            return None

    @property
    def rooms(self):
        """Gets Room Data as JSON Payload"""
        return self._rooms

    def room(self, roomId):
        """Convinience to get data on a single room"""
        for room in self._rooms:
            if room.get("id") == roomId:
                return room

    @property
    def thermostats(self):
        return self._thermostats

    def thermostat(self, thermostatId):
        for thermostat in self._thermostats:
            if thermostat.get("id") == thermostatId:
                return thermostat

    @property
    def roomStats(self):
        return self._roomstats

    def roomStat(self, roomstatId):
        for roomstat in self._roomstats:
            if roomstat.get("id") == roomstatId:
                return roomstat

    @property
    def schedules(self):
        return self._schedules

    def schedule(self, scheduleId):
        for schedule in self._schedules:
            if schedule.get("id") == scheduleId:
                return schedule

    def roomSchedule(self, roomId):
        if self.room(roomId):
            return self.schedule(self.room(roomId).get("ScheduleId"))

    @property
    def smartPlugs(self):
        return self._smartplugs

    def smartPlug(self, smartplugId):
        for smartplug in self._smartplugs:
            if smartplug.get("id") == smartplugId:
                return smartplug
                
    def smartPlugMode(self, smartplugId):
        for smartplug in self._smartplugs:
            if smartplug.get("id") == smartplugId:
                return smartplug.get("Mode")

    @property
    def relayNodes(self):
        return self._nodeMap

    def deviceParentNode(self, deviceId):
        if self.device(deviceId):
            return self._nodeMap[self.device(deviceId).get("ParentNodeId")]
            

    def heatingRelayStatus(self, heatingChannelId=1):
        # There could be multiple heating channels,
        for heatingChannel in self._heating:
            if heatingChannel.get("id") == heatingChannelId:
                return heatingChannel.get("HeatingRelayState")

    @property
    def hotwaterRelayStatus(self):
        try:
            return self._hotwater[0].get("WaterHeatingState")
        except KeyError:
            return None

    def roomSetPoint(self, roomId):
        room = self.room(roomId)
        if room is not None:
            return room.get("DisplayedSetPoint")

    def roomTemperature(self, roomId):
        room = self.room(roomId)
        if room is not None:
            return room.get("CalculatedTemperature")

    @property
    def homeAwayMode(self):
        if self.systemValue("OverrideType") == "Away":
            return "AWAY"
        else:
            return "HOME"

    # ---------------------------------------------------------------
    # Set functions
    # ---------------------------------------------------------------
    async def asyncSetHomeAwayMode(self, mode, temperature=10):
        """
        
        """
        if mode not in HOMEAWAY:
            raise WiserException(
                "InvalidMode",
                "Mode can only be HOME or AWAY")
                
        if not self._checkTempRange(temperature):
            raise WiserException(
                "InvalidTemp",
                "Temperature can only be between {} and {} or {}(Off)".format(
                    TEMP_MINIMUM, TEMP_MAXIMUM, TEMP_OFF
                )
            )
            
        if mode == "AWAY":
            patchData = {"type": 2, "setPoint": self._toWiserTemp(temperature)}
        else:
            patchData = {"type": 0, "setPoint": 0}
            
        try:
            await self.request(
                "patch", path=WISERSYSTEM.format("RequestOverride"), json=patchData
            )
            return True
        except WiserHubException as ex:
            _LOGGER.debug("Set Home/Away Response code = {}".format(ex.status))
            raise WiserException(
                "InvalidResponse",
                "Error setting Home/Away to {}, error {} {}".format(
                    mode, ex.status, ex.message
                )
            )

    async def asyncSetHotwaterMode(self, mode, HwOnTemp=110):
        """
          Switch Hot Water on or off manually, or reset to 'Auto' (schedule).
          'mode' can be "on", "off" or "auto".
        """
        #Test if function available on this hub
        if self.hotwater:
            HWmodeMapping = {
                "on": {
                    "RequestOverride": {
                        "Type": "Manual",
                        "SetPoint": self._toWiserTemp(HwOnTemp),
                    }
                },
                "off": {
                    "RequestOverride": {
                        "Type": "Manual",
                        "SetPoint": self._toWiserTemp(TEMP_OFF),
                    }
                },
                "auto": {"RequestOverride": {"Type": "None", "Mode": "Auto"}},
            }

            if mode.lower() not in HWmodeMapping:
                raise WiserException(
                    "InvalidMode",
                    "Hot Water can be either 'on', 'off' or 'auto' - not {}".format(
                        mode.lower()
                    )
                )
            try:
                await self.request(
                    "patch",
                    path=WISERHOTWATER.format(self._hotwater[0].get("id")),
                    json=HWmodeMapping.get(mode.lower()),
                )
                return True
            except WiserHubException as ex:
                _LOGGER.debug("Set hot water response code = {}".format(ex.status))
                raise WiserException(
                    "InvalidResponse",
                    "Error setting hot water mode to {}, error {} {}".format(
                        mode, ex.status, ex.message
                    )
                )
        else:
            raise WiserException(
                "NotAvailable",
                "Hot water is not available on this Wiser hub.")

    async def asyncSetSystemSwitch(self, switch, mode=False):
        """
        Sets a system switch. For details of which switches to set look at the System section of the payload from the wiserhub
        :param switch: Name of Switch
        :param mode: Value of mode
        :return:
        """

        if switch not in self.system:
            raise WiserException(
                    "InvalidSwitch",
                    "System switch {} does not exist on your hub.".format(switch)
            )
        try:
            await self.request("patch", path=WISERSYSTEM.format(""), json={switch: mode.lower()})
            return True
        except WiserHubException as ex:
            _LOGGER.debug("Set system switch response code = {}".format(ex.status))
            raise WiserException(
                    "InvalidResponse",
                    "Error setting system switch {} to {}, error {} {}".format(
                    switch, mode, ex.status, ex.message
                )
            )

    async def asyncSetRoomSchedule(self, roomId, scheduleData: dict):
        """
        Sets Room Schedule

        param roomId:
        param scheduleData: json data for schedule
        return:
        """
        scheduleId = self.room(roomId).get("ScheduleId")

        if scheduleId is not None:
            try:
                await self.request(
                    "patch", path=WISERSCHEDULE.format(scheduleId), json=scheduleData
                )
                return True
            except WiserHubException as ex:
                _LOGGER.debug("Set Schedule Response code = {}".format(ex.status))
                raise WiserException(
                    "InvalidResponse",
                    "Error setting schedule for room {} , error {} {}".format(
                        roomId, ex.status, ex.message
                    )
                )
        else:
            raise WiserException(
                    "InvalidRoomSchedule",
                    "No schedule found that matches roomId")

    async def asyncSetRoomScheduleFromFile(self, roomId, scheduleFile: str):
        """
        Sets Room Schedule

        param roomId:
        param scheduleData: json data for schedule
        return:
        """
        scheduleId = self.room(roomId).get("ScheduleId")
        scheduleData = ""

        if scheduleId is not None:
            if os.path.exists(scheduleFile):
                try:
                    async with aiofiles.open(scheduleFile, "r") as f:
                        scheduleData = await f.read()
                        await json.loads(scheduleData)
                except:
                    raise WiserException(
                            "ErrorReadingFile",
                            "Error reading file - {}".format(scheduleFile))
                await self.asyncSetRoomSchedule(roomId, scheduleData)
                return True
            else:
                raise WiserException(
                        "FileNotFound",
                        "Schedule file, {}, not found.".format(
                        os.path.abspath(scheduleFile)
                    )
                )
        else:
            raise WiserException(
                    "NoScheduleFoundForRoom",
                    "No schedule found that matches roomId")

    async def asyncCopyRoomSchedule(self, fromRoomId, toRoomId):
        """
        Copies Room Schedule from one room to another

        param fromRoomId:
        param toRoomId:
        return: boolean
        """
        scheduleData = self.roomSchedule(fromRoomId)
        if scheduleData != None:
            await self.asyncSetRoomSchedule(toRoomId, scheduleData)
            return True
        else:
            raise WiserException(
                    "InvalidRoom",
                    "Error copying schedule.  One of the room Ids is not valid")

    async def asyncSetRoomMode(self, roomId, mode, temperature=20, boost_time=30):
        """
        Set the Room Mode, this can be Auto, Manual, off or Boost. When you set the
        mode back to Auto it will automatically take the scheduled temperature.

        param roomId: RoomId
        param mode:  Mode (auto, manual off, or boost)
        param boost_temp:  If boosting enter the temperature here in C, can be between 5-30
        param boost_temp_time:  How long to boost for in minutes
        """
        mode = mode.lower()
        if self.room(roomId) is None:
            raise WiserException(
                    "InvalidRoom",
                    "Room {} does not exist".format(roomId))
        if mode == "manual":
            temperature = self._fromWiserTemp(self.room(roomId).get("CurrentSetPoint"))
            if temperature == TEMP_OFF:
                temperature = self._fromWiserTemp(
                    self.room(roomId).get("ScheduledSetPoint")
                )
                mode = "manual_set"
            # If temp is less than 5C then set to min temp
            if temperature < TEMP_MINIMUM:
                temperature = TEMP_MINIMUM
                mode = "manual_set"
        if mode in ["manual", "boost"]:
            if not self._checkTempRange(temperature):
                raise WiserException(
                        "InvalidTemp",
                        "Temperature is set to {}. Temperature can only be between {} and {}.".format(
                        temperature, TEMP_MINIMUM, TEMP_MAXIMUM
                    )
                )
        roomModeMapping = {
            "auto": {"Mode": "Auto"},
            "boost": {
                "RequestOverride": {
                    "Type": "Manual",
                    "DurationMinutes": boost_time,
                    "SetPoint": self._toWiserTemp(temperature),
                    "Originator": "App",
                }
            },
            "cancelboost": {
                "RequestOverride": {
                    "Type": "None",
                    "DurationMinutes": 0,
                    "SetPoint": 0,
                    "Originator": "App",
                }
            },
            "manual_set": {
                "RequestOverride": {
                    "Type": "Manual",
                    "SetPoint": self._toWiserTemp(temperature),
                },
                "Mode": "Manual",
            },
            "manual": {"Mode": "Manual"},
            "off": {
                "Mode": "Manual",
                "RequestOverride": {
                    "Type": "Manual",
                    "SetPoint": self._toWiserTemp(TEMP_OFF),
                },
            },
        }

        if not roomModeMapping.get(mode):
            raise WiserException(
                    "InvalidMode",
                    "Mode {} is not valid.  Modes are auto, boost, manual and off".format(
                    mode
                )
            )
        _LOGGER.info(
            "Setting room {} to mode {} and temp {} with data {}".format(
                roomId, mode.lower(), temperature, roomModeMapping.get(mode.lower())
            )
        )
        try:
            if mode != "boost":
                # Cancel boost
                await self.request(
                    "patch",
                    path=WISERROOM.format(roomId),
                    json=roomModeMapping.get("cancelboost"),
                )
            await self.request(
                "patch", path=WISERROOM.format(roomId), json=roomModeMapping.get(mode)
            )
            return True
        except WiserHubException as ex:
            if ex.status == 404:
                _LOGGER.debug("Set room mode, room not found error ")
                raise WiserException(
                    "InvalidDevice",
                    "Set room {} to mode {}, room not found error".format(roomId, mode)
                )
            else:
                _LOGGER.debug(
                    "Set room {} to {} response code = {}".format(
                        roomId, mode, ex.status
                    )
                )
                raise WiserException(
                    "ResponseError",
                    "Error setting room {} to mode {}, error {} {}".format(
                        roomId, mode, ex.status, ex.message
                    )
                )

    async def asyncSetRoomTemperature(self, roomId, temperature):
        """
        Sets the room temperature
        param roomId:  The Room ID
        param temperature:  The temperature in celcius from 5 to 30, -20 for Off
        """
        if not self._checkTempRange(temperature):
            raise WiserException(
                    "InvalidTemp",
                    "Temperature is set to {}. Temperature can only be between {} and {}.".format(
                    temperature, TEMP_MINIMUM, TEMP_MAXIMUM
                )
            )
        _LOGGER.info("Setting room {} to temp {}.".format(roomId, temperature))
        try:
            await self.request(
                "patch",
                path=WISERROOM.format(roomId),
                json={
                    "RequestOverride": {
                        "Type": "Manual",
                        "SetPoint": self._toWiserTemp(temperature),
                    }
                },
            )
            return True
        except WiserHubException as ex:
            if ex.status == 404:
                _LOGGER.debug("Set room temperature, room not found error ")
                raise WiserException(
                    "InvalidDevice",
                    "Set room temperature {} not found error".format(roomId)
                )
            else:
                _LOGGER.debug(
                    "Set room {} to {}C response code = {}".format(
                        roomId, self._toWiserTemp(temperature), ex.status
                    )
                )
                raise WiserException(
                    "ResponseError",
                    "Error setting room {} to {}C, error {} {}".format(
                        roomId, self._toWiserTemp(temperature), ex.status, ex.message
                    )
                )

    async def asyncSetSmartPlugState(self, smartPlugId, smartPlugState):
        """
        Switch smartplug on or off
        param smartPlugId: the id of smartplug
        param smartPlugState: On or Off
        """
        if smartPlugState.lower() not in ["on", "off"]:
            _LOGGER.debug("SmartPlug State must be either On or Off")
            raise WiserException(
                "InvalidMode",
                "SmartPlug State must be either On or Off")
        if self.smartPlug(smartPlugId) is None:
            raise WiserException(
                "InvalidDevice",
                "Smartplug {} does not exist".format(smartPlugId)
                )
        _LOGGER.debug(
            "Setting smartplug {} to {}".format(smartPlugId, smartPlugState.title())
        )
        try:
            await self.request(
                "patch",
                path=WISERPLUG.format(smartPlugId),
                json={"RequestOutput": smartPlugState.title()},
            )
            return True
        except WiserHubException as ex:
            if ex.status == 404:
                _LOGGER.debug("Set smart plug not found error ")
                raise WiserException(
                    "InvalidDevice",
                    "Set smart plug {} not found error".format(smartPlugId)
                )
            else:
                _LOGGER.debug(
                    "Set smartplug {} to {} response code = {}".format(
                        smartPlugId, smartPlugState.title(), ex.status
                    )
                )
                raise WiserException(
                    "ResponseError",
                    "Error setting smartplug {} to {}, error {} {}".format(
                        smartPlugId, smartPlugState.title(), ex.status, ex.message
                    )
                )

    async def asyncSetSmartPlugMode(self, smartPlugId, smartPlugMode):
        """
        Set smartplug to Auto or Manual
        param smartplugid: the id of smartplug
        param smartPlugMode: Manual or Auto
        """
        if smartPlugMode.title() not in ["Auto", "Manual"]:
            _LOGGER.error("SmartPlug Mode must be either Auto or Manual")
            raise WiserException(
                "InvalidMode",
                "SmartPlug Mode must be either Auto or Manual")
        try:
            await self.request(
                "patch",
                path=WISERPLUG.format(smartPlugId),
                json={"Mode": smartPlugMode.title()},
            )
            return True
        except WiserHubException as ex:
            if ex.status == 404:
                _LOGGER.debug("Set smart plug not found error ")
                raise WiserException(
                    "InvalidDevice",
                    "Set smart plug {} not found error".format(smartPlugId)
                )
            else:
                _LOGGER.debug(
                    "Set smartplug {} to {} response code = {}".format(
                        smartPlugId, smartPlugMode.lower(), ex.status
                    )
                )
                raise WiserException(
                    "ReponseError",
                    "Error setting smartplug {} to {}, error {} {}".format(
                        smartPlugId, smartPlugMode.lower(), ex.status, ex.message
                    )
                )
