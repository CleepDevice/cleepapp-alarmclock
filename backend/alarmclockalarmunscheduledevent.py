#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.event import Event


class AlarmclockAlarmUnscheduledEvent(Event):
    """
    Alarmclock.alarm.unscheduled event
    """

    EVENT_NAME = "alarmclock.alarm.unscheduled"
    EVENT_PROPAGATE = True
    EVENT_PARAMS = ["hour", "minute", "timeout", "volume", "count", "repeat", "shuffle"]

    def __init__(self, params):
        """
        Constructor

        Args:
            params (dict): event parameters
        """
        Event.__init__(self, params)
