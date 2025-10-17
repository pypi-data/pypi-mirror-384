#  NI Battery Cell Quality (nibcq) Python API

## Overall Status

| **Project Info** | |
|---|---|
| **Package** | NI Battery Cell Quality Toolkit Python API |
| **Author** | NI |

<!-- | **main branch status** | [![CI Build Status](https://github.com/ni/nibcq-python/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ni/nibcq-python/actions/workflows/ci.yml) [![License](https://img.shields.io/github/license/ni/nibcq-python.svg)](https://github.com/ni/nibcq-python/blob/main/LICENSE) | -->

## About

Use the *nibcq* Python package to perform battery cell characterization measurement testing on NI hardware. The package provides high-level APIs for the following tests:
- Electrochemical Impedance Spectroscopy (EIS)
- AC Internal Resistance (ACIR)
- DC Internal Resistance (DCIR)
- Open Circuit Voltage (OCV)

---

## API Status

| **Status** | **Details** |
|---|---|
| **PyPI Version** | [![PyPI Version](https://img.shields.io/pypi/v/nibcq.svg)](https://pypi.org/project/nibcq/) |
| **Supported Python Versions** | [![Python Version](https://img.shields.io/pypi/pyversions/nibcq.svg)](https://pypi.org/project/nibcq/) |
| **Documentation** | [![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://ni.github.io/nibcq-python) |
| **Downloads** | [![PyPI Downloads](https://static.pepy.tech/personalized-badge/nibcq?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/nibcq) |
| **Driver Version Tested Against** | 2025 Q4 |

<!--| **Package Status** | [![CI Build Status](https://github.com/ni/nibcq-python/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ni/nibcq-python/actions/workflows/ci.yml) | -->
<!--| **Documentation Generator** | [![Docs Build Status](https://github.com/ni/nibcq-python/actions/workflows/docs.yml/badge.svg?branch=main)](https://github.com/ni/nibcq-python/actions/workflows/docs.yml) |-->

> **Note**: NI created and supports nibcq.

### Contributing

**At this time, NI is not accepting external contributions.**

The nibcq library is under development. While we appreciate interest from our community, we are not set up to handle external pull requests, issues, or contributions. This policy may change in the future.

---

## Features

The nibcq package includes support for the following features.
- **Electrochemical Impedance Spectroscopy (EIS)** - Conduct a multi-frequency impedance characterization
- **AC Internal Resistance (ACIR)** - Conduct a single-frequency impedance measurement  
- **DC Internal Resistance (DCIR)** - Conduct a two-point DC resistance measurement
- **Open Circuit Voltage (OCV)** - Conduct a precision voltage measurement at rest
- **Advanced Compensation Logic** - Support multiple methods for your complex compensation system:
  - **Short Compensation**: Remove cable and contact resistance using short-circuit measurements
  - **Golden DUT Compensation**: Calibrate your DUT using known reference devices
  - **Short with Known Impedance Table (KIT)**: Isolate test fixture impedance by subtracting known reference resistor values for a precise jig-only compensation
- **Temperature Monitoring** - Track temperature during measurements
- **Switch Control** - Automate multi-DUT testing with NI switch modules
- **Self-Calibration Diary Logging** - Manage NI hardware self-calibration with persistent logging, tracking calibration history, temperature conditions, and time-based validity

---

## System Requirements

### Software Requirements

The nibcq package requires the following software:
- **Python**: 3.12 or later (required)
- **NI Driver Runtimes** (required):
  - NI-DCPower
  - NI-DMM  
  - NI-Switch
  - NI-DAQmx

> **Note**: Installing the Battery Cell Quality Toolkit through NI Package Manager automatically installs all required NI drivers.

> **Note**: The nibcq package uses NumPy for impedance calculations and signal processing. NumPy installs automatically as a dependency with nibcq.

### Supported Devices

#### Source Measure Units (SMUs)
EIS and ACIR testing requires the following NI hardware:
- NI PXIe-4139
- NI PXIe-4139 40W

#### Electronic Loads
DCIR testing requires the following NI hardware:
- NI PXIe-4051

#### Digital Multimeters (DMMs)
OCV testing requires the following NI hardware:
- NI PXI-4071 (Note: Not available for purchase)
- NI PXIe-4081

#### Switch Modules
Multi-DUT tests use the following optional NI hardware:
- NI PXI-2525
- NI PXIe-2530B

#### Thermocouple Input Modules
Temperature sensing tests use the following optional NI hardware:
- NI PXIe-4353

---

## Installation

Use pip to install the nibcq package through the following command:

```bash
pip install nibcq
```

> **Note**: To visualize EIS measurement results, install matplotlib through the following command:
> ```bash
> pip install matplotlib
> ```

---

## Quick Start

### Basic Measurement Workflow

All nibcq package measurements use the following Python pattern:

```python
from nibcq import Device, ACIR, ACIRTestParameters
from nibcq.enums import DeviceFamily

# 1. Connect the device
with Device.create(DeviceFamily.SMU, resource_name="PXI1Slot3") as device:

    # 2. Configures the test parameters from a file or programmatically
    test_params = ACIRTestParameters.from_file("ACIRConfigFile.json")

    # 3. Creates a measurement instance
    acir = ACIR(device, test_params, test_frequency=1000.0)

    # 4. Loads a compensation (Also needed if set to NO_COMPENSATION)
    compensation = acir.load_compensation_file()

    # 5. Runs a measurement
    result = acir.run(compensation)

    # 6. Accesses the results
    print(f"Impedance: {result.impedance} Ω")
```

### Available Measurement Types

```python
# OCV - DMM based
from nibcq import OCV, OCVTestParameters
from nibcq.enums import DMMRange
ocv = OCV(device, OCVTestParameters(
    range=DMMRange.DC_10V,
    aperture_time=1.0,
    number_of_averages=10,
    adc_calibration=True
))
start, end, voltage = ocv.run()

# ACIR - Single frequency
from nibcq import ACIR, ACIRTestParameters
from nibcq.enums import CompensationMethod
acir = ACIR(device, ACIRTestParameters(
    voltage_limit_hi=5.0,
    nominal_voltage=3.7,
    current_amplitude=0.1,
    number_of_periods=20,
    compensation_method=CompensationMethod.SHORT
), test_frequency=1000.0)
result = acir.run(compensation)

# EIS - Multi-frequency
from nibcq import EIS, EISTestParameters, FrequencySet
eis = EIS(device, EISTestParameters(
    voltage_limit_hi=5.0,
    nominal_voltage=3.7,
    compensation_method=CompensationMethod.SHORT,
    frequency_sweep_characteristics={
        10000.0: FrequencySet(current_amplitude=0.1, number_of_periods=1000),
        1000.0: FrequencySet(current_amplitude=0.1, number_of_periods=100),
        100.0: FrequencySet(current_amplitude=0.1, number_of_periods=10)
    }
))
results = eis.run(compensation)
nyquist, magnitude, phase = eis.get_plots()  # Get plot data

# DCIR - Electronic load-based
from nibcq import DCIR, DCIRTestParameters
from nibcq.enums import PowerlineFrequency
dcir = DCIR(device, DCIRTestParameters(
    max_load_current=2.0,
    powerline_frequency=PowerlineFrequency.FREQ_60_HZ
))
resistance = dcir.run()
```

---

## Advanced Features

The nibcq package includes support for the following advanced features.
- **Multi-DUT Testing with Switching** - Test DUTs sequentially in multiple test jigs using a SMU or a DMM
- **Temperature Monitoring** - Perform tests with temperature monitoring
- **Device Self-Calibration** - Set Devices to perform a self-calibration under specific circumstances
- **Compensation File Creation** - Create compensation values to account for the impedance of cables, connectors, and other components in the measurement path

### Multi-DUT Testing with Switching

```python
from nibcq import Device, ACIR, ACIRTestParameters
from nibcq.enums import DeviceFamily, SwitchDeviceType, SwitchTopology
from nibcq.switch import SwitchConfiguration

# Connect to the SMU
with Device.create(DeviceFamily.SMU, resource_name="PXI1Slot3") as device:
    # Configure switching
    switch_config = SwitchConfiguration(
        topology=SwitchTopology.SWITCH_2_WIRE_QUAD_16X1_MUX,
        channels=["ch0", "ch1", "ch2", "ch3"]
    )

    # Add switching capability to the device
    device.with_switching(
        config=switch_config,
        sense_switch_resource_name="PXI1Slot5",
        source_switch_resource_name="PXI1Slot6",
        dmm_switch_type=SwitchDeviceType.PXIe_2530B
    )

    # Configure the measurement
    test_params = ACIRTestParameters.from_file("ACIRConfigFile.json")
    acir = ACIR(device, test_params, test_frequency=1000.0)
    compensation = acir.load_compensation_file()

    # Run the measurement on all channels
    results = acir.run_with_switching(compensation)

    # Display the results per channel
    for cell_data, result in results:
        print(f"Channel {cell_data.channel_name}: {result.impedance} Ω")
```

### Temperature Monitoring

```python
from nibcq import Device, ACIR, ACIRTestParameters
from nibcq.enums import DeviceFamily
from nibcq.temperature import ThermocoupleSettings

# Connect to the SMU
with Device.create(DeviceFamily.SMU, resource_name="PXI1Slot3") as device:
    # Add the temperature monitoring
    tc_settings = ThermocoupleSettings("PXI1Slot7/ai0")
    device.with_temperature(tc_settings)

    # Configure and run the measurement
    test_params = ACIRTestParameters.from_file("ACIRConfigFile.json")
    acir = ACIR(device, test_params, test_frequency=1000.0)
    compensation = acir.load_compensation_file()
    # Optional - Set acceptable temperature delta for validation
    acir.acceptable_temperature_delta = 5.0  # degrees Celsius

    result = acir.run(compensation)

    # Measure and display temperature
    acir.measure_temperature()
    print(f"Impedance: {result.impedance} Ω at {acir.temperature:.2f} °C")
```

### Device Self-Calibration

```python
from nibcq import Device, Calibrator
from nibcq.calibration import Settings
from nibcq.enums import DeviceFamily

# Connect to the device
with Device.create(DeviceFamily.SMU, resource_name="PXI1Slot3") as device:
    # Configure the calibration settings
    cal_settings = Settings(
        temperature_delta=2.0,  # °C tolerance
        days_to_calibration=1,  # Recalibration interval in days
    )

    # Create the calibrator
    calibrator = Calibrator(device, cal_settings)

    # Validate the calibration
    if not calibrator.last_calibration_is_valid:
        print("Calibration required - running self-calibration...")
        calibrator.self_calibrate()
        print("Calibration complete!")
    else:
        print("Calibration is valid.")
```

### Compensation File Creation

```python
from nibcq import Device, ACIR, ACIRTestParameters
from nibcq.enums import DeviceFamily

with Device.create(DeviceFamily.SMU, "PXI1Slot3") as device:
    # Create the compensation file with a connected short circuit
    acir = ACIR(device, ACIRTestParameters.from_file("ACIRConfigFile.json"), 1000.0)
    comp_file_path = acir.write_compensation_file(
        comment="Short compensation at 1 kHz"
    )
    print(f"Compensation file created: {comp_file_path}")
```

---

## Documentation

- **API Reference**: [nibcq Documentation](https://ni.github.io/nibcq-python/)
- **Battery Cell Quality Toolkit Manual**: [NI Documentation](https://www.ni.com/docs/en-US/bundle/battery-cell-quality-toolkit)
- **Examples**: Refer to the [examples directory](https://github.com/ni/nibcq-python/tree/main/examples) in the nibcq-python repository

> **Note**: The nibcq Python repository, and all related examples, are for internal use only. Access is granted only to authorized personnel upon request and approval by NI.

---

## Support and Feedback

- [Contact NI Technical Support](https://www.ni.com/support)

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

For third-party software notices and license information, see the [NOTICE](NOTICE) file.

---

## Related Projects

- [nidcpower](https://github.com/ni/nimi-python/tree/master/generated/nidcpower) - NI-DCPower Python API
- [nidmm](https://github.com/ni/nimi-python/tree/master/generated/nidmm) - NI-DMM Python API  
- [niswitch](https://github.com/ni/nimi-python/tree/master/generated/niswitch) - NI-Switch Python API
- [nidaqmx](https://github.com/ni/nidaqmx-python) - NI-DAQmx Python API
- [NumPy](https://numpy.org/) - Fundamental package for scientific computing with Python (BSD License)
