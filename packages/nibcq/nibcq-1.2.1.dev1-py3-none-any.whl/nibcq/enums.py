"""Centralized enums for nibcq package."""

from enum import Enum

import nidcpower
import nidmm

### ------ ###
#   Device   #
### ------ ###


class _EloadDriver:
    """Wrapper to distinguish ELOAD from SMU while using the same nidcpower driver.

    This prevents enum aliasing where ELOAD would become an alias of SMU.
    """

    Session = nidcpower.Session


class DeviceFamily(Enum):
    """Enumeration for device families supported by the nibcq package.

    Defines the major categories of measurement devices that can be used
    with the Battery Cell Quality Toolkit. Each family corresponds to
    different measurement capabilities and driver modules.

    Values:
        DMM: Digital Multimeter devices (nidmm module)
            - Used for voltage measurements (OCV)
            - Examples: PXI-4071, PXIe-4081
        SMU: Source Measure Unit devices (nidcpower module)
            - Used for impedance measurements (EIS, ACIR)
            - Examples: PXIe-4139
        ELOAD: Electronic Load devices (nidcpower module)
            - Used for DC resistance testing (DCIR)
            - Examples: PXIe-4051

    Examples:
        >>> device = Device.create(DeviceFamily.DMM, "PXI1Slot2")
        >>> if device.device_family == DeviceFamily.SMU:
        ...     print("This is a Source Measure Unit")
        >>> device_eload = Device.create(DeviceFamily.ELOAD, "PXI1Slot3")
        >>> if device_eload.device_family == DeviceFamily.ELOAD:
        ...     print("This is an Electronic Load (for DCIR)")
    """

    DMM = nidmm
    SMU = nidcpower
    # Electronic load uses a wrapper to prevent enum aliasing with SMU
    # Both use nidcpower but serve different purposes:
    # - SMU (4139): for EIS/ACIR impedance measurements
    # - ELOAD (4051): for DCIR resistance measurements
    ELOAD = _EloadDriver


### ------------ ###
#   Measurements   #
### ------------ ###


class PowerlineFrequency(Enum):
    """Enumeration of powerline frequencies for measurement synchronization.

    Defines the standard AC power grid frequencies used worldwide. These values
    are used to configure measurement instruments for proper powerline noise
    rejection and timing synchronization.

    Values:
        FREQ_50_HZ (50): 50 Hz powerline frequency
            - Used in Europe, Asia, Africa, and most other regions
        FREQ_60_HZ (60): 60 Hz powerline frequency
            - Used in North America, parts of South America, and some other regions

    Examples:
        >>> params = OCVTestParameters()
        >>> params.powerline_frequency = PowerlineFrequency.FREQ_50_HZ
        >>> print(params.powerline_frequency.value)  # 50
    """

    FREQ_50_HZ = 50
    FREQ_60_HZ = 60


class DMMRange(Enum):
    """Enumeration for DMM voltage measurement range options.

    Defines the voltage measurement ranges available for Digital Multimeter
    operations. The range selection affects measurement resolution and accuracy,
    with smaller ranges providing better resolution for signals within that range.

    Values:
        DC_10V (10): ±10 Volt measurement range
            - High resolution for low voltage measurements
            - Suitable for most battery cell voltage measurements (0-5V)
        DC_1000V (1000): ±1000 Volt measurement range
            - Extended range for high voltage applications
            - Lower resolution but handles higher voltage signals

    Examples:
        >>> params = OCVTestParameters()
        >>> params.range = DMMRange.DC_10V  # For typical battery measurements
        >>> params.range = DMMRange.DC_1000V  # For high voltage applications
        >>> print(params.range.value)  # 10 or 1000
    """

    DC_10V = 10
    DC_1000V = 1000


class SMUOutputFunction(Enum):
    """Enumeration for SMU output function types.

    Defines the output modes available for Source Measure Unit (SMU) devices
    during impedance measurements. Each mode configures the SMU to operate
    as either a voltage source or current source, with continuous or pulsed
    output capabilities.

    Values:
        DC_VOLTAGE: Continuous DC voltage sourcing mode
            - SMU acts as a voltage source with current measurement
            - Used for voltage-controlled impedance measurements
        DC_CURRENT: Continuous DC current sourcing mode
            - SMU acts as a current source with voltage measurement
            - Used for current-controlled impedance measurements (ACIR/EIS)
        PULSE_VOLTAGE: Pulsed voltage sourcing mode
            - Voltage output with defined pulse timing
            - Reduces heating effects during measurements
        PULSE_CURRENT: Pulsed current sourcing mode
            - Current output with defined pulse timing
            - Preferred for battery testing to minimize thermal effects

    Examples:
        >>> params = ACIRTestParameters()
        >>> params.output_function = OutputFunction.DC_CURRENT
        >>> # Configure SMU for current-controlled ACIR measurement
        >>> params.output_function = OutputFunction.PULSE_CURRENT
        >>> # Use pulsed mode to reduce heating
    """

    DC_VOLTAGE = nidcpower.OutputFunction.DC_VOLTAGE
    DC_CURRENT = nidcpower.OutputFunction.DC_CURRENT
    PULSE_VOLTAGE = nidcpower.OutputFunction.PULSE_VOLTAGE
    PULSE_CURRENT = nidcpower.OutputFunction.PULSE_CURRENT


