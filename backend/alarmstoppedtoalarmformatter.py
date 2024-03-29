#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.profileformatter import ProfileFormatter
from cleep.profiles.alarmprofile import AlarmProfile


class AlarmStoppedToAlarmFormatter(ProfileFormatter):
    """
    AlarmStoppedEvent event to AlarmProfile
    """

    def __init__(self, params):
        """
        Constuctor
        Args:
            params (dict): formatter parameters
        """
        ProfileFormatter.__init__(
            self, params, "alarmclock.alarm.stopped", AlarmProfile()
        )

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
        profile.status = (
            profile.STATUS_SNOOZED
            if event_params["snoozed"]
            else profile.STATUS_STOPPED
        )

        return profile
