"""SMUSelfCalLogic class for handling SMU hardware self-calibration logic."""

from datetime import datetime

import nidcpower

from nibcq._self_cal_logic.base import SelfCalLogic


class SMUSelfCalLogic(SelfCalLogic):
    """Implementation of SelfCalLogic protocol for NI Source Measure Unit (SMU) devices.

    This class provides device-specific implementations for SMU self-calibration operations,
    including temperature monitoring, calibration status checking, and performing
    self-calibration routines. It serves as an adapter between the generic SelfCalLogic
    protocol interface and the nidcpower device driver API.

    SMU devices have different calibration characteristics compared to DMM devices,
    particularly in how they handle temperature sensing and calibration procedures.
    This implementation abstracts those differences while providing a consistent
    interface for calibration operations.
    """

    def __init__(self, session: nidcpower.Session) -> None:
        """Initialize the SMU self-calibration logic with a hardware session.

        Args:
            session: An nidcpower.Session instance representing the SMU hardware
                    session for calibration operations to function properly.

        Example:
            >>> import nidcpower
            >>> smu_session = nidcpower.Session("PXI1Slot3")
            >>> smu_logic = SMUSelfCalLogic(smu_session)
        """
        self.session = session

    def get_self_cal_supported(self) -> bool:
        """Check if self-calibration is supported by the SMU device.

        For SMU devices using nidcpower, self-calibration is generally supported
        across all modern SMU models. This method currently returns True as a
        default, but could be extended in the future to query specific device
        capabilities if needed.

        Returns:
            bool: True indicating that SMU devices support self-calibration.

        Example:
            >>> smu_logic = SMUSelfCalLogic(smu_device)
            >>> if smu_logic.get_self_cal_supported():
            ...     print("SMU supports self-calibration")
        """
        return True

    def get_current_temperature(self) -> float:
        """Get the current internal temperature of the SMU device.

        Reads the current temperature from the SMU's internal temperature sensor.
        SMU devices typically have more sophisticated thermal monitoring compared
        to DMM devices due to their higher power dissipation capabilities.

        Returns:
            float: Current device temperature in degrees Celsius.

        Example:
            >>> smu_logic = SMUSelfCalLogic(smu_device)
            >>> current_temp = smu_logic.get_current_temperature()
            >>> print(f"SMU temperature: {current_temp:.1f}°C")
            >>> if current_temp > 70.0:
            ...     print("Warning: SMU running hot, consider cooling")
        """
        return self.session.read_current_temperature()

    def get_last_cal_temperature(self) -> float:
        """Get the temperature at which the last self-calibration was performed.

        Retrieves the internal temperature of the SMU device when the most recent
        self-calibration was executed. SMU devices are particularly sensitive to
        temperature variations due to their precision analog circuitry, making
        temperature-based calibration decisions critical for measurement accuracy.

        Returns:
            float: Temperature during last self-calibration in degrees Celsius.

        Example:
            >>> smu_logic = SMUSelfCalLogic(smu_device)
            >>> last_cal_temp = smu_logic.get_last_cal_temperature()
            >>> current_temp = smu_logic.get_current_temperature()
            >>> temp_drift = abs(current_temp - last_cal_temp)
            >>> if temp_drift > 3.0:  # SMUs typically need tighter temperature control
            ...     print(f"Temperature drift: {temp_drift:.1f}°C, recalibration needed")
        """
        return self.session.get_self_cal_last_temp()

    def get_last_cal_date_time(self) -> datetime:
        """Get the date and time when the last self-calibration was performed.

        Retrieves timestamp information for the most recent self-calibration cycle.
        SMU devices often require more frequent calibration than DMM devices due to
        their dual-mode operation (source and measure) and higher precision requirements,
        making accurate timestamp tracking essential for maintenance schedules.

        Returns:
            datetime: Timestamp of the last self-calibration as a datetime object.

        Example:
            >>> from datetime import datetime, timedelta
            >>> smu_logic = SMUSelfCalLogic(smu_device)
            >>> last_cal_time = smu_logic.get_last_cal_date_time()
            >>> time_since_cal = datetime.now() - last_cal_time
            >>> if time_since_cal > timedelta(days=14):  # More frequent than DMM
            ...     print(f"SMU calibration overdue by {time_since_cal.days - 14} days")
        """
        return self.session.get_self_cal_last_date_and_time()

    def self_cal(self) -> None:
        """Perform self-calibration on the SMU device.

        Initiates an internal self-calibration routine on the SMU hardware. SMU
        self-calibration is typically more comprehensive than DMM calibration as
        it must calibrate both source and measure functionality across multiple
        ranges and polarities. The process may take longer than DMM calibration.

        During calibration, the SMU adjusts internal DAC and ADC references,
        offset corrections, and gain adjustments to maintain specified accuracy
        across all measurement and sourcing ranges.

        Example:
            >>> smu_logic = SMUSelfCalLogic(smu_device)
            >>> print("Starting SMU self-calibration (this may take longer)...")
            >>> smu_logic.self_cal()
            >>> print("SMU self-calibration completed successfully")
            >>>
            >>> # Verify calibration success
            >>> cal_time = smu_logic.get_last_cal_date_time()
            >>> print(f"Calibration completed at: {cal_time}")
        """
        self.session.self_cal()
