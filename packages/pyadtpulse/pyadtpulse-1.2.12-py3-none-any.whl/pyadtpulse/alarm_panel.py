"""ADT Alarm Panel Dataclass."""

import re
import logging
from time import time
from asyncio import run_coroutine_threadsafe
from threading import RLock
from dataclasses import dataclass

from lxml import html
from typeguard import typechecked

from .util import make_etree
from .const import ADT_ARM_DISARM_URI
from .pulse_connection import PulseConnection

LOG = logging.getLogger(__name__)
ADT_ALARM_AWAY = "away"
ADT_ALARM_HOME = "stay"
ADT_ALARM_OFF = "off"
ADT_ALARM_UNKNOWN = "unknown"
ADT_ALARM_ARMING = "arming"
ADT_ALARM_DISARMING = "disarming"
ADT_ALARM_NIGHT = "night"

ALARM_STATUSES = (
    ADT_ALARM_AWAY,
    ADT_ALARM_HOME,
    ADT_ALARM_OFF,
    ADT_ALARM_UNKNOWN,
    ADT_ALARM_ARMING,
    ADT_ALARM_DISARMING,
    ADT_ALARM_NIGHT,
)

ALARM_POSSIBLE_STATUS_MAP = {
    "Disarmed": (ADT_ALARM_OFF, ADT_ALARM_ARMING),
    "Armed Away": (ADT_ALARM_AWAY, ADT_ALARM_DISARMING),
    "Armed Stay": (ADT_ALARM_HOME, ADT_ALARM_DISARMING),
    "Armed Night": (ADT_ALARM_NIGHT, ADT_ALARM_DISARMING),
}

ADT_ARM_DISARM_TIMEOUT: float = 20