### ------------ ###
#   Compensation   #
### ------------ ###


class CompensationMethod(str, Enum):
    """Enumeration of available compensation methods for ACIR/EIS measurements.

    Defines the mathematical compensation techniques used to remove systematic
    errors from impedance measurements. Each method corrects for different
    types of measurement artifacts including cable impedance, contact resistance,
    and instrument characteristics.

    Values:
        NO_COMPENSATION ("No Compensation"): No correction applied
            - Raw measurement values are used without any compensation
            - Fastest measurement but includes all systematic errors
        SHORT ("Short"): Short-circuit compensation
            - Corrects for parasitic impedances using short-circuit reference
            - Removes cable and contact resistance effects
        GOLDEN_DUT ("Golden DUT"): Reference device compensation
            - Uses known reference device to calibrate measurements
            - Corrects for instrument and setup characteristics

    Examples:
        >>> params = ACIRTestParameters()
        >>> params.compensation_method = CompensationMethod.SHORT
        >>> # Load short compensation file and apply corrections
        >>> params.compensation_method = CompensationMethod.NO_COMPENSATION
        >>> # Fastest measurement, no correction applied
    """

    NO_COMPENSATION = "No Compensation"
    SHORT = "Short"
    GOLDEN_DUT = "Golden DUT"
    SHORT_GOLDEN_DUT = "Short-Golden DUT"


class InterpolationMode(str, Enum):
    """Interpolation modes for compensation value lookups in frequency domain.

    Defines how compensation values are calculated when the measurement frequency
    doesn't exactly match a frequency in the compensation table. Different modes
    provide different trade-offs between accuracy and computational simplicity.

    Values:
        NEAREST ("nearest"): Nearest neighbor interpolation
            - Uses the compensation value from the closest frequency point
            - Fast and simple, but may introduce step discontinuities
        LOWER ("lower"): Lower bound interpolation
            - Always uses compensation value from the next lower frequency
            - Conservative approach, ensures no extrapolation above known points
        UPPER ("upper"): Upper bound interpolation
            - Always uses compensation value from the next higher frequency
            - Conservative approach, ensures no extrapolation below known points
        LINEAR ("linear"): Linear interpolation
            - Calculates compensation value using linear interpolation between
              neighboring frequency points
            - Most accurate for smooth frequency responses

    Examples:
        >>> compensation = Compensation.from_file(CompensationMethod.SHORT, "short.json")
        >>> impedance = compensation.get_compensated_impedance(
        ...     frequency=1500.0,
        ...     measured_impedance=complex(0.1, 0.05),
        ...     interpolation_mode=InterpolationMode.LINEAR
        ... )
    """

    NEAREST = "nearest"
    LOWER = "lower"
    UPPER = "upper"
    LINEAR = "linear"


### --------- ###
#   Switching   #
### --------- ###


class SwitchDeviceType(Enum):
    """Enumeration of supported NI switch device types for multiplexer control.

    Defines the National Instruments switch modules that are supported by the
    Battery Cell Quality Toolkit for sequential DUT testing. Each device type
    has specific topology capabilities and connection options.

    Values:
        PXI_2525 ("2525"): PXI-2525 switch module
            - Typically used for source switching in SMU applications
            - Supports various relay configurations
        PXIe_2530B ("2530"): PXIe-2530B switch module
            - Typically used for sense switching and DMM applications.
            - High-density relay configurations.

    Examples:
        >>> device_type = SwitchDeviceType.PXIe_2530B
        >>> topology = f"{device_type.value}/2-Wire Quad 16x1 Mux"
        >>> print(topology)  # "2530/2-Wire Quad 16x1 Mux"
    """

    PXI_2525 = "2525"
    PXIe_2530B = "2530"


class SwitchTopology(Enum):
    """Enumeration of available switch topologies for multiplexer configurations.

    Defines the standard relay topologies supported by NI switch modules for
    Battery Cell Quality testing applications. Each topology provides different
    channel counts and connection capabilities for DUT switching.

    Values:
        SWITCH_2_WIRE_64X1_MUX ("2-Wire 64x1 Mux"):
            - Single 64-channel multiplexer
            - Maximum DUT capacity with 2-wire connections
        SWITCH_2_WIRE_DUAL_32X1_MUX ("2-Wire Dual 32x1 Mux"):
            - Two independent 32-channel multiplexers
            - Good for applications requiring channel isolation
        SWITCH_2_WIRE_QUAD_16X1_MUX ("2-Wire Quad 16x1 Mux"):
            - Four independent 16-channel multiplexers
            - Recommended topology for most applications
            - Good balance of channel count and flexibility

    Examples:
        >>> topology = SwitchTopology.SWITCH_2_WIRE_QUAD_16X1_MUX
        >>> config = SwitchConfiguration(topology, ["ch0", "ch1"])
        >>> print(config.get_topology_string())  # "2-Wire Quad 16x1 Mux"
    """

    SWITCH_2_WIRE_64X1_MUX = "2-Wire 64x1 Mux"
    SWITCH_2_WIRE_DUAL_32X1_MUX = "2-Wire Dual 32x1 Mux"
    SWITCH_2_WIRE_QUAD_16X1_MUX = "2-Wire Quad 16x1 Mux"
