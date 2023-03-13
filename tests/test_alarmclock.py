#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import logging
import datetime
import sys

sys.path.append("../")
from backend.alarmclock import Alarmclock
from backend.alarmclockalarmtriggeredevent import AlarmclockAlarmTriggeredEvent
from backend.alarmclockalarmscheduledevent import AlarmclockAlarmScheduledEvent
from backend.alarmclockalarmunscheduledevent import AlarmclockAlarmUnscheduledEvent
from backend.alarmclockalarmstoppedevent import AlarmclockAlarmStoppedEvent
from backend.alarmscheduledtoalarmformatter import AlarmScheduledToAlarmFormatter
from backend.alarmunscheduledtoalarmformatter import AlarmUnscheduledToAlarmFormatter
from backend.alarmtriggeredtoalarmformatter import AlarmTriggeredToAlarmFormatter
from backend.alarmstoppedtoalarmformatter import AlarmStoppedToAlarmFormatter
from cleep.exception import (
    InvalidParameter,
    MissingParameter,
    CommandError,
    Unauthorized,
)
from cleep.libs.tests import session
from mock import Mock, patch, MagicMock


class TestsAlarmclock(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(
            level=logging.FATAL,
            format=u"%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s",
        )
        self.session = session.TestSession(self)

    def tearDown(self):
        self.session.clean()

    def init(self, start=True, mocks=True):
        self.module = self.session.setup(Alarmclock)

        if mocks:
            self.module._set_today_is_non_working_day = Mock()
            self.module._set_tomorrow_is_non_working_day = Mock()

        if start:
            self.session.start_module(self.module)

    def test__on_start(self):
        self.init(False)
        self.module._schedule_alarm = Mock()
        self.module.is_module_loaded = Mock(return_value=True)

        self.session.start_module(self.module)

        self.module._set_today_is_non_working_day.assert_called()
        self.module._set_tomorrow_is_non_working_day.assert_called()
        self.module._schedule_alarm.assert_called()
        self.assertTrue(self.module.has_audioplayer)

    def test__on_start_no_audioplayer(self):
        self.init(False)
        self.module._set_today_is_non_working_day = Mock()
        self.module._set_tomorrow_is_non_working_day = Mock()
        self.module._schedule_alarm = Mock()
        self.module.is_module_loaded = Mock(return_value=False)

        self.session.start_module(self.module)

        self.assertFalse(self.module.has_audioplayer)

    def test_on_event_unhandled_event(self):
        self.init()
        event = {
            "event": "an.unhandled.event",
        }

        self.module.on_event(event)

        self.assertEqual(self.module._set_today_is_non_working_day.call_count, 1)
        self.assertEqual(self.module._set_tomorrow_is_non_working_day.call_count, 1)

    def test_on_event_time_event_not_midnight(self):
        self.init()
        event = {
            "event": "parameters.time.now",
            "params": {
                "hour": 10,
                "minute": 10,
                "weekday_literal": "mon",
                "weekday": 0,
            },
        }

        self.module.on_event(event)

        self.assertEqual(self.module._set_today_is_non_working_day.call_count, 1)
        self.assertEqual(self.module._set_tomorrow_is_non_working_day.call_count, 1)

    def test_on_event_time_event_midnight(self):
        self.init()
        event = {
            "event": "parameters.time.now",
            "params": {
                "hour": 0,
                "minute": 0,
                "weekday_literal": "mon",
                "weekday": 0,
            },
        }

        self.module.on_event(event)

        self.assertEqual(self.module._set_today_is_non_working_day.call_count, 2)
        self.assertEqual(self.module._set_tomorrow_is_non_working_day.call_count, 2)

    def test_add_alarm(self):
        self.init()
        self.module._add_device = Mock(return_value={"uuid": "12345678"})
        time_ = {"hour": 1, "minute": 1}
        days = {
            "mon": True,
            "tue": False,
            "wed": True,
            "thu": False,
            "fri": True,
            "sat": False,
            "sun": True,
        }
        self.module.tomorrow = {
            "date": datetime.date(2021, 12, 16),
            "nonWorkingDay": False,
        }

        result = self.module.add_alarm(time_, 10, days, False, 50, False, False)

        self.assertEqual(result, "12345678")
        self.module._add_device.assert_called_with(
            {
                "time": time_,
                "timeout": 10,
                "days": days,
                "nonWorkingDays": False,
                "type": "alarmclock",
                "name": "Alarm",
                "enabled": True,
                "volume": 50,
                "repeat": False,
                "shuffle": False,
            }
        )

    def test_add_alarm_failed(self):
        self.init()
        self.module._add_device = Mock(return_value=None)
        time_ = {"hour": 1, "minute": 1}
        days = {
            "mon": True,
            "tue": False,
            "wed": True,
            "thu": False,
            "fri": True,
            "sat": False,
            "sun": True,
        }

        with self.assertRaises(CommandError) as cm:
            self.module.add_alarm(time_, 10, days, False, 50, False, False)
        self.assertEqual(str(cm.exception), "Error adding alarm")

    def test_add_alarm_invalid_parameters(self):
        self.init()
        self.module._add_device = Mock(return_value=None)
        time_ = {"hour": 1, "minute": 1}
        days = {
            "mon": True,
            "tue": False,
            "wed": True,
            "thu": False,
            "fri": True,
            "sat": False,
            "sun": True,
        }

        with self.assertRaises(MissingParameter) as cm:
            self.module.add_alarm(None, 10, days, False, 50, False, False)
        self.assertEqual(str(cm.exception), 'Parameter "alarm_time" is missing')
        with self.assertRaises(MissingParameter) as cm:
            self.module.add_alarm(time_, None, days, False, 50, False, False)
        self.assertEqual(str(cm.exception), 'Parameter "timeout" is missing')
        with self.assertRaises(MissingParameter) as cm:
            self.module.add_alarm(time_, 10, None, False, 50, False, False)
        self.assertEqual(str(cm.exception), 'Parameter "days" is missing')
        with self.assertRaises(MissingParameter) as cm:
            self.module.add_alarm(time_, 10, days, None, 50, False, False)
        self.assertEqual(str(cm.exception), 'Parameter "non_working_days" is missing')
        with self.assertRaises(MissingParameter) as cm:
            self.module.add_alarm(time_, 10, days, False, None, False, False)
        self.assertEqual(str(cm.exception), 'Parameter "volume" is missing')
        with self.assertRaises(MissingParameter) as cm:
            self.module.add_alarm(time_, 10, days, False, 50, None, False)
        self.assertEqual(str(cm.exception), 'Parameter "repeat" is missing')
        with self.assertRaises(MissingParameter) as cm:
            self.module.add_alarm(time_, 10, days, False, 50, False, None)
        self.assertEqual(str(cm.exception), 'Parameter "shuffle" is missing')

        with self.assertRaises(InvalidParameter) as cm:
            self.module.add_alarm({}, 10, days, False, 50, False, False)
        self.assertEqual(
            str(cm.exception), 'Parameter "alarm_time" is invalid (specified="{}")'
        )
        with self.assertRaises(InvalidParameter) as cm:
            self.module.add_alarm(
                {"hour": 1, "minutes": 1}, 10, days, False, 50, False, False
            )
        self.assertEqual(
            str(cm.exception),
            "Parameter \"alarm_time\" is invalid (specified=\"{'hour': 1, 'minutes': 1}\")",
        )
        with self.assertRaises(InvalidParameter) as cm:
            self.module.add_alarm(
                {"hour": 1, "minutes": "1"}, 10, days, False, 50, False, False
            )
        self.assertEqual(
            str(cm.exception),
            "Parameter \"alarm_time\" is invalid (specified=\"{'hour': 1, 'minutes': '1'}\")",
        )

        with self.assertRaises(InvalidParameter) as cm:
            self.module.add_alarm(
                time_, 10, {"mon": True, "other": True}, False, 50, False, False
            )
        self.assertEqual(
            str(cm.exception), 'Parameter "days" is invalid or no day is selected'
        )
        with self.assertRaises(InvalidParameter) as cm:
            self.module.add_alarm(
                time_,
                10,
                {
                    "mon": False,
                    "tue": False,
                    "wed": False,
                    "thu": False,
                    "fri": False,
                    "sat": False,
                    "sun": False,
                },
                False,
                50,
                False,
                False,
            )
        self.assertEqual(
            str(cm.exception), 'Parameter "days" is invalid or no day is selected'
        )

        with self.assertRaises(InvalidParameter) as cm:
            self.module.add_alarm(time_, -2, days, False, 50, False, False)
        self.assertEqual(str(cm.exception), "Timeout must be greater or equal to 0")

        with self.assertRaises(InvalidParameter) as cm:
            self.module.add_alarm(time_, 10, days, False, 0, False, False)
        self.assertEqual(str(cm.exception), "Volume must be between 1 and 100")
        with self.assertRaises(InvalidParameter) as cm:
            self.module.add_alarm(time_, 10, days, False, 101, False, False)
        self.assertEqual(str(cm.exception), "Volume must be between 1 and 100")

    def test_remove_alarm(self):
        self.init()
        self.module._get_device = Mock(return_value={})
        self.module._delete_device = Mock(return_value=True)
        alarm = {
            "time": {"hour": 1, "minute": 1},
            "timeout": 10,
            "enabled": True,
            "volume": 50,
            "repeat": False,
            "shuffle": False,
        }
        self.module._get_device = Mock(return_value=alarm)
        self.module._Alarmclock__scheduled_alarm_uuids = set(("123456789",))

        self.module.remove_alarm("123456789")

        self.module._delete_device.assert_called_with("123456789")
        self.assertEqual(len(self.module._Alarmclock__scheduled_alarm_uuids), 0)
        self.session.assert_event_called_with(
            "alarmclock.alarm.unscheduled",
            {
                "hour": 1,
                "minute": 1,
                "timeout": 10,
                "volume": 50,
                "count": 0,
                "repeat": False,
                "shuffle": False,
            },
        )

    def test_remove_alarm_failed(self):
        self.init()
        self.module._get_device = Mock(return_value={})
        self.module._delete_device = Mock(return_value=False)

        with self.assertRaises(CommandError) as cm:
            self.module.remove_alarm("123456789")
        self.assertEqual(str(cm.exception), "Error removing alarm")

    def test_remove_alarm_check_parameters(self):
        self.init()
        self.module._get_device = Mock(return_value=None)

        with self.assertRaises(InvalidParameter) as cm:
            self.module.remove_alarm("123456789")
        self.assertEqual(str(cm.exception), "Alarm does not exist")

    def test_toggle_alarm_disable(self):
        self.init()
        self.module._Alarmclock__scheduled_alarm_uuids = set(("123456789",))
        alarm = {
            "time": {"hour": 1, "minute": 1},
            "timeout": 10,
            "enabled": True,
            "volume": 50,
            "repeat": False,
            "shuffle": False,
        }
        self.module._get_device = Mock(return_value=alarm)
        self.module._update_device = Mock(return_value=True)

        enabled = self.module.toggle_alarm("123456789")

        self.assertFalse(enabled)
        self.module._update_device.assert_called_with("123456789", {"enabled": False})
        self.session.assert_event_called_with(
            "alarmclock.alarm.unscheduled",
            {
                "hour": 1,
                "minute": 1,
                "timeout": 10,
                "volume": 50,
                "count": 0,
                "repeat": False,
                "shuffle": False,
            },
        )
        self.assertFalse(self.session.event_called("alarmclock.alarm.scheduled"))

    def test_toggle_alarm_enable(self):
        self.init()
        alarm = {
            "time": {"hour": 1, "minute": 1},
            "timeout": 10,
            "enabled": False,
            "volume": 50,
            "repeat": False,
            "shuffle": False,
        }
        self.module._get_device = Mock(return_value=alarm)
        self.module._update_device = Mock(return_value=True)

        enabled = self.module.toggle_alarm("123456789")

        self.assertTrue(enabled)
        self.module._update_device.assert_called_with("123456789", {"enabled": True})
        self.session.assert_event_called_with(
            "alarmclock.alarm.scheduled",
            {
                "hour": 1,
                "minute": 1,
                "timeout": 10,
                "volume": 50,
                "count": 1,
                "repeat": False,
                "shuffle": False,
            },
        )
        self.assertFalse(self.session.event_called("alarmclock.alarm.unscheduled"))

    def test_toggle_alarm_failed(self):
        self.init()
        alarm = {
            "time": {"hour": 1, "minute": 1},
            "timeout": 10,
            "enabled": True,
            "volume": 10,
        }
        self.module._get_device = Mock(return_value=alarm)
        self.module._update_device = Mock(return_value=False)

        with self.assertRaises(CommandError) as cm:
            self.module.toggle_alarm("123456789")
        self.assertEqual(str(cm.exception), "Error updating alarm")

    def test_toggle_alarm_check_parameters(self):
        self.init()
        self.module._get_device = Mock(return_value=None)

        with self.assertRaises(InvalidParameter) as cm:
            self.module.toggle_alarm("123456789")
        self.assertEqual(str(cm.exception), "Alarm does not exist")

    def test__set_today_is_non_working_day(self):
        self.init(start=False, mocks=False)
        is_today_non_working_day_mock = self.session.make_mock_command(
            "is_today_non_working_day", True
        )
        self.session.add_mock_command(is_today_non_working_day_mock)
        self.module._set_tomorrow_is_non_working_day = Mock()
        self.session.start_module(self.module)

        self.module._set_today_is_non_working_day()

        self.assertTrue(self.module.today_is_non_working_day)
        self.session.assert_command_called_with(
            "is_today_non_working_day", None, to="parameters"
        )

    def test__set_today_is_non_working_day_failed(self):
        self.init(start=False, mocks=False)
        is_today_non_working_day_mock = self.session.make_mock_command(
            "is_today_non_working_day", True, fail=True
        )
        self.session.add_mock_command(is_today_non_working_day_mock)
        self.module._set_tomorrow_is_non_working_day = Mock()
        self.session.start_module(self.module)
        self.module._set_tomorrow_is_non_working_day = Mock()

        try:
            self.module._set_today_is_non_working_day()
        except:
            self.fail("_set_today_is_non_working_day should not raise exception")

    @patch("backend.alarmclock.date")
    def test__set_tomorrow_is_non_working_day(self, date_mock):
        today = datetime.date(2021, 12, 15)
        date_mock.today.return_value = today
        self.init(start=False, mocks=False)
        is_module_loaded = self.session.make_mock_command("is_module_loaded", True)
        self.session.add_mock_command(is_module_loaded)
        is_non_working_day_mock = self.session.make_mock_command(
            "is_non_working_day", True
        )
        self.session.add_mock_command(is_non_working_day_mock)
        self.module._set_today_is_non_working_day = Mock()
        self.session.start_module(self.module)

        self.module._set_tomorrow_is_non_working_day()

        self.assertTrue(self.module.tomorrow["is_non_working_day"])
        self.assertEqual(self.module.tomorrow["date"], datetime.date(2021, 12, 16))
        self.session.assert_command_called_with(
            "is_non_working_day", {"day": "2021-12-16"}, to="parameters"
        )

    @patch("backend.alarmclock.date")
    def test__set_tomorrow_is_non_working_day_failed(self, date_mock):
        today = datetime.date(2021, 12, 15)
        date_mock.today.return_value = today
        self.init(start=False, mocks=False)
        is_module_loaded = self.session.make_mock_command("is_module_loaded", True)
        self.session.add_mock_command(is_module_loaded)
        is_non_working_day_mock = self.session.make_mock_command(
            "is_non_working_day", True, fail=True
        )
        self.session.add_mock_command(is_non_working_day_mock)
        self.module._set_today_is_non_working_day = Mock()
        self.session.start_module(self.module)

        try:
            self.module._set_tomorrow_is_non_working_day()
        except:
            self.fail("_set_tomorrow_is_non_working_day should not raise exception")

    @patch("backend.alarmclock.Timer")
    def test__trigger_alarm(self, timer_mock):
        self.init()
        alarm = self.module._add_device(
            {
                "type": "alarmclock",
                "name": "Alarm",
                "enabled": True,
                "nonWorkingDays": True,
                "time": {
                    "hour": 12,
                    "minute": 0,
                },
                "timeout": 10,
                "days": {
                    "mon": True,
                    "tue": True,
                    "wed": True,
                    "thu": True,
                    "fri": True,
                    "sat": True,
                    "sun": True,
                },
                "volume": 50,
                "repeat": False,
                "shuffle": False,
            }
        )
        self.module.tomorrow = {
            "date": datetime.date(2021, 12, 16),
            "nonWorkingDay": False,
        }

        self.module._trigger_alarm({"hour": 12, "minute": 0}, "tue")

        self.session.assert_event_called_with(
            "alarmclock.alarm.triggered",
            {
                "hour": 12,
                "minute": 0,
                "timeout": 10,
                "volume": 50,
                "repeat": False,
                "shuffle": False,
            },
        )
        timer_mock.assert_called_with(600, self.module._stop_alarm, [alarm["uuid"]])

    def test__trigger_alarm_with_alarm_disabled(self):
        self.init()
        self.module._add_device(
            {
                "type": "alarmclock",
                "name": "Alarm",
                "enabled": False,
                "nonWorkingDays": True,
                "time": {
                    "hour": 12,
                    "minute": 0,
                },
                "timeout": 10,
                "days": {
                    "mon": True,
                    "tue": True,
                    "wed": True,
                    "thu": True,
                    "fri": True,
                    "sat": True,
                    "sun": True,
                },
                "repeat": False,
                "shuffle": False,
            }
        )
        self.module.tomorrow = {
            "date": datetime.date(2021, 12, 16),
            "nonWorkingDay": False,
        }

        self.module._trigger_alarm({"hour": 12, "minute": 0}, "tue")

        self.assertEqual(self.session.event_call_count("alarmclock.alarm.triggered"), 0)

    def test__trigger_alarm_with_not_good_time(self):
        self.init()
        self.module._add_device(
            {
                "type": "alarmclock",
                "name": "Alarm",
                "enabled": True,
                "nonWorkingDays": True,
                "time": {
                    "hour": 12,
                    "minute": 12,
                },
                "timeout": 10,
                "days": {
                    "mon": True,
                    "tue": True,
                    "wed": True,
                    "thu": True,
                    "fri": True,
                    "sat": True,
                    "sun": True,
                },
                "repeat": False,
                "shuffle": False,
            }
        )
        self.module.tomorrow = {
            "date": datetime.date(2021, 12, 16),
            "nonWorkingDay": False,
        }

        self.module._trigger_alarm({"hour": 12, "minute": 0}, "tue")

        self.assertEqual(self.session.event_call_count("alarmclock.alarm.triggered"), 0)

    def test__trigger_alarm_on_working_day(self):
        self.init()
        self.module._add_device(
            {
                "type": "alarmclock",
                "name": "Alarm",
                "enabled": True,
                "nonWorkingDays": False,
                "time": {
                    "hour": 12,
                    "minute": 0,
                },
                "timeout": 10,
                "days": {
                    "mon": True,
                    "tue": True,
                    "wed": True,
                    "thu": True,
                    "fri": True,
                    "sat": True,
                    "sun": True,
                },
                "repeat": False,
                "shuffle": False,
            }
        )
        self.module.tomorrow = {
            "date": datetime.date(2021, 12, 16),
            "nonWorkingDay": False,
        }
        self.module.today_is_non_working_day = True

        self.module._trigger_alarm({"hour": 12, "minute": 0}, "tue")

        self.assertEqual(self.session.event_call_count("alarmclock.alarm.triggered"), 0)

    def test__trigger_alarm_on_disabled_day(self):
        self.init()
        self.module._add_device(
            {
                "type": "alarmclock",
                "name": "Alarm",
                "enabled": True,
                "nonWorkingDays": True,
                "time": {
                    "hour": 12,
                    "minute": 0,
                },
                "timeout": 10,
                "days": {
                    "mon": True,
                    "tue": False,
                    "wed": True,
                    "thu": True,
                    "fri": True,
                    "sat": True,
                    "sun": True,
                },
                "repeat": False,
                "shuffle": False,
            }
        )
        self.module.tomorrow = {
            "date": datetime.date(2021, 12, 16),
            "nonWorkingDay": False,
        }
        self.module.today_is_non_working_day = True

        self.module._trigger_alarm({"hour": 12, "minute": 0}, "tue")

        self.assertEqual(self.session.event_call_count("alarmclock.alarm.triggered"), 0)

    def test__stop_alarm(self):
        self.init()
        device = {
            "name": "Alarm",
            "type": "alarmclock",
            "time": {
                "hour": 12,
                "minute": 0,
            },
            "enabled": True,
            "timeout": 10,
            "volume": 50,
        }
        self.module._get_device = Mock(return_value=device)
        timer_mock = Mock()
        self.module.stop_timers["1234567789"] = timer_mock

        self.module._stop_alarm("1234567789")

        self.session.assert_event_called_with(
            "alarmclock.alarm.stopped",
            {
                "hour": 12,
                "minute": 0,
                "timeout": 10,
                "snoozed": False,
                "volume": 50,
            },
        )
        timer_mock.cancel.assert_called()
        self.assertEqual(len(self.module.stop_timers.keys()), 0)

    def test__stop_alarm_alarm_not_found(self):
        self.init()
        self.module._get_device = Mock(return_value=None)

        self.module._stop_alarm("1234567789")

        self.assertEqual(self.session.event_call_count("alarmclock.alarm.stopped"), 0)

    @patch("backend.alarmclock.datetime")
    def test__schedule_alarm_for_today(self, datetime_mock):
        datetime_mock.now.return_value = datetime.datetime(2021, 12, 16, 12, 0)
        self.init()
        self.module._add_device(
            {
                "type": "alarmclock",
                "name": "Alarm",
                "enabled": True,
                "nonWorkingDays": False,
                "time": {
                    "hour": 12,
                    "minute": 10,
                },
                "timeout": 10,
                "days": {
                    "mon": True,
                    "tue": True,
                    "wed": True,
                    "thu": True,
                    "fri": True,
                    "sat": True,
                    "sun": True,
                },
                "volume": 50,
                "repeat": False,
                "shuffle": False,
            }
        )
        self.module.today_is_non_working_day = False
        self.module.tomorrow = {
            "date": datetime.date(2021, 12, 17),
            "is_non_working_day": False,
        }

        self.module._schedule_alarm()

        self.session.assert_event_called_with(
            "alarmclock.alarm.scheduled",
            {
                "hour": 12,
                "minute": 10,
                "timeout": 10,
                "volume": 50,
                "count": 1,
                "repeat": False,
                "shuffle": False,
            },
        )
        self.assertEqual(self.session.event_call_count("alarmclock.alarm.scheduled"), 1)

    @patch("backend.alarmclock.datetime")
    def test__schedule_alarm_for_today_but_disabled(self, datetime_mock):
        datetime_mock.now.return_value = datetime.datetime(2021, 12, 16, 12, 0)
        self.init()
        self.module._add_device(
            {
                "type": "alarmclock",
                "name": "Alarm",
                "enabled": False,
                "nonWorkingDays": False,
                "time": {
                    "hour": 12,
                    "minute": 10,
                },
                "timeout": 10,
                "days": {
                    "mon": True,
                    "tue": True,
                    "wed": True,
                    "thu": True,
                    "fri": True,
                    "sat": True,
                    "sun": True,
                },
                "repeat": False,
                "shuffle": False,
            }
        )
        self.module.today_is_non_working_day = False
        self.module.tomorrow = {
            "date": datetime.date(2021, 12, 17),
            "is_non_working_day": False,
        }

        self.module._schedule_alarm()

        self.assertEqual(self.session.event_call_count("alarmclock.alarm.scheduled"), 0)

    @patch("backend.alarmclock.datetime")
    def test__schedule_alarm_for_today_but_non_working_day(self, datetime_mock):
        datetime_mock.now.return_value = datetime.datetime(2021, 12, 16, 12, 0)
        self.init()
        self.module._add_device(
            {
                "type": "alarmclock",
                "name": "Alarm",
                "enabled": True,
                "nonWorkingDays": False,
                "time": {
                    "hour": 12,
                    "minute": 10,
                },
                "timeout": 10,
                "days": {
                    "mon": True,
                    "tue": True,
                    "wed": True,
                    "thu": True,
                    "fri": True,
                    "sat": True,
                    "sun": True,
                },
                "repeat": False,
                "shuffle": False,
            }
        )
        self.module.today_is_non_working_day = True
        self.module.tomorrow = {
            "date": datetime.date(2021, 12, 17),
            "is_non_working_day": True,
        }

        self.module._schedule_alarm()

        self.assertEqual(self.session.event_call_count("alarmclock.alarm.scheduled"), 0)

    @patch("backend.alarmclock.datetime")
    def test__schedule_alarm_for_tomorrow(self, datetime_mock):
        datetime_mock.now.return_value = datetime.datetime(2021, 12, 16, 12, 0)
        self.init()
        self.module._add_device(
            {
                "type": "alarmclock",
                "name": "Alarm",
                "enabled": True,
                "nonWorkingDays": False,
                "time": {
                    "hour": 12,
                    "minute": 10,
                },
                "timeout": 10,
                "days": {
                    "mon": True,
                    "tue": True,
                    "wed": True,
                    "thu": False,
                    "fri": True,
                    "sat": True,
                    "sun": True,
                },
                "volume": 50,
                "repeat": False,
                "shuffle": False,
            }
        )
        self.module.today_is_non_working_day = False
        self.module.tomorrow = {
            "date": datetime.date(2021, 12, 17),
            "is_non_working_day": False,
        }

        self.module._schedule_alarm()

        self.session.assert_event_called_with(
            "alarmclock.alarm.scheduled",
            {
                "hour": 12,
                "minute": 10,
                "timeout": 10,
                "volume": 50,
                "count": 1,
                "repeat": False,
                "shuffle": False,
            },
        )
        self.assertEqual(self.session.event_call_count("alarmclock.alarm.scheduled"), 1)

    @patch("backend.alarmclock.datetime")
    def test__schedule_alarm_for_tomorrow_but_disabled(self, datetime_mock):
        datetime_mock.now.return_value = datetime.datetime(2021, 12, 16, 12, 0)
        self.init()
        self.module._add_device(
            {
                "type": "alarmclock",
                "name": "Alarm",
                "enabled": False,
                "nonWorkingDays": False,
                "time": {
                    "hour": 12,
                    "minute": 10,
                },
                "timeout": 10,
                "days": {
                    "mon": True,
                    "tue": True,
                    "wed": True,
                    "thu": False,
                    "fri": True,
                    "sat": True,
                    "sun": True,
                },
                "repeat": False,
                "shuffle": False,
            }
        )
        self.module.today_is_non_working_day = False
        self.module.tomorrow = {
            "date": datetime.date(2021, 12, 17),
            "is_non_working_day": False,
        }

        self.module._schedule_alarm()

        self.assertEqual(self.session.event_call_count("alarmclock.alarm.scheduled"), 0)

    @patch("backend.alarmclock.datetime")
    def test__schedule_alarm_for_tomorrow_but_non_working_day(self, datetime_mock):
        datetime_mock.now.return_value = datetime.datetime(2021, 12, 16, 12, 0)
        self.init()
        self.module._add_device(
            {
                "type": "alarmclock",
                "name": "Alarm",
                "enabled": False,
                "nonWorkingDays": False,
                "time": {
                    "hour": 12,
                    "minute": 10,
                },
                "timeout": 10,
                "days": {
                    "mon": True,
                    "tue": True,
                    "wed": True,
                    "thu": False,
                    "fri": True,
                    "sat": True,
                    "sun": True,
                },
                "repeat": False,
                "shuffle": False,
            }
        )
        self.module.today_is_non_working_day = False
        self.module.tomorrow = {
            "date": datetime.date(2021, 12, 17),
            "is_non_working_day": True,
        }

        self.module._schedule_alarm()

        self.assertEqual(self.session.event_call_count("alarmclock.alarm.scheduled"), 0)

    @patch("backend.alarmclock.datetime")
    def test__schedule_alarm_alarms_for_today_and_tomorrow(self, datetime_mock):
        datetime_mock.now.return_value = datetime.datetime(2021, 12, 16, 12, 0)
        self.init()
        self.module._add_device(
            {
                "type": "alarmclock",
                "name": "Alarm",
                "enabled": True,
                "nonWorkingDays": True,
                "time": {
                    "hour": 14,
                    "minute": 10,
                },
                "timeout": 10,
                "volume": 50,
                "days": {
                    "mon": True,
                    "tue": True,
                    "wed": True,
                    "thu": True,
                    "fri": True,
                    "sat": True,
                    "sun": True,
                },
                "repeat": False,
                "shuffle": False,
            }
        )
        self.module._add_device(
            {
                "type": "alarmclock",
                "name": "Alarm",
                "enabled": True,
                "nonWorkingDays": True,
                "time": {
                    "hour": 10,
                    "minute": 10,
                },
                "timeout": 10,
                "volume": 50,
                "days": {
                    "mon": True,
                    "tue": True,
                    "wed": True,
                    "thu": True,
                    "fri": True,
                    "sat": True,
                    "sun": True,
                },
                "repeat": False,
                "shuffle": False,
            }
        )
        self.module.tomorrow = {
            "date": datetime.date(2021, 12, 17),
            "is_non_working_day": False,
        }

        self.module._schedule_alarm()

        self.assertEqual(self.session.event_call_count("alarmclock.alarm.scheduled"), 2)

    @patch("backend.alarmclock.datetime")
    def test__schedule_alarm_no_alarm_for_today_and_tomorrow(self, datetime_mock):
        datetime_mock.now.return_value = datetime.datetime(2021, 12, 16, 12, 0)
        self.init()
        self.module._add_device(
            {
                "type": "alarmclock",
                "name": "Alarm",
                "enabled": False,
                "nonWorkingDays": True,
                "time": {
                    "hour": 12,
                    "minute": 10,
                },
                "timeout": 10,
                "days": {
                    "mon": True,
                    "tue": True,
                    "wed": True,
                    "thu": False,
                    "fri": False,
                    "sat": True,
                    "sun": True,
                },
                "repeat": False,
                "shuffle": False,
            }
        )
        self.module.tomorrow = {
            "date": datetime.date(2021, 12, 17),
            "is_non_working_day": False,
        }

        self.module._schedule_alarm()

        self.assertEqual(self.session.event_call_count("alarmclock.alarm.scheduled"), 0)


class TestAlarmclockAlarmTriggeredEvent(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(
            level=logging.FATAL,
            format="%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s",
        )
        self.session = session.TestSession(self)
        self.event = self.session.setup_event(AlarmclockAlarmTriggeredEvent)

    def test_event_params(self):
        self.assertEqual(
            self.event.EVENT_PARAMS,
            [
                "hour",
                "minute",
                "timeout",
                "volume",
                "repeat",
                "shuffle",
            ],
        )


class TestAlarmclockAlarmScheduledEvent(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(
            level=logging.FATAL,
            format="%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s",
        )
        self.session = session.TestSession(self)
        self.event = self.session.setup_event(AlarmclockAlarmScheduledEvent)

    def test_event_params(self):
        self.assertEqual(
            self.event.EVENT_PARAMS,
            [
                "hour",
                "minute",
                "timeout",
                "volume",
                "count",
                "repeat",
                "shuffle",
            ],
        )


class TestAlarmclockAlarmUnscheduledEvent(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(
            level=logging.FATAL,
            format="%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s",
        )
        self.session = session.TestSession(self)
        self.event = self.session.setup_event(AlarmclockAlarmUnscheduledEvent)

    def test_event_params(self):
        self.assertEqual(
            self.event.EVENT_PARAMS,
            [
                "hour",
                "minute",
                "timeout",
                "volume",
                "count",
                "repeat",
                "shuffle",
            ],
        )


class TestAlarmclockAlarmStoppedEvent(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(
            level=logging.FATAL,
            format="%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s",
        )
        self.session = session.TestSession(self)
        self.event = self.session.setup_event(AlarmclockAlarmStoppedEvent)

    def test_event_params(self):
        self.assertEqual(
            self.event.EVENT_PARAMS,
            [
                "hour",
                "minute",
                "timeout",
                "snoozed",
                "volume",
            ],
        )


class TestsAlarmScheduledToAlarmFormatter(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(
            level=logging.FATAL,
            format=u"%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s",
        )
        events_broker = Mock()
        self.formatter = AlarmScheduledToAlarmFormatter(
            {"events_broker": events_broker}
        )

    def test_fill_profile(self):
        event_params = {
            "hour": 12,
            "minute": 30,
            "timeout": 10,
            "volume": 50,
            "count": 2,
            "repeat": False,
            "shuffle": True,
        }
        profile_mock = Mock()
        profile = self.formatter._fill_profile(event_params, profile_mock)

        self.assertEqual(profile.hour, 12)
        self.assertEqual(profile.minute, 30)
        self.assertEqual(profile.timeout, 10)
        self.assertEqual(profile.volume, 50)
        self.assertEqual(profile.count, 2)
        self.assertEqual(profile.repeat, False)
        self.assertEqual(profile.shuffle, True)


class TestsAlarmUnscheduledToAlarmFormatter(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(
            level=logging.FATAL,
            format=u"%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s",
        )
        events_broker = Mock()
        self.formatter = AlarmUnscheduledToAlarmFormatter(
            {"events_broker": events_broker}
        )

    def test_fill_profile(self):
        event_params = {
            "hour": 12,
            "minute": 30,
            "timeout": 10,
            "volume": 50,
            "count": 2,
            "repeat": False,
            "shuffle": True,
        }
        profile_mock = Mock()
        profile = self.formatter._fill_profile(event_params, profile_mock)

        self.assertEqual(profile.hour, 12)
        self.assertEqual(profile.minute, 30)
        self.assertEqual(profile.timeout, 10)
        self.assertEqual(profile.volume, 50)
        self.assertEqual(profile.count, 2)
        self.assertEqual(profile.repeat, False)
        self.assertEqual(profile.shuffle, True)


class TestsAlarmTriggeredToAlarmFormatter(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(
            level=logging.FATAL,
            format=u"%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s",
        )
        events_broker = Mock()
        self.formatter = AlarmTriggeredToAlarmFormatter(
            {"events_broker": events_broker}
        )

    def test_fill_profile(self):
        event_params = {
            "hour": 12,
            "minute": 30,
            "timeout": 10,
            "volume": 50,
            "repeat": False,
            "shuffle": True,
        }
        profile_mock = Mock()
        profile = self.formatter._fill_profile(event_params, profile_mock)

        self.assertEqual(profile.hour, 12)
        self.assertEqual(profile.minute, 30)
        self.assertEqual(profile.timeout, 10)
        self.assertEqual(profile.volume, 50)
        self.assertEqual(profile.repeat, False)
        self.assertEqual(profile.shuffle, True)


class TestsAlarmStoppedToAlarmFormatter(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(
            level=logging.FATAL,
            format=u"%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s",
        )
        events_broker = Mock()
        self.formatter = AlarmStoppedToAlarmFormatter({"events_broker": events_broker})

    def test_fill_profile_snoozed(self):
        event_params = {
            "hour": 12,
            "minute": 30,
            "timeout": 10,
            "volume": 50,
            "snoozed": True,
        }
        profile_mock = Mock()
        profile = self.formatter._fill_profile(event_params, profile_mock)

        self.assertEqual(profile.hour, 12)
        self.assertEqual(profile.minute, 30)
        self.assertEqual(profile.timeout, 10)
        self.assertEqual(profile.volume, 50)
        self.assertEqual(profile.status, profile_mock.STATUS_SNOOZED)

    def test_fill_profile_stopped(self):
        event_params = {
            "hour": 12,
            "minute": 30,
            "timeout": 10,
            "volume": 50,
            "snoozed": False,
        }
        profile_mock = Mock()
        profile = self.formatter._fill_profile(event_params, profile_mock)

        self.assertEqual(profile.hour, 12)
        self.assertEqual(profile.minute, 30)
        self.assertEqual(profile.timeout, 10)
        self.assertEqual(profile.volume, 50)
        self.assertEqual(profile.status, profile_mock.STATUS_STOPPED)


if __name__ == "__main__":
    # coverage run --omit="*/lib/python*/*","test_*" --concurrency=thread test_alarmclock.py; coverage report -m -i
    unittest.main()
