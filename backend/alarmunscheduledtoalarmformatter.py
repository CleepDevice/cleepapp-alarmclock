#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.profileformatter import ProfileFormatter
from cleep.profiles.alarmprofile import AlarmProfile

class AlarmUnscheduledToAlarmFormatter(ProfileFormatter):
    """
    AlarmUnscheduledEvent event to AlarmProfile
    """
    def __init__(self, params):
        """
        Constuctor

        Args:
            params (dict): formatter parameters
        """
        ProfileFormatter.__init__(self, params, 'alarmclock.alarm.unscheduled', AlarmProfile())

    def _fill_profile(self, event_params, profile):
        """
        Fill profile with event data

        Args:
            event_params (dict): event parameters
            profile (Profile): profile instance
        """
        profile.hour = event_params["hour"]
        profile.minute = event_params["minute"]
        profile.timeout = event_params["timeout"]
        profile.volume = event_params["volume"]
        profile.count = event_params["count"]
        profile.status = profile.STATUS_UNSCHEDULED

        return profile