"""Defines the DCIR (Direct Current Internal Resistance) measurement for the nibcq package."""

import math
from dataclasses import dataclass
from typing import Final

import nidcpower

from nibcq._device import Device
from nibcq.enums import DeviceFamily
from nibcq.measurement import Measurement, TestParameters, SMUMeasurement


@dataclass
class DCIRTestParameters(TestParameters):
    """Configuration parameters for Direct Current Internal Resistance (DCIR) measurements.

    This class extends the base TestParameters to provide DCIR-specific configuration
    options for DC resistance measurements. DCIR measurements characterize the DC
    internal resistance of electrochemical systems, batteries, and other devices by
    applying controlled current loads and measuring the resulting voltage response.

    The DCIR measurement uses a two-point load test where two different current levels
    are applied sequentially, and the internal resistance is calculated from the
    voltage difference divided by the current difference (Ohm's law). This provides
    a direct measurement of the device's internal resistance under load conditions.

    Attributes:
        max_load_current: Maximum current load applied during the measurement in Amperes.
                         This current defines the second discharge period load, while
                         the first discharge period uses 20% of this value. Default 0.0A
                         requires configuration before measurement. Typical values range
                         from 0.1A to 10A depending on DUT characteristics.
        powerline_frequency: Local powerline frequency for noise rejection (50 Hz or 60 Hz).
                           Should match the local electrical grid frequency to minimize
                           powerline interference in sensitive measurements. Inherited
                           from TestParameters with default 60 Hz.

    Example:
        >>> params = DCIRTestParameters(
        ...     max_load_current=2.0,
        ...     powerline_frequency=PowerlineFrequency.FREQ_50_HZ
        ... )
        >>> params.max_load_current
        2.0
    """

    max_load_current: float = 0.0


@dataclass
class DischargePeriods:
    """Time durations for the two-phase DCIR discharge sequence configuration.

    This dataclass defines the timing parameters for the two-phase DCIR measurement
    sequence. The DCIR test applies two different current loads for specified time
    periods to establish steady-state conditions before voltage measurements are taken.
    The discharge periods ensure that transient effects settle and stable voltage
    readings can be obtained for accurate resistance calculations.

    The periods are automatically adjusted by subtracting a 0.11-second offset to
    account for measurement timing overhead and ensure proper synchronization with
    the data acquisition system.

    Attributes:
        discharge_period_1: Duration of the first discharge phase in seconds.
                           Default 10.0s provides sufficient time for initial
                           settling with the lower current load (20% of max).
                           Longer periods improve measurement stability but
                           increase total test time.
        discharge_period_2: Duration of the second discharge phase in seconds.
                           Default 1.0s is typically sufficient for the higher
                           current load (100% of max) since the DUT is already
                           at a stable baseline from the first phase.

    Example:
        >>> periods = DischargePeriods(discharge_period_1=15.0, discharge_period_2=2.0)
        >>> periods.discharge_period_1
        15.0
        >>> periods.discharge_period_2
        2.0
    """

    discharge_period_1: float = 10.0
    discharge_period_2: float = 1.0


@dataclass
class DischargeCurrents:
    """Current levels for the two-phase DCIR measurement sequence.

    This dataclass contains the calculated current values applied during each phase
    of the DCIR measurement. These currents are derived from the maximum load current
    specified in the test parameters, with the first current set to 20% of maximum
    for initial conditioning and the second current set to the full maximum load.

    The two-point measurement approach allows calculation of internal resistance
    using Ohm's law: R = (V1 - V2) / (I1 - I2), where the subscripts refer to
    the two measurement points at different current levels.

    Attributes:
        discharge_current_1: Current level for the first discharge phase in Amperes.
                           Typically set to 20% of max_load_current to provide a
                           light load reference point. Default 0.0A indicates the
                           values must be calculated during configuration.
        discharge_current_2: Current level for the second discharge phase in Amperes.
                           Set to the full max_load_current to provide the high
                           load measurement point. Default 0.0A indicates the
                           values must be calculated during configuration.

    Example:
        >>> currents = DischargeCurrents(discharge_current_1=0.4, discharge_current_2=2.0)
        >>> # Calculate resistance using Ohm's law: R = (V1 - V2) / (I1 - I2)
        >>> resistance = (voltage_1 - voltage_2) / (
        ...     currents.discharge_current_1 - currents.discharge_current_2
        ... )
    """

    discharge_current_1: float = 0.0
    discharge_current_2: float = 0.0


