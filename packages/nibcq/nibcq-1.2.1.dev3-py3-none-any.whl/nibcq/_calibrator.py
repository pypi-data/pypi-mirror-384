""" ""This module defines the Calibrator class for handling hardware self-calibration."""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional

from ._self_cal_logic import SelfCalFactory, SelfCalLogic
from .calibration import Diary, Entry, Settings

if TYPE_CHECKING:
    from ._device import Device


class Calibrator:
    """A calibration manager for hardware devices that handles self-calibration operations.

    The Calibrator class manages device self-calibration by tracking calibration history,
    validating calibration status based on time and temperature constraints, and performing
    new calibrations when needed. It uses a diary system to persist calibration records
    and works with hardware adapters to interface with actual devices.

    Attributes:
        calibration_settings (Settings): Configuration settings for calibration validation,
            including temperature delta and time interval thresholds.

    Raises:
        ValueError: When calibration file path is empty or invalid.
        TypeError: When self-calibration is not supported by the device.
        RuntimeError: When attempting calibration on unsupported hardware.

    Example:
        >>> device = Device(session, device_family)
        >>> settings = Settings(temperature_delta=2.0, days_to_calibration=30)
        >>> calibrator = Calibrator(device, settings, "/path/to/cal.json")
        >>> if not calibrator.last_calibration_is_valid:
        ...     calibrator.self_calibrate()
    """

    calibration_settings: Settings

    def __init__(
        self,
        device: "Device",
        calibration_settings: Settings,
        calibration_file_path: Optional[str] = None,
    ):
        """Initialize the Calibrator with a hardware session."""
        self._hw_adapter: SelfCalLogic = SelfCalFactory.get_logic(
            device.session, device.device_family
        )
        self.calibration_settings = calibration_settings
        if not calibration_file_path:
            calibration_file_path = device.default_calibration_path
        self._calibration_diary: Diary = Diary(calibration_file_path)

    @property
    def calibration_file_path(self):
        """Return the calibration file path."""
        return self._calibration_diary.file_path

    @calibration_file_path.setter
    def calibration_file_path(self, path: str):
        """Set the calibration file path."""
        if not path:
            raise ValueError("Calibration file path cannot be empty.")
        self._calibration_diary = Diary(file_path=path)

    @property
    def last_calibration_is_valid(self):
        """Return if the latest self-calibration is valid for the instrument."""
        last = self._calibration_diary.last_entry
        adapter = self._hw_adapter
        settings = self.calibration_settings
        if last is None:
            return False

        # Only check if self calibration is supported:
        if adapter.get_self_cal_supported():
            # Try to decide validty. If any error is triggered, then consider it invalid.
            try:
                # Check last calibration time and temperature from the calibration diary.
                entry_temp = (
                    abs(last.temperature - adapter.get_current_temperature())
                    < settings.temperature_delta
                )
                entry_time = (datetime.now() - last.timestamp) < timedelta(
                    days=settings.days_to_calibration
                )
                is_last_entry_valid = entry_temp and entry_time
                # Check last calibration temperature from the device's last self calibration.
                is_last_stored_temp_valid = (
                    abs(adapter.get_last_cal_temperature() - adapter.get_current_temperature())
                    < settings.temperature_delta
                )
                return is_last_entry_valid and is_last_stored_temp_valid
            # If some value error happens, then the last calibration is invalid.
            except ValueError:
                return False
        else:
            raise TypeError("Self Calibration is not Supported.")

    # Alternatively, we can warn the user here and require an acknowledgment.
    def self_calibrate(self, force: bool = False) -> bool:
        """Perform self-calibration on the session.

        Args:
            force (bool): If True, skips the user prompt for acknowledgment.
        """
        if not force:
            input(
                "[nibcq] WARNING: Please ensure the Device Under Test (DUT)"
                " is removed from the test before self-calibration.\n"
                "A DUT cell that is present during self-calibration may be damaged.\n"
                "Press Enter to continue..."
            )

        adapter = self._hw_adapter
        # Check if device support Self Calibraion.
        if adapter.get_self_cal_supported():
            # Decide if the device is already calibrated.
            if not self.last_calibration_is_valid:
                # If it is required, run self-calibration.
                adapter.self_cal()
                self._calibration_diary.add_new_entry(
                    Entry(
                        timestamp=adapter.get_last_cal_date_time(),
                        temperature=adapter.get_last_cal_temperature(),
                    )
                )
                return True
        else:
            raise RuntimeError(
                f"Self calibration is not supported on {adapter.session.instrument_model}!"
            )
        return False
