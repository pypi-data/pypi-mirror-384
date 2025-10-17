"""Factory class for creating device-specific self-calibration logic instances.

This module implements the Factory design pattern to create appropriate self-calibration
logic instances based on device family types. It provides a clean abstraction layer
that eliminates the need for client code to know about specific implementation classes
while ensuring type safety and extensibility for future device families.
"""

import nidcpower
import nidmm

from nibcq._self_cal_logic._dmm_logic import DMMSelfCalLogic
from nibcq._self_cal_logic._smu_logic import SMUSelfCalLogic
from nibcq._self_cal_logic.base import SelfCalLogic
from nibcq.enums import DeviceFamily


class SelfCalFactory:
    """Factory class for creating device-specific self-calibration logic instances.

    This factory implements the Factory design pattern to create appropriate
    SelfCalLogic implementations based on the device family type. It provides
    a centralized way to instantiate calibration logic while hiding the specific
    implementation details from client code.

    The factory uses a registry pattern with a class-level dictionary mapping
    device families to their corresponding logic implementation classes. This
    design makes it easy to add support for new device families without
    modifying existing client code.

    Attributes:
        session (nidmm.Session|nidcpower.Session):
                The hardware session that this logic implementation operates on.
                Must be set during initialization and should remain immutable.

    """

    FACTORY_LOGICS = {
        DeviceFamily.DMM: DMMSelfCalLogic,
        DeviceFamily.SMU: SMUSelfCalLogic,
    }

    @staticmethod
    def get_logic(
        session: nidmm.Session | nidcpower.Session, device_family: DeviceFamily
    ) -> SelfCalLogic:
        """Create a self-calibration logic instance based on the session type and device family.

        This method serves as the main entry point for creating device-specific
        self-calibration logic instances. It examines the device family type
        and returns an appropriate SelfCalLogic implementation initialized with
        the provided session.

        Args:
            session: A hardware session instance (nidmm.Session for DMM devices,
                    nidcpower.Session for SMU devices) that will be used by the
                    self-calibration logic to communicate with the hardware.
            device_family: A DeviceFamily enum value indicating the type of device
                          (DeviceFamily.DMM, DeviceFamily.SMU, etc.).

        Returns:
            SelfCalLogic: An instance of the appropriate SelfCalLogic implementation
                         for the device family (DMMSelfCalLogic for DMM devices,
                         SMUSelfCalLogic for SMU devices, etc.) initialized with
                         the provided session.

        Raises:
            ValueError: If the device family is not supported by the factory.
                       This typically indicates either an unsupported device
                       type or a missing implementation in the FACTORY_LOGICS registry.

        Example:
            >>> import nidcpower
            >>> from nibcq.enums import DeviceFamily
            >>>
            >>> # Create logic for an SMU device
            >>> smu_session = nidcpower.Session("PXI1Slot3")
            >>> smu_logic = SelfCalFactory.get_logic(smu_session, DeviceFamily.SMU)
            >>> isinstance(smu_logic, SMUSelfCalLogic)
            True
            >>>
            >>> # Create logic for a DMM device
            >>> import nidmm
            >>> dmm_session = nidmm.Session("PXI1Slot2")
            >>> dmm_logic = SelfCalFactory.get_logic(dmm_session, DeviceFamily.DMM)
            >>> isinstance(dmm_logic, DMMSelfCalLogic)
            True
            >>>
            >>> # Handle unsupported device families
            >>> try:
            ...     logic = SelfCalFactory.get_logic(smu_session, "UNSUPPORTED")
            ... except ValueError as e:
            ...     print(f"Error: {e}")
            Error: Unsupported device family: UNSUPPORTED
        """
        creator = SelfCalFactory.FACTORY_LOGICS.get(device_family)
        if creator:
            return creator(session)
        else:
            raise ValueError(f"Unsupported device family: {device_family}")
