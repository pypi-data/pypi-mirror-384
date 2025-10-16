"""DMMSelfCalLogic class for handling DMM hardware self-calibration logic."""

from datetime import datetime

import nidmm

from nibcq._self_cal_logic.base import SelfCalLogic


class DMMSelfCalLogic(SelfCalLogic):
    """Implementation of SelfCalLogic protocol for NI Digital Multimeter (DMM) devices.

    This class provides device-specific implementations for DMM self-calibration operations,
    including temperature monitoring, calibration status checking, and performing
    self-calibration routines. It serves as an adapter between the generic SelfCalLogic
    protocol interface and the nidmm device driver API.

    The DMM self-calibration logic handles the specific quirks and API differences of
    DMM devices compared to other device families like SMU, providing a unified
    interface for calibration operations across different hardware types.
    """

    def __init__(self, session: nidmm.Session) -> None:
        """Initialize the DMM self-calibration logic with a hardware session.

        Args:
            session: An nidmm.Session instance representing the DMM hardware
                    session for calibration operations to function properly.

        Example:
            >>> import nidmm
            >>> dmm_session = nidmm.Session("PXI1Slot2")
            >>> dmm_logic = DMMSelfCalLogic(dmm_session)
        """
        self.session = session

    def get_self_cal_supported(self) -> bool:
        """Check if self-calibration is supported by the DMM device.

        Queries the DMM hardware to determine if it supports internal self-calibration
        routines. This capability varies by DMM model and firmware version.

        Returns:
            bool: True if self-calibration is supported, False otherwise.

        Example:
            >>> dmm_logic = DMMSelfCalLogic(dmm_device)
            >>> if dmm_logic.get_self_cal_supported():
            ...     print("DMM supports self-calibration")
            ... else:
            ...     print("DMM does not support self-calibration")
        """
        return self.session.get_self_cal_supported()

    def get_current_temperature(self) -> float:
        """Get the current internal temperature of the DMM device.

        Reads the current temperature from the DMM's internal temperature sensor.
        This information is useful for monitoring thermal conditions and determining
        if self-calibration should be performed based on temperature drift.

        Returns:
            float: Current device temperature in degrees Celsius.

        Example:
            >>> dmm_logic = DMMSelfCalLogic(dmm_device)
            >>> current_temp = dmm_logic.get_current_temperature()
            >>> print(f"DMM temperature: {current_temp:.1f}°C")
        """
        return self.session.get_dev_temp()

    def get_last_cal_temperature(self) -> float:
        """Get the temperature at which the last self-calibration was performed.

        Retrieves the internal temperature of the DMM device when the most recent
        self-calibration was executed. This helps determine if significant temperature
        drift has occurred since the last calibration, indicating whether a new
        calibration cycle should be initiated.

        Returns:
            float: Temperature during last self-calibration in degrees Celsius.


        Example:
            >>> dmm_logic = DMMSelfCalLogic(dmm_device)
            >>> last_cal_temp = dmm_logic.get_last_cal_temperature()
            >>> current_temp = dmm_logic.get_current_temperature()
            >>> temp_drift = abs(current_temp - last_cal_temp)
            >>> if temp_drift > 5.0:
            ...     print(f"Temperature drift: {temp_drift:.1f}°C, recalibration recommended")
        """
        return self.session.get_last_cal_temp(cal_type=0)

    def get_last_cal_date_time(self) -> datetime:
        """Get the date and time when the last self-calibration was performed.

        Retrieves timestamp information for the most recent self-calibration cycle.
        This is essential for tracking calibration intervals and determining when
        the next calibration should be scheduled based on time-based criteria.

        Returns:
            datetime: Timestamp of the last self-calibration as a datetime object.

        Example:
            >>> from datetime import datetime, timedelta
            >>> dmm_logic = DMMSelfCalLogic(dmm_device)
            >>> last_cal_time = dmm_logic.get_last_cal_date_time()
            >>> time_since_cal = datetime.now() - last_cal_time
            >>> if time_since_cal > timedelta(days=30):
            ...     print(f"Last calibration was {time_since_cal.days} days ago")
        """
        return self.session.get_cal_date_and_time(cal_type=0)

    def self_cal(self) -> None:
        """Perform self-calibration on the DMM device.

        Initiates an internal self-calibration routine on the DMM hardware. This
        process typically takes several seconds to complete and adjusts internal
        reference values to maintain measurement accuracy. The device should not
        be disturbed during calibration.

        The calibration process updates internal calibration constants and records
        the calibration timestamp and temperature for future reference.

        Example:
            >>> dmm_logic = DMMSelfCalLogic(dmm_device)
            >>> if dmm_logic.get_self_cal_supported():
            ...     print("Starting DMM self-calibration...")
            ...     dmm_logic.self_cal()
            ...     print("Self-calibration completed successfully")
            ... else:
            ...     print("DMM does not support self-calibration")
        """
        self.session.self_cal()
