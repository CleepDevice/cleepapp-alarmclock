#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.event import Event


class AlarmclockAlarmStoppedEvent(Event):
    """
    Alarmclock.alarm.triggered event
    """

    EVENT_NAME = "alarmclock.alarm.stopped"
    EVENT_PROPAGATE = True
    EVENT_PARAMS = ["hour", "minute", "timeout", "snoozed", "volume"]

    def __init__(self, params):
        """
        Constructor

        Args:
            params (dict): event parameters
        """
        Event.__init__(self, params)
