#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import date, timedelta, datetime
import os
from threading import Timer
from cleep.exception import CommandError
from cleep.common import CATEGORIES
from cleep.core import CleepModule


class Alarmclock(CleepModule):
    """
    Alarmclock application
    """

    MODULE_LABEL = "Alarm clock"
    MODULE_AUTHOR = "Cleep"
    MODULE_VERSION = "1.0.0"
    MODULE_DEPS = []
    MODULE_DESCRIPTION = "Build your own smart alarm clock"
    MODULE_LONGDESCRIPTION = "Configure time to wake up everyday"
    MODULE_TAGS = ["wakeup", "music"]
    MODULE_CATEGORY = CATEGORIES.APPLICATION
    MODULE_URLINFO = "https://github.com/tangb/cleepapp-alarmclock"
    MODULE_URLHELP = None
    MODULE_URLSITE = None
    MODULE_URLBUGS = "https://github.com/tangb/cleepapp-alarmclock/issues"

    MODULE_CONFIG_FILE = "alarmclock.conf"
    DEFAULT_CONFIG = {}

    STORAGE_PATH = "/opt/cleep/modules/Alarmclock"
    WEEKDAYS_MAPPING = {
        0: "mon",
        1: "tue",
        2: "wed",
        3: "thu",
        4: "fri",
        5: "sat",
        6: "sun",
    }

    def __init__(self, bootstrap, debug_enabled):
        """
        Constructor

        Args:
            bootstrap (dict): bootstrap objects
            debug_enabled (bool): debug status
        """
        CleepModule.__init__(self, bootstrap, debug_enabled)

        self.today_is_non_working_day = False
        self.tomorrow = {
            "date": None,
            "is_non_working_day": False,
        }
        self.has_audioplayer = False
        self.audioplayer_uuid = None
        self.stop_timers = {}
        self.__scheduled_alarm_uuids = set()

        self.alarm_triggered_event = self._get_event("alarmclock.alarm.triggered")
        self.alarm_scheduled_event = self._get_event("alarmclock.alarm.scheduled")
        self.alarm_unscheduled_event = self._get_event("alarmclock.alarm.unscheduled")
        self.alarm_stopped_event = self._get_event("alarmclock.alarm.stopped")

    def _on_start(self):
        """
        Start module.
        Use this function to start your tasks.
        At this time all applications are started and should respond to your command requests.
        """
        self._set_today_is_non_working_day()
        self._set_tomorrow_is_non_working_day()

        self._schedule_alarm()

        self.has_audioplayer = self.is_module_loaded("audioplayer")
        self.logger.info("Audioplayer app installed: %s", self.has_audioplayer)

    def on_event(self, event):
        """
        Event received

        Args:
            event (MessageRequest): event data
        """
        if event["event"] == "parameters.time.now":
            # at midnight check if today is a non working day
            if event["params"]["hour"] == 0 and event["params"]["minute"] == 0:
                self._set_today_is_non_working_day()
                self._set_tomorrow_is_non_working_day()

            self._trigger_alarm(
                event["params"], self.WEEKDAYS_MAPPING[event["params"]["weekday"]]
            )

    def add_alarm(self, alarm_time, timeout, days, non_working_days, volume):
        """
        Add new alarm

        Args:
            alarm_time (dict): time to trigger alarm::

                {
                    hour (int): alarm hour
                    minute (int): alarm minute
                }

            timeout (int): alarm timeout (in minutes)
            days (dict): list of days to triger alarm::

                {
                    mon (bool),
                    tue (bool),
                    wed (bool),
                    thu (bool),
                    fri (bool),
                    sat (bool),
                    sun (bool),
                }

            non_working_days (bool): True to enable alarm on non working days
            volume (int): volume percentage

        Returns:
            string: created alarm identifier

        Raises:
            CommandError: if alarm creation failed
            MissingParameter: if parameter is missing
            InvalidParameter: if parameter has invalid value
        """
        self._check_parameters(
            [
                {
                    "name": "alarm_time",
                    "type": dict,
                    "value": alarm_time,
                    "validator": lambda v: len(v) > 0
                    and all(key in ["hour", "minute"] for key in v.keys())
                    and isinstance(v["hour"], int)
                    and isinstance(v["minute"], int),
                },
                {
                    "name": "days",
                    "type": dict,
                    "value": days,
                    "validator": Alarmclock._check_days_validator,
                    "message": 'Parameter "days" is invalid or no day is selected',
                },
                {"name": "non_working_days", "type": bool, "value": non_working_days},
                {
                    "name": "timeout",
                    "type": int,
                    "value": timeout,
                    "validator": lambda v: v >= 0,
                    "message": "Timeout must be greater or equal to 0",
                },
                {
                    "name": "volume",
                    "value": volume,
                    "type": int,
                    "validator": lambda v: v > 0 and v <= 100,
                    "message": "Volume must be between 1 and 100",
                },
            ]
        )

        alarm = {
            "type": "alarmclock",
            "name": "Alarm",
            "time": alarm_time,
            "days": days,
            "nonWorkingDays": non_working_days,
            "enabled": True,
            "timeout": timeout,
            "volume": volume,
        }
        created_alarm = self._add_device(alarm)
        if not created_alarm:
            raise CommandError("Error adding alarm")

        self._schedule_alarm()

        return created_alarm["uuid"]

    def remove_alarm(self, alarm_uuid):
        """
        Remove specified alarm

        Args:
            alarm_uuid (string): alarm identifier

        Raises:
            CommandError: if alarm deletion failed
            MissingParameter: if parameter is missing
            InvalidParameter: if parameter has invalid value

        """
        self._check_parameters(
            [
                {
                    "name": alarm_uuid,
                    "type": str,
                    "value": alarm_uuid,
                    "validator": lambda v: self._get_device(v) is not None,
                    "message": "Alarm does not exist",
                }
            ]
        )

        if not self._delete_device(alarm_uuid):
            raise CommandError("Error removing alarm")

    def toggle_alarm(self, alarm_uuid):
        """
        Toggle alarm enabling/disabling it

        Args:
            alarm_uuid (string): alarm identifier

        Returns:
            bool: True if alarm enabled, True if disabled
        """
        self._check_parameters(
            [
                {
                    "name": "alarm_uuid",
                    "type": str,
                    "value": alarm_uuid,
                    "validator": lambda v: self._get_device(v) is not None,
                    "message": "Alarm does not exist",
                }
            ]
        )

        alarm = self._get_device(alarm_uuid)
        enabled = not alarm["enabled"]
        updated = self._update_device(
            alarm_uuid,
            {
                "enabled": enabled,
            },
        )
        if not updated:
            raise CommandError("Error updating alarm")

        if enabled:
            self.__scheduled_alarm_uuids.add(alarm_uuid)
        else:
            self.__scheduled_alarm_uuids.remove(alarm_uuid)
        event = self.alarm_scheduled_event if enabled else self.alarm_unscheduled_event
        event.send(
            params={
                "hour": alarm["time"]["hour"],
                "minute": alarm["time"]["minute"],
                "timeout": alarm["timeout"],
                "volume": alarm["volume"],
                "count": len(self.__scheduled_alarm_uuids),
            },
            device_id=alarm_uuid,
        )

        return enabled

    @staticmethod
    def _check_days_validator(days):
        """
        Validate all days are present in specified dict

        Args:
            days (dict): list of days

        Returns:
            bool: True if days dict is valid
        """
        week_days_exists = all(
            day in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
            for day in days.keys()
        )
        at_least_one_day = any(days.values())
        return week_days_exists and at_least_one_day

    def _set_today_is_non_working_day(self):
        """
        Get from parameters if today is a non working day
        """
        try:
            resp = self.send_command("is_today_non_working_day", "parameters")
            if resp.error:
                raise Exception(resp.message)
            self.today_is_non_working_day = resp.data
        except Exception:
            self.logger.exception("Unable to know if today is a non working day")

    def _set_tomorrow_is_non_working_day(self):
        """
        Get from parameters if tomorrow is a non working day
        """
        try:
            self.tomorrow["date"] = date.today() + timedelta(days=1)
            resp = self.send_command(
                "is_non_working_day",
                "parameters",
                {"day": self.tomorrow["date"].isoformat()},
            )
            if resp.error:
                raise Exception(resp.message)
            self.tomorrow["is_non_working_day"] = resp.data
        except Exception:
            self.logger.exception("Unable to know if tomorrow is a non working day")

    def _trigger_alarm(self, current_time, weekday):
        """
        Trigger alarm if necessary

        Args:
            current_time: received time.now event parameters
            weekday (string): literal weekday with 3 first chars (mon, tue...)
        """
        alarms = self.get_module_devices()
        for alarm_uuid, alarm in alarms.items():
            if not alarm["nonWorkingDays"] and self.today_is_non_working_day:
                self.logger.debug(
                    "Alarm %s: dropped because non working days", alarm_uuid
                )
                continue
            if not alarm["enabled"]:
                self.logger.debug("Alarm %s: dropped because disabled", alarm_uuid)
                continue
            if not alarm["days"][weekday]:
                self.logger.debug(
                    "Alarm %s: dropped because disabled for this weekday", alarm_uuid
                )
                continue
            if (
                alarm["time"]["hour"] != current_time["hour"]
                or alarm["time"]["minute"] != current_time["minute"]
            ):
                self.logger.debug("Alarm %s: dropped because no alarm time", alarm_uuid)
                continue

            self.alarm_triggered_event.send(
                params={
                    "hour": alarm["time"]["hour"],
                    "minute": alarm["time"]["minute"],
                    "timeout": alarm["timeout"],
                    "volume": alarm["volume"],
                },
                device_id=alarm_uuid,
            )
            self._schedule_alarm()

            self.stop_timers[alarm_uuid] = Timer(
                alarm["timeout"] * 60, self._stop_alarm, [alarm_uuid]
            )
            self.logger.info("Trigger alarm %s", alarm_uuid)
            self.stop_timers[alarm_uuid].start()

    def _stop_alarm(self, alarm_uuid, snoozed=False):
        """
        Stop specified alarm

        Args:
            alarm_uuid (string): alarm identifier
            snoozed (bool): True if alarm was snoozed
        """
        self.logger.info("Alarm %s stopped", alarm_uuid)
        if self.stop_timers.get(alarm_uuid):
            self.stop_timers[alarm_uuid].cancel()
            del self.stop_timers[alarm_uuid]

        alarm = self._get_device(alarm_uuid)
        if not alarm:
            self.logger.warning(
                'Unable to stop alarm "%s": device not found', alarm_uuid
            )
            return

        self.alarm_stopped_event.send(
            params={
                "hour": alarm["time"]["hour"],
                "minute": alarm["time"]["minute"],
                "timeout": alarm["timeout"],
                "volume": alarm["volume"],
                "snoozed": snoozed,
            },
            device_id=alarm_uuid,
        )

    def _schedule_alarm(self):
        """
        Schedule alarm for today
        """
        now = datetime.now()
        tomorrow_weekday_literal = self.WEEKDAYS_MAPPING[
            self.tomorrow["date"].weekday()
        ]
        today_weekday_literal = self.WEEKDAYS_MAPPING[now.weekday()]
        alarms = self.get_module_devices()

        # check next alarm for today
        for alarm_uuid, alarm in alarms.items():
            if not alarm["nonWorkingDays"] and self.today_is_non_working_day:
                continue
            if not alarm["enabled"]:
                continue

            if (
                alarm["days"][today_weekday_literal]
                and alarm["time"]["hour"] >= now.hour
                and alarm["time"]["minute"] > now.minute
            ):
                self.__scheduled_alarm_uuids.add(alarm_uuid)
                self.alarm_scheduled_event.send(
                    params={
                        "hour": alarm["time"]["hour"],
                        "minute": alarm["time"]["minute"],
                        "timeout": alarm["timeout"],
                        "volume": alarm["volume"],
                        "count": len(self.__scheduled_alarm_uuids),
                    },
                    device_id=alarm_uuid,
                )
                return

        # check next alarm for tomorrow
        for alarm_uuid, alarm in alarms.items():
            if not alarm["nonWorkingDays"] and self.tomorrow["is_non_working_day"]:
                continue
            if not alarm["enabled"]:
                continue

            if alarm["days"][tomorrow_weekday_literal]:
                self.__scheduled_alarm_uuids.add(alarm_uuid)
                self.alarm_scheduled_event.send(
                    params={
                        "hour": alarm["time"]["hour"],
                        "minute": alarm["time"]["minute"],
                        "timeout": alarm["timeout"],
                        "volume": alarm["volume"],
                        "count": len(self.__scheduled_alarm_uuids),
                    },
                    device_id=alarm_uuid,
                )
                return