@dataclass(slots=True)
class ADTPulseAlarmPanel:
    """ADT Alarm Panel information."""

    model: str = "Unknown"
    _sat: str = ""
    _status: str = "Unknown"
    manufacturer: str = "ADT"
    online: bool = True
    _is_force_armed: bool = False
    _state_lock = RLock()
    _last_arm_disarm: int = int(time())

    @property
    def status(self) -> str:
        """
        Get alarm status.

        Returns:
            str: the alarm status

        """
        with self._state_lock:
            return self._status

    @status.setter
    def status(self, new_status: str) -> None:
        """
        Set alarm status.

        Args:
            new_status (str): the new alarm status

        """
        with self._state_lock:
            if new_status not in ALARM_STATUSES:
                raise ValueError(f"Alarm status must be one of {ALARM_STATUSES}")
            self._status = new_status

    @property
    def is_away(self) -> bool:
        """
        Return wheter the system is armed away.

        Returns:
            bool: True if armed away

        """
        with self._state_lock:
            return self._status == ADT_ALARM_AWAY

    @property
    def is_home(self) -> bool:
        """
        Return whether system is armed at home/stay.

        Returns:
            bool: True if system is armed home/stay

        """
        with self._state_lock:
            return self._status == ADT_ALARM_HOME

    @property
    def is_disarmed(self) -> bool:
        """
        Return whether the system is disarmed.

        Returns:
            bool: True if the system is disarmed

        """
        with self._state_lock:
            return self._status == ADT_ALARM_OFF

    @property
    def is_force_armed(self) -> bool:
        """
        Return whether the system is armed in bypass mode.

        Returns:
            bool: True if system armed in bypass mode

        """
        with self._state_lock:
            return self._is_force_armed

    @property
    def is_arming(self) -> bool:
        """
        Return if system is attempting to arm.

        Returns:
            bool: True if system is attempting to arm

        """
        with self._state_lock:
            return self._status == ADT_ALARM_ARMING

    @property
    def is_disarming(self) -> bool:
        """
        Return if system is attempting to disarm.

        Returns:
            bool: True if system is attempting to disarm

        """
        with self._state_lock:
            return self._status == ADT_ALARM_DISARMING

    @property
    def is_armed_night(self) -> bool:
        """
        Return if system is in night mode.

        Returns:
            bool: True if system is in night mode

        """
        with self._state_lock:
            return self._status == ADT_ALARM_NIGHT

    @property
    def last_update(self) -> float:
        """
        Return last update time.

        Returns:
            float: last arm/disarm time

        """
        with self._state_lock:
            return self._last_arm_disarm

    @typechecked
    async def _arm(
        self, connection: PulseConnection, mode: str, force_arm: bool
    ) -> bool:
        """
        Set arm status.

        Args:
            connection (PulseConnection): the connection to use
            mode (str): the mode to set the alarm to
            force_arm (bool): True if arm force

        Returns:
            bool: True if operation successful

        """
        LOG.debug("Setting ADT alarm %s to %s, force = %s", self._sat, mode, force_arm)
        with self._state_lock:
            if self._status == mode:
                LOG.warning(
                    "Attempting to set alarm status %s to existing status %s",
                    mode,
                    self._status,
                )
            if ADT_ALARM_OFF not in (self._status, mode):
                LOG.warning("Cannot set alarm status from %s to %s", self._status, mode)
                return False
            params = {
                "href": "rest/adt/ui/client/security/setArmState",
                "armstate": self._status,  # existing state
                "arm": mode,  # new state
                "sat": self._sat,
            }
            if force_arm and mode != ADT_ALARM_OFF:
                params = {
                    "href": "rest/adt/ui/client/security/setForceArm",
                    "armstate": "forcearm",  # existing state
                    "arm": mode,  # new state
                    "sat": self._sat,
                }

            response = await connection.async_query(
                ADT_ARM_DISARM_URI,
                method="POST",
                extra_params=params,
                timeout=10,
            )

            tree = make_etree(
                response[0],
                response[1],
                response[2],
                logging.WARNING,
                f"Failed updating ADT Pulse alarm {self._sat} to {mode}",
            )
            if tree is None:
                return False

            arm_result = tree.find(
                path=".//div[@class='p_armDisarmWrapper']",
                namespaces=None,
            )
            if arm_result is not None:
                error_block = arm_result.find(".//div")
                if error_block is not None:
                    error_text = arm_result.text_content().replace(
                        "Arm AnywayCancel\n\n", ""
                    )
                    LOG.warning(
                        "Could not set alarm state to %s because %s", mode, error_text
                    )
                    return False
        self._is_force_armed = force_arm
        if mode == ADT_ALARM_OFF:
            self._status = ADT_ALARM_DISARMING
        else:
            self._status = ADT_ALARM_ARMING
        self._last_arm_disarm = int(time())
        return True

    @typechecked
    def _sync_set_alarm_mode(
        self,
        connection: PulseConnection,
        mode: str,
        force_arm: bool = False,
    ) -> bool:
        coro = self._arm(connection, mode, force_arm)
        return run_coroutine_threadsafe(
            coro,
            connection.check_sync(
                "Attempting to sync change alarm mode from async session"
            ),
        ).result()

    @typechecked
    def arm_away(self, connection: PulseConnection, force_arm: bool = False) -> bool:
        """
        Arm the alarm in Away mode.

        Args:
            connection (PulseConnection): the connection to use
            force_arm (bool, Optional): force system to arm

        Returns:
            bool: True if arm succeeded

        """
        return self._sync_set_alarm_mode(connection, ADT_ALARM_AWAY, force_arm)

    @typechecked
    def arm_night(self, connection: PulseConnection, force_arm: bool = False) -> bool:
        """
        Arm the alarm in Night mode.

        Args:
            connection (PulseConnection): the connection to use
            force_arm (bool, Optional): force system to arm

        Returns:
            bool: True if arm succeeded

        """
        return self._sync_set_alarm_mode(connection, ADT_ALARM_NIGHT, force_arm)

    @typechecked
    def arm_home(self, connection: PulseConnection, force_arm: bool = False) -> bool:
        """
        Arm the alarm in Home mode.

        Args:
            connection (PulseConnection): the connection to use
            force_arm (bool, Optional): force system to arm

        Returns:
            bool: True if arm succeeded

        """
        return self._sync_set_alarm_mode(connection, ADT_ALARM_HOME, force_arm)

    @typechecked
    def disarm(self, connection: PulseConnection) -> bool:
        """
        Disarm the alarm.

        Returns:
            bool: True if disarm succeeded

        """
        return self._sync_set_alarm_mode(connection, ADT_ALARM_OFF, False)

    @typechecked
    async def async_arm_away(
        self, connection: PulseConnection, force_arm: bool = False
    ) -> bool:
        """
        Arm alarm away async.

        Args:
            connection (PulseConnection): the connection to use
            force_arm (bool, Optional): force system to arm

        Returns:
            bool: True if arm succeeded

        """
        return await self._arm(connection, ADT_ALARM_AWAY, force_arm)

    @typechecked
    async def async_arm_home(
        self, connection: PulseConnection, force_arm: bool = False
    ) -> bool:
        """
        Arm alarm home async.

        Args:
            connection (PulseConnection): the connection to use
            force_arm (bool, Optional): force system to arm
        Returns:
            bool: True if arm succeeded

        """
        return await self._arm(connection, ADT_ALARM_HOME, force_arm)

    @typechecked
    async def async_arm_night(
        self, connection: PulseConnection, force_arm: bool = False
    ) -> bool:
        """
        Arm alarm night async.

        Args:
            connection (PulseConnection): the connection to use
            force_arm (bool, Optional): force system to arm
        Returns:
            bool: True if arm succeeded

        """
        return await self._arm(connection, ADT_ALARM_NIGHT, force_arm)

    @typechecked
    async def async_disarm(self, connection: PulseConnection) -> bool:
        """
        Disarm alarm async.

        Returns:
            bool: True if disarm succeeded

        """
        return await self._arm(connection, ADT_ALARM_OFF, False)

    @typechecked
    def update_alarm_from_etree(self, summary_html_etree: html.HtmlElement) -> None:
        """
        Update the alarm status extracted from the provided lxml etree.

        Args:
            summary_html_etree: html.HtmlElement: the parsed response tree.

        Returns:
            None: This function does not return anything.

        """
        LOG.debug("Updating alarm status")
        value = summary_html_etree.find(
            path=".//span[@class='p_boldNormalTextLarge']",
            namespaces=None,
        )
        sat_location = "security_button_0"
        with self._state_lock:
            status_found = False
            last_updated = int(time())
            if value is not None:
                text = value.text_content().lstrip().splitlines()[0]

                for (
                    current_status,
                    possible_statuses,
                ) in ALARM_POSSIBLE_STATUS_MAP.items():
                    if text.startswith(current_status):
                        status_found = True
                        if (
                            self._status != possible_statuses[1]
                            or last_updated - self._last_arm_disarm
                            > ADT_ARM_DISARM_TIMEOUT
                        ):
                            self._status = possible_statuses[0]
                            self._last_arm_disarm = last_updated
                        break

            if value is None or not status_found:
                if not text.startswith("Status Unavailable"):
                    LOG.warning("Failed to get alarm status from '%s'", text)
                self._status = ADT_ALARM_UNKNOWN
                self._last_arm_disarm = last_updated
                return
            LOG.debug("Alarm status = %s", self._status)
            sat_string = f'.//input[@id="{sat_location}"]'
            sat_button = summary_html_etree.find(
                path=sat_string,
                namespaces=None,
            )
            if sat_button is not None and "onclick" in sat_button.attrib:
                on_click = sat_button.attrib["onclick"]
                match = re.search(r"sat=([a-z0-9\-]+)", on_click)
                if match:
                    self._sat = match.group(1)
            if not self._sat:
                LOG.warning("No sat recorded and was unable to extract sat.")
            else:
                LOG.debug("Extracted sat = %s", self._sat)

    @typechecked
    def set_alarm_attributes(self, alarm_attributes: dict[str, str]) -> None:
        """
        Set alarm attributes including model, manufacturer, and online status.

        Args:
            self (object): The instance of the alarm.
            alarm_attributes (dict[str, str]): A dictionary containing alarm attributes.

        Returns:
            None

        """
        self.model = alarm_attributes.get("type_model", "Unknown")
        self.manufacturer = alarm_attributes.get("manufacturer_provider", "ADT")
        self.online = alarm_attributes.get("status", "Offline") == "Online"
        LOG.debug(
            "Set alarm attributes: Model = %s, Manufacturer = %s, Online = %s",
            self.model,
            self.manufacturer,
            self.online,
        )
