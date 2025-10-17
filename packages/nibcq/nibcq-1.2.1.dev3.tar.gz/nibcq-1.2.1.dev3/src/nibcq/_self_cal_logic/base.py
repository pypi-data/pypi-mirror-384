"""Base protocol definition for device self-calibration logic implementations.

This module defines the SelfCalLogic protocol that establishes a common interface
for self-calibration operations across different device families. The protocol
ensures that all device-specific implementations provide consistent methods for
temperature monitoring, calibration status checking, and performing calibration
routines, regardless of the underlying hardware driver differences.

The protocol-based approach allows for type-safe polymorphism while maintaining
flexibility for device-specific calibration procedures and requirements.
"""

from datetime import datetime
from typing import Protocol

import nidcpower
import nidmm


class SelfCalLogic(Protocol):
    """Protocol defining the interface for device self-calibration logic implementations.

    This protocol establishes a common contract that all device-specific self-calibration
    logic classes must implement. It provides a type-safe way to handle calibration
    operations across different device families (DMM, SMU, etc.) without requiring
    inheritance from a common base class.

    The protocol ensures that calibration logic implementations provide essential
    methods for:
    - Checking calibration support capabilities
    - Monitoring current and historical temperatures
    - Tracking calibration timestamps
    - Performing self-calibration routines

    This design allows the factory pattern and client code to work with any
    device family that implements this protocol, ensuring consistent behavior
    while accommodating device-specific implementation details.

    Example:
        >>> # Any class implementing this protocol can be used polymorphically
        >>> def perform_calibration_check(logic: SelfCalLogic) -> None:
        ...     if logic.get_self_cal_supported():
        ...         current_temp = logic.get_current_temperature()
        ...         last_temp = logic.get_last_cal_temperature()
        ...         if abs(current_temp - last_temp) > 5.0:
        ...             logic.self_cal()
        >>>
        >>> # Works with any device family
        >>> dmm_logic = DMMSelfCalLogic(dmm_session)
        >>> smu_logic = SMUSelfCalLogic(smu_session)
        >>> perform_calibration_check(dmm_logic)  # Type-safe
        >>> perform_calibration_check(smu_logic)  # Type-safe
    """

    session: nidmm.Session | nidcpower.Session

    def __init__(self, session: nidmm.Session | nidcpower.Session) -> None:
        """Initialize the self-calibration logic with a hardware session.

        Args:
            session (nidmm.Session | nidcpower.Session): A hardware session instance
                    (nidmm.Session for DMM devices, nidcpower.Session for SMU devices)
                    that this calibration logic will use to communicate with the hardware.
        """
        ...

    def get_self_cal_supported(self) -> bool:
        """Check if self-calibration is supported by the device.

        This method should query the device to determine if it supports
        internal self-calibration routines. Support may vary by device
        model, firmware version, or hardware configuration.

        Returns:
            bool: True if self-calibration is supported, False otherwise.
        """
        ...

    def get_current_temperature(self) -> float:
        """Get the current internal temperature of the device.

        This method should read the current temperature from the device's
        internal temperature sensor. The temperature information is crucial
        for determining when calibration should be performed based on
        thermal drift criteria.

        Returns:
            float: Current device temperature in the defined degrees unit.
        """
        ...

    def get_last_cal_temperature(self) -> float:
        """Get the temperature at which the last self-calibration was performed.

        This method should retrieve the internal temperature of the device
        when the most recent self-calibration was executed. This information
        is used to determine if significant temperature drift has occurred
        since the last calibration, indicating whether a new calibration
        cycle should be initiated.

        Returns:
            float: Temperature during last self-calibration in the defined degrees unit.
        """
        ...

    def get_last_cal_date_time(self) -> datetime:
        """Get the date and time when the last self-calibration was performed.

        This method should retrieve timestamp information for the most recent
        self-calibration cycle. This is essential for tracking calibration
        intervals and determining when the next calibration should be scheduled
        based on time-based criteria.

        Returns:
            datetime: Timestamp of the last self-calibration as a datetime object.
        """
        ...

    def self_cal(self) -> None:
        """Perform self-calibration on the device.

        This method should initiate an internal self-calibration routine on
        the hardware. The calibration process typically takes several seconds
        to complete and adjusts internal reference values to maintain measurement
        accuracy. The device should not be disturbed during calibration.

        The calibration process should update internal calibration constants
        and record the calibration timestamp and temperature for future reference.
        """
        ...