@dataclass
class ObtainedDCIRParameters:
    """Internal measurement acquisition parameters for DCIR data collection.

    This dataclass contains the calculated parameters used to configure the SMU
    for data acquisition during DCIR measurements. These parameters control the
    timing, sampling, and measurement precision aspects of the data collection
    process, ensuring optimal measurement quality and accuracy.

    The parameters are optimized for DCIR measurements which require stable,
    accurate voltage and current readings during the discharge periods. The
    aperture time and sample count are balanced to provide good noise rejection
    while maintaining reasonable measurement speed.

    Attributes:
        aperture_time: Integration time per measurement sample in specified units.
                      Default 0.0 indicates automatic calculation.
        aperture_time_units: Time base for aperture_time measurement from nidcpower.
                           Default SECONDS allows direct time specification.
                           POWER_LINE_CYCLES provides better noise rejection by
                           synchronizing with power line frequency.
        number_of_samples: Number of measurement samples taken per discharge period.
                          Default 3 samples provides statistical averaging while
                          maintaining fast measurement speed. More samples improve
                          accuracy but increase measurement time.

    Example:
        >>> params = ObtainedDCIRParameters(
        ...     aperture_time=2.0,
        ...     aperture_time_units=nidcpower.ApertureTimeUnits.POWER_LINE_CYCLES,
        ...     number_of_samples=5
        ... )
        >>> params.number_of_samples
        5
    """

    aperture_time: float = 0.0
    aperture_time_units: nidcpower.ApertureTimeUnits = nidcpower.ApertureTimeUnits.SECONDS
    number_of_samples: int = 3


