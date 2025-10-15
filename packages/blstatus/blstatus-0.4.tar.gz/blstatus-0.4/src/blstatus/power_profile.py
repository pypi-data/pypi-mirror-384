from typing import Callable
import subprocess
from pydbus.bus import Bus

from . import config


def get_profile_abbreviation(profile):
    """Return a single character abbreviation for the battery state"""
    if profile == "performance":
        return 'Perf'
    elif profile == "balanced":
        return 'Bal'
    elif profile == "power-saver":
        return 'PS'
    else:
        return '?'


class PowerProfile:
    _publish_status = None
    _signal_text = ''
    _spacer = ''
    _system_bus = None
    _device_proxy = None
    text = ''

    def __init__(self, system_bus: Bus, publish_status: Callable[[], None], spacer=''):

        self._publish_status = publish_status  # Function to update the full status text
        self._signal_text = config.power_profile_signal_text if config.enable_signal_text else ''  # statuscmd signal text
        self._spacer = spacer  # Spacer text added after status
        self._system_bus = system_bus

        self._power_profiles_proxy = self._system_bus.get('org.freedesktop.UPower.PowerProfiles')

        if self._power_profiles_proxy is not None:
            self._power_profiles_proxy.PropertiesChanged.connect(self._update_and_publish)
            self.update_text()  # Initial update


    def update_text(self):
        active_profile = self._power_profiles_proxy.ActiveProfile

        # Format status text
        self.text = f'{self._signal_text}{get_profile_abbreviation(active_profile)}{self._spacer}'

    def _update_and_publish(self, *params):
        """Callback for the PropertiesChanged signal"""
        self.update_text()
        self._publish_status()
