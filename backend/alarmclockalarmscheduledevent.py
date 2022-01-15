#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.event import Event


class AlarmclockAlarmScheduledEvent(Event):
    """
    Alarmclock.alarm.scheduled event
    """

    EVENT_NAME = "alarmclock.alarm.scheduled"
    EVENT_PROPAGATE = True
    EVENT_PARAMS = ["hour", "minute", "timeout", "volume"]

    def __init__(self, params):
        """
        Constructor

        Args:
            params (dict): event parameters
        """
        Event.__init__(self, params)
