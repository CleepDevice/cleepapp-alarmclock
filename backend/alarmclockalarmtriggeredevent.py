#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.event import Event


class AlarmclockAlarmTriggeredEvent(Event):
    """
    Alarmclock.alarm.triggered event
    """

    EVENT_NAME = "alarmclock.alarm.triggered"
    EVENT_PROPAGATE = True
    EVENT_PARAMS = ["hour", "minute", "duration"]

    def __init__(self, params):
        """
        Constructor

        Args:
            params (dict): event parameters
        """
        Event.__init__(self, params)
