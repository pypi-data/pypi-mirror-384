# noinspection PyUnresolvedReferences
"""This is a space to test peripherals and get index numbers for each peripheral.

>>> Exceptions

"""

import platform
import sys
from collections.abc import Generator
from typing import Mapping

import pyaudio

from jarvis.modules.exceptions import no_alsa_err

if sys.version_info.minor > 10:
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        """Override for python 3.10 due to lack of StrEnum."""


if platform.system() == "Linux":
    with no_alsa_err():
        audio_engine = pyaudio.PyAudio()
else:
    audio_engine = pyaudio.PyAudio()
# audio_engine.open(output_device_index=6, output=True, channels=1, format=pyaudio.paInt16, rate=16000)
_device_range = audio_engine.get_device_count()


class ChannelType(StrEnum):
    """Allowed values for channel types.

    >>> ChannelType

    """

    input_channels = "maxInputChannels"
    output_channels = "maxOutputChannels"


channel_type = ChannelType


def get_audio_devices(channels: str) -> Generator[Mapping[str, str | int | float]]:
    """Iterates over all devices and yields the device that has input channels.

    Args:
        channels: Takes an argument to determine whether to yield input or output channels.

    Yields:
        dict:
        Yields a dictionary with all the input devices available.
    """
    for index in range(_device_range):
        device_info = audio_engine.get_device_info_by_index(device_index=index)
        if device_info.get(channels, 0) > 0:
            yield device_info