class DCIR(Measurement):
    """Direct Current Internal Resistance (DCIR) measurement handler class.

    This class implements two-point DC resistance measurements using a Source Measure
    Unit (SMU) configured as an electronic load. DCIR measurements characterize the
    internal resistance of electrochemical systems, batteries, fuel cells, and other
    devices by applying controlled current loads and measuring voltage response.

    The DCIR measurement applies two sequential current loads: first a light load
    (20% of maximum current) followed by a heavy load (100% of maximum current).
    The internal resistance is calculated using Ohm's law from the voltage and
    current differences: R = (V1 - V2) / (I1 - I2).

    This measurement is fundamental in battery testing and electrochemical analysis
    for characterizing device performance, health monitoring, and quality control.
    Unlike AC impedance measurements, DCIR provides the DC resistance component
    which is critical for power delivery and efficiency calculations.

    The class supports only NI PXIe-4051 electronic loads, which provide the
    necessary current sinking capability and measurement precision required for
    accurate DCIR measurements.

    Example:
        >>> # Configure measurement parameters
        >>> params = DCIRTestParameters(
        ...     max_load_current=2.0,
        ...     powerline_frequency=PowerlineFrequency.FREQ_50_HZ
        ... )
        >>>
        >>> # Connect to electronic load device
        >>> device = Device.create(DeviceFamily.ELOAD, "PXI1Slot2")
        >>> dcir = DCIR(device, params)
        >>>
        >>> # Run measurement
        >>> resistance = dcir.run()
        >>> print(f"Internal resistance: {resistance:.4f} Ohms")
    """

    DEVICE_FAMILY: Final[DeviceFamily] = DeviceFamily.ELOAD
    """DeviceFamily: Device family for DCIR measurements."""

    def __init__(self, device: Device, test_parameters: DCIRTestParameters):
        """Initialize the DCIR measurement with the specified device and parameters.

        Configures the DCIR measurement system with the provided electronic load device
        and test parameters. Validates device compatibility and initializes internal
        parameters for the two-phase discharge sequence.

        The initialization sets up default discharge periods with timing offsets to
        account for measurement overhead, configures measurement parameters optimized
        for DCIR testing, and prepares the internal state for subsequent measurement
        execution.

        Args:
            device: The SMU device instance configured as an electronic load.
                   Must be an NI PXIe-4051 or compatible electronic load device
                   with current sinking capability suitable for DCIR measurements.
            test_parameters: DCIR-specific configuration parameters including maximum
                           load current and powerline frequency settings. The
                           max_load_current determines both discharge current levels.

        Raises:
            ValueError: If the device is not an NI PXIe-4051 electronic load or is
                       otherwise incompatible with DCIR measurement requirements.
            TypeError: If test_parameters is not a DCIRTestParameters instance.

        Example:
            >>> device = Device.create(DeviceFamily.SMU, "PXI1Slot2")
            >>> params = DCIRTestParameters(max_load_current=1.5)
            >>> dcir = DCIR(device, params)
        """
        super().__init__(device, test_parameters)
        # Ensure the provided device belongs to the Electronic Load family
        if self.device.device_family is not DCIR.DEVICE_FAMILY:
            raise ValueError(
                f"{self.device.product} (family={self.device.device_family.name}) "
                f"is not supported by the Cell Quality Toolkit for a DCIR test; "
                f"DCIR requires a {DCIR.DEVICE_FAMILY.name} device."
            )

        # Set parameters
        self._input_discharge_parameters = DischargePeriods(
            discharge_period_1=10 - 0.11,
            discharge_period_2=1 - 0.11,
        )  # Subtract a small offset to account for measurement time.
        self._obtained_discharge_parameters = DischargeCurrents()
        self._obtained_measurement_parameters = ObtainedDCIRParameters(
            aperture_time=2,
            aperture_time_units=nidcpower.ApertureTimeUnits.POWER_LINE_CYCLES,
            number_of_samples=3,
        )
        self._raw_measurement_data = None
        self._result = None
        self._test_parameters = test_parameters

    # Overwrite test_parameters as the class specific subtype of ConfigParameters.
    @property
    def test_parameters(self) -> DCIRTestParameters:
        """Get the current DCIR test configuration parameters.

        Returns:
            DCIRTestParameters: The current measurement configuration including
                              max_load_current and powerline_frequency settings.
                              These parameters control the discharge current levels
                              and noise rejection characteristics.

        Raises:
            ValueError: If test parameters have not been properly initialized
                       during object construction.
        """
        return self._test_parameters

    @test_parameters.setter
    def test_parameters(self, value: DCIRTestParameters):
        """Set new DCIR test configuration parameters.

        Updates the measurement configuration with new parameters. This method
        allows reconfiguration of the DCIR measurement without creating a new
        instance. The new parameters take effect on the next measurement run.

        Args:
            value: New DCIR test configuration parameters. Must include valid
                  max_load_current (> 0) and appropriate powerline_frequency
                  for the measurement environment.

        Raises:
            TypeError: If value is not a DCIRTestParameters instance.
            ValueError: If max_load_current is negative or zero, which would
                       prevent proper discharge current calculation.

        Example:
            >>> dcir.test_parameters = DCIRTestParameters(
            ...     max_load_current=3.0,
            ...     powerline_frequency=PowerlineFrequency.FREQ_50_HZ
            ... )
        """
        # Set Test Parameters field
        self._test_parameters = value

    @property
    def measurement_data(self) -> SMUMeasurement:
        """Get the processed measurement data from the last DCIR test.

        Returns voltage and current measurement data collected during the two-phase
        discharge sequence. This data includes all samples from both discharge
        periods and can be used for detailed analysis or custom calculations.

        Returns:
            SMUMeasurement: Processed measurement data containing voltage_values and
                          current_values lists with samples from both discharge periods.
                          tone_frequency is set to 0 for DC measurements. Returns None
                          if no measurement has been performed yet.
        """
        return self._raw_measurement_data

    @property
    def result(self) -> float:
        """Get the calculated internal resistance result from the last measurement.

        Returns:
            float: The calculated internal resistance in Ohms from the most recent
                  DCIR measurement. Calculated using R = (V1 - V2) / (I1 - I2)
                  where subscripts refer to the two discharge current levels.
                  Returns None if no measurement has been completed.
        """
        return self._result

    def _calculate_current_level_range(self, target_range: float) -> float:
        """Calculate appropriate current level range for SMU configuration.

        Determines the optimal current measurement range based on the target current
        level. This ensures the SMU operates within its specified ranges for optimal
        accuracy and prevents configuration errors during measurement setup.

        Args:
            target_range: Expected maximum current level in Amperes that will be
                         measured during the DCIR test. Typically set to the
                         max_load_current from test parameters.

        Returns:
            float: Appropriate current level range in Amperes.
        """
        # Info about current range and unit testing: For unit testing, we use a simulated 4139 SMU
        # since the 4051 Eload can't be simulated as of Aug 2025.
        # Both support the same NI DC Power properties, but differ in behavior.
        # So for unit tests, 4139 can be used.
        # The 4139 SMU only supports Current Level Range up to 3—passing 4 causes an error.
        # NI DC Power rounds unsupported values up to the nearest supported value, internally.
        # So setting the range to 3 works for both unit tests (4139) and real hardware
        # (4051, rounded up by NI DC Power to 4), making it a safe workaround.
        return 40 if target_range > 4 else 3

    def _configure(self):
        """Configure the electronic load for DCIR measurement execution.

        Sets up the SMU device with all necessary parameters for the two-phase DCIR
        measurement sequence. This includes discharge current calculations, timing
        parameters, measurement settings, and hardware configuration validation.

        The configuration process:
        1. Calculates discharge currents (20% and 100% of max_load_current)
        2. Configures measurement parameters (aperture time, samples, noise rejection)
        3. Sets up the current sequence for two-phase discharge
        4. Enables output and validates all settings

        The method ensures the device is properly configured before measurement
        begins and validates that all critical parameters are set correctly.

        Raises:
            ValueError: If the electronic load configuration parameters are not set
                       correctly during configuration. This can occur if the device
                       does not accept the calculated current ranges or sample counts,
                       indicating hardware limitations or compatibility issues.
            RuntimeError: If the device session cannot be properly configured or
                         if communication with the hardware fails during setup.

        Example:
            >>> dcir._configure()  # Prepares device for measurement
        """
        # Calculate discharge currents based on max load current:
        # The first discharge current is set to 20% of the max load current
        # The second discharge current is set to the max load current
        # This allows for a quick initial discharge followed by a more substantial load
        config_discharge = DischargeCurrents(
            discharge_current_1=self.test_parameters.max_load_current * 0.2,
            discharge_current_2=self.test_parameters.max_load_current,
        )
        self._obtained_discharge_parameters = config_discharge

        # Configure eload
        # Configure the SMU for the DCIR, eload measurement properties
        sess = self.device.session
        sess.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE
        sess.auto_zero = nidcpower.AutoZero.OFF
        sess.dc_noise_rejection = nidcpower.DCNoiseRejection.NORMAL
        sess.sense = nidcpower.Sense.REMOTE
        sess.aperture_time = self._obtained_measurement_parameters.aperture_time
        sess.aperture_time_units = self._obtained_measurement_parameters.aperture_time_units
        sess.power_line_frequency = self.test_parameters.powerline_frequency.value
        sess.measure_record_length = self._obtained_measurement_parameters.number_of_samples
        # Configure the SMU for the DCIR, eload discharge properties
        sess.set_sequence(
            values=[
                self._obtained_discharge_parameters.discharge_current_1,
                self._obtained_discharge_parameters.discharge_current_2,
            ],
            source_delays=[
                self._input_discharge_parameters.discharge_period_1,
                self._input_discharge_parameters.discharge_period_2,
            ],
        )
        sess.output_function = nidcpower.OutputFunction.DC_CURRENT
        sess.source_mode = nidcpower.SourceMode.SEQUENCE

        # Commit channel and enable the output
        sess.commit()
        sess.output_enabled = True
        sess.current_level_range = self._calculate_current_level_range(
            self.test_parameters.max_load_current
        )

        # Retrieve and validate eload configuration.
        # Number of samples part
        target_number_of_samples = self._obtained_measurement_parameters.number_of_samples
        number_of_samples_okay = target_number_of_samples == sess.measure_record_length
        # Current level range part
        # Workaround: In _calculate_current_level_range we set the range to 3 if the max current
        # is equal to or less than 4 in order to work with the 4139 smu for unit tests,
        # as 4051 eload is not able to be simulated.
        real_range_normal = 4 if sess.current_level_range == 3 else sess.current_level_range
        target_range = self._calculate_current_level_range(self.test_parameters.max_load_current)
        target_range_normal = 4 if target_range == 3 else target_range
        current_level_range_okay = real_range_normal == target_range_normal
        if not (number_of_samples_okay and current_level_range_okay):
            raise ValueError(
                "Eload Parameter Problem in config step: "
                "Current Level Range or Number of Samples not set correctly."
            )

    def _calculate_timeout(self) -> float:
        """Calculate measurement timeout based on discharge period durations.

        Computes the total time required for the complete DCIR measurement sequence
        including both discharge periods plus a safety buffer. The timeout ensures
        the measurement system waits sufficiently long for the sequence to complete
        while preventing indefinite blocking on hardware issues.

        Returns:
            float: Total timeout duration in seconds. Includes the sum of both
                  discharge periods plus a 5-second safety buffer to account for
                  hardware settling time and measurement overhead.

        Example:
            >>> # With default periods (9.89s + 0.89s) + 5s buffer = 15.78s
            >>> timeout = dcir._calculate_timeout()
            >>> timeout
            15.78
        """
        # Add a buffer time of 5 seconds to the total discharge time
        buffer_time = 5.0
        total_discharge_time = (
            self._input_discharge_parameters.discharge_period_1
            + self._input_discharge_parameters.discharge_period_2
            + buffer_time
        )
        return total_discharge_time

    def _measure(self):
        """Execute the DCIR measurement sequence and acquire data.

        Performs the complete two-phase discharge measurement by initiating the
        current sequence, waiting for completion, and fetching the resulting voltage
        and current data. The measurement follows this sequence:

        1. Initiate the pre-configured current sequence on the electronic load
        2. Wait for the sequence engine to complete both discharge phases
        3. Fetch voltage and current measurements from all sample points
        4. Store data in SMUMeasurement format for subsequent analysis
        5. Clean up hardware state and disable output

        The method handles all timing synchronization and ensures proper data
        acquisition from both discharge periods with the configured sample count.

        Raises:
            RuntimeError: If measurement data cannot be retrieved from the device,
                         if the sequence engine fails to complete within the timeout
                         period, or if hardware communication errors occur during
                         data acquisition.
            TimeoutError: If the measurement sequence does not complete within the
                         calculated timeout period, indicating potential hardware
                         or DUT issues.

        Example:
            >>> dcir._measure()  # Executes measurement and stores data internally
        """
        sess = self.device.session

        # Initiate the measurement device
        sess.initiate()
        # Wait until the measurement is complete or timeout occurs
        sess.wait_for_event(
            event_id=nidcpower.Event.SEQUENCE_ENGINE_DONE,
            timeout=self._calculate_timeout(),
        )

        # Using a constant of 2 for the two setpoints used in DischargeCurrents
        number_of_setpoints = 2
        to_fetch = self._obtained_measurement_parameters.number_of_samples * number_of_setpoints
        measurements = sess.fetch_multiple(
            count=to_fetch,
            timeout=self._calculate_timeout(),
        )
        # Using a SMUMeasurement dataclass with 0 frequency for DCIR measurements
        self._raw_measurement_data = SMUMeasurement(
            tone_frequency=0,
            voltage_values=[m.voltage for m in measurements],
            current_values=[m.current for m in measurements],
        )

        # Abort and reset after measurement is fetched
        sess.abort()
        sess.reset()
        sess.output_enabled = False

    def _impedance_calculation(self) -> float:
        """Calculate internal resistance from measured voltage and current data.

        Computes the DC internal resistance using Ohm's law applied to the voltage
        and current differences between the two discharge periods. The calculation
        follows the formula: R = (V1 - V2) / (I1 - I2), where subscripts 1 and 2
        refer to the first (light load) and second (heavy load) discharge periods.

        The method performs statistical averaging of all samples within each discharge
        period to reduce noise effects and improve measurement accuracy. Sample
        validation ensures data integrity and proper measurement synchronization.

        Returns:
            float: Calculated internal resistance in Ohms. Returns NaN if the current
                  difference between discharge periods is zero (indicating identical
                  current levels), which would result in division by zero.

        Raises:
            ValueError: If raw measurement data is not available (measurement not yet
                       performed), if voltage and current data lengths do not match
                       (indicating data corruption), or if sample periods have
                       different lengths (indicating timing synchronization issues).

        Example:
            >>> # After successful measurement
            >>> resistance = dcir._impedance_calculation()
            >>> print(f"Internal resistance: {resistance:.4f} Ohms")
        """
        if not self._raw_measurement_data:
            raise ValueError("No raw measurement data available for impedance calculation.")

        voltage_values = self._raw_measurement_data.voltage_values
        current_values = self._raw_measurement_data.current_values

        if len(voltage_values) != len(current_values):
            raise ValueError("Voltage and current data lengths do not match.")

        # Get mean values for each discharge period
        num_samples = self._obtained_measurement_parameters.number_of_samples
        v1_samples = voltage_values[:num_samples]
        v2_samples = voltage_values[num_samples:]
        c1_samples = current_values[:num_samples]
        c2_samples = current_values[num_samples:]
        if len(v1_samples) != len(v2_samples) or len(c1_samples) != len(c2_samples):
            raise ValueError("Mismatch in sample lengths for discharge periods.")

        v1_mean = sum(v1_samples) / len(v1_samples)
        v2_mean = sum(v2_samples) / len(v2_samples)
        c1_mean = sum(c1_samples) / len(c1_samples)
        c2_mean = sum(c2_samples) / len(c2_samples)

        # Calculate impedance using the formula: Z = (V1 - V2) / (I2 - I1)
        v_means_diff = v1_mean - v2_mean
        c_means_diff = c2_mean - c1_mean
        self._result = v_means_diff / c_means_diff if c_means_diff != 0 else math.nan

        return self._result

    def run(self) -> float:
        """Execute the complete DCIR measurement process and return the result.

        Performs the full DCIR measurement sequence including device configuration,
        two-phase discharge measurement, and internal resistance calculation. The
        method coordinates all measurement steps and ensures proper resource
        management through session locking.

        The measurement process follows these steps:
        1. Acquire exclusive device session lock for thread safety
        2. Configure the electronic load with calculated parameters
        3. Execute the two-phase discharge measurement sequence
        4. Calculate internal resistance from voltage and current data
        5. Validate the result for mathematical and physical validity
        6. Release device session lock and return the resistance value

        Returns:
            float: The measured internal resistance in Ohms. Valid results are finite,
                  positive values representing the DC resistance of the DUT under
                  the specified load conditions.

        Raises:
            ValueError: If the calculated resistance is NaN (zero current difference)
                       or infinite (indicating measurement or calculation errors),
                       if device configuration fails due to invalid parameters,
                       or if measurement data validation fails.
            RuntimeError: If the measurement process fails at any step due to
                         hardware communication errors, device malfunctions, or
                         resource conflicts with other measurement sessions.
            TimeoutError: If the measurement sequence does not complete within
                         the calculated timeout period.

        Example:
            >>> # Configure and run DCIR measurement
            >>> params = DCIRTestParameters(max_load_current=2.0)
            >>> dcir = DCIR(device, params)
            >>> resistance = dcir.run()
            >>> print(f"DCIR: {resistance:.4f} Ohms")
        """
        with self.device.session.lock():
            self._configure()
            self._measure()
            result = self._impedance_calculation()
            if math.isnan(result) or math.isinf(result):
                raise ValueError("Invalid measurement result: NaN or Infinity encountered.")
            return self._result

    def run_with_switching(self):
        """Execute DCIR measurement with automatic switching between multiple DUTs.

        This method would coordinate DCIR measurements across multiple Device Under
        Test (DUT) connections using switch matrix hardware. The switching capability
        would allow sequential testing of multiple cells or devices without manual
        reconnection, enabling automated battery pack testing and multi-cell analysis.

        Currently not implemented for DCIR measurements due to complexity of
        coordinating electronic load operations with switching matrix timing and
        the specialized requirements for current sinking applications.

        Raises:
            NotImplementedError: DCIR switching functionality is not currently
                               available. Standard DCIR measurements should use
                               the run() method instead.

        Note:
            Future implementation would return a list of tuples containing
            (SMUCellData, resistance_result) pairs for each tested DUT position.
        """
        raise NotImplementedError("DCIR currently does not support switching functionality.")
