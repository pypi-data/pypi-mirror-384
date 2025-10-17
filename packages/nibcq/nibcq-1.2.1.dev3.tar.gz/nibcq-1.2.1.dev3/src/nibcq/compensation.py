"""Support functions and classes for ACIR/EIS Compensation methods."""

import bisect
import json
import math
import os
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from nibcq.constants import DEFAULT_COMPENSATION_DIR
from nibcq.enums import CompensationMethod, InterpolationMode
from nibcq.temperature import CenteredRange

### ---------------------- ###
#   Complex i-j conversion   #
### ---------------------- ###


def _complex_to_i_str(val):
    """Convert complex number to string representation using 'i' notation for JSON serialization.

    Converts Python complex numbers to a string format compatible with LabVIEW
    and JSON serialization. Uses 'i' notation instead of Python's default 'j'
    notation for imaginary components.

    Args:
        val: The value to convert. If complex, converts to 'i' notation string.
            If not complex, returns the value unchanged.

    Returns:
        Union[str, Any]: String representation like '1.0+2.0i' or '1.0-2.0i' for complex values,
            or the original value unchanged if not complex.

    Examples:
        >>> complex_to_i_str(complex(1.0, 2.0))
        '1.0 +2.0 i'
        >>> complex_to_i_str(complex(1.0, -2.0))
        '1.0 -2.0 i'
        >>> complex_to_i_str(5.0)
        5.0
    """
    if isinstance(val, complex):
        # Format as e.g. '1.0+2.0i' or '1.0-2.0i'
        return f"{val.real} {'+' if val.imag >= 0 else ''}{val.imag} i"
    return val


def _i_str_to_complex(val):
    """Convert string representation with 'i' notation back to Python complex number.

    Parses compensation values stored in JSON format with 'i' notation and converts
    them back to Python complex numbers for mathematical operations. Handles the
    conversion from LabVIEW-compatible 'i' notation to Python's 'j' notation.

    Args:
        val: The value to convert. If string containing 'i', converts to complex.
            If not a string with 'i', returns the value unchanged.

    Returns:
        Union[complex, Any]: Python complex number if input was 'i' notation string,
            or the original value unchanged if not applicable.

    Raises:
        ValueError: If the string format is invalid and cannot be parsed as complex

    Examples:
        >>> i_str_to_complex("1.0 +2.0 i")
        (1.0+2.0j)
        >>> i_str_to_complex("1.0 -2.0 i")
        (1.0-2.0j)
        >>> i_str_to_complex(5.0)
        5.0
        >>> i_str_to_complex("not a complex string")
        'not a complex string'
    """
    if isinstance(val, str) and "i" in val:
        val = val.strip().replace("i", "j").replace(" ", "")
        return complex(val)
    return val


### ------------------------------------- ###
#   Compensation representation in Memory   #
### ------------------------------------- ###


@dataclass
class CompensationParameter:
    """Represents compensation parameters for a specific frequency point.

    This class encapsulates the frequency-specific compensation data used in
    ACIR/EIS measurements for error correction. Each instance represents a single
    frequency point with its associated complex impedance compensation value.

    The compensation value is typically obtained through calibration measurements
    using known standards (short circuits, golden reference devices, etc.) and
    is applied to raw measurements to improve accuracy by correcting for systematic
    errors in the measurement system.

    Attributes:
        frequency: The frequency in Hertz for which this compensation applies.
                  Must be a positive value.
        compensation_value: The complex impedance compensation value in Ohms.
                          Applied to raw measurements through mathematical operations
                          (typically subtraction for SHORT compensation).

    Example:
        >>> param = CompensationParameter(frequency=1000.0, compensation_value=10+5j)
        >>> param.frequency
        1000.0
        >>> param.compensation_value
        (10+5j)
    """

    frequency: float
    compensation_value: complex

    @classmethod
    def from_item_dict(cls, item: Dict[str, Any]):
        """Build from a row dict.

        Supports:
          - {"Frequency (Hz)": <float>, "Compensation Value (Ohm)": "<a+b i>"}
        """
        freq = float(item["Frequency (Hz)"])
        val = _i_str_to_complex(item["Compensation Value (Ohm)"])
        return cls(frequency=freq, compensation_value=val)

    def to_item_dict(self) -> Dict[str, Any]:
        """Single item representation used for JSON rows (frequency + value)."""
        return {
            "Frequency (Hz)": self.frequency,
            "Compensation Value (Ohm)": _complex_to_i_str(self.compensation_value),
        }

    @staticmethod
    def dict_to_list(param_dict: Dict[float, complex]) -> list["CompensationParameter"]:
        """Convert a frequency-to-impedance dictionary into a list of CompensationParameter objects.

        Transforms a dictionary mapping frequencies to complex impedance values into
        a structured list of CompensationParameter objects. The resulting list is
        sorted in descending frequency order for consistency with file formats.

        Args:
            param_dict: Dictionary mapping frequency values (Hz) to complex impedance
                       values (Ohms). Frequencies should be positive numbers.

        Returns:
            list[CompensationParameter]: List of CompensationParameter objects sorted
                                       by descending frequency.

        Example:
            >>> freq_dict = {1000.0: 10+5j, 2000.0: 15+3j, 500.0: 8+7j}
            >>> param_list = CompensationParameter.dict_to_list(freq_dict)
            >>> len(param_list)
            3
            >>> param_list[0].frequency  # Highest frequency first
            2000.0
            >>> param_list[0].compensation_value
            (15+3j)
        """
        result: list[CompensationParameter] = []
        # Ensure descending frequency order when reading dictionaries
        for f in sorted(param_dict.keys(), reverse=True):
            v = param_dict[f]
            # Normalize frequency
            freq = float(f)
            # Normalize complex value; remove spaces; accept strings with 'i' or 'j'
            if isinstance(v, str):
                val = _i_str_to_complex(v)
            else:
                val = complex(v)
            result.append(CompensationParameter(frequency=freq, compensation_value=val))
        return result

    @staticmethod
    def list_to_dict(param_list: list["CompensationParameter"]) -> Dict[float, complex]:
        """Convert a list of CompensationParameter objects into a frequency-to-impedance dictionary.

        Transforms a list of CompensationParameter objects into a dictionary mapping
        frequencies to complex impedance values. The resulting dictionary maintains
        descending frequency order for consistency.

        Args:
            param_list: List of CompensationParameter objects to convert.

        Returns:
            Dict[float, complex]: Dictionary mapping frequency values (Hz) to complex
                                impedance values (Ohms), ordered by descending frequency.

        Example:
            >>> params = [
            ...     CompensationParameter(1000.0, 10+5j),
            ...     CompensationParameter(2000.0, 15+3j)
            ... ]
            >>> freq_dict = CompensationParameter.list_to_dict(params)
            >>> freq_dict[1000.0]
            (10+5j)
            >>> list(freq_dict.keys())  # Descending order
            [2000.0, 1000.0]
        """
        # Ensure the returned dictionary is ordered by descending frequency
        return {
            p.frequency: p.compensation_value
            for p in sorted(param_list, key=lambda x: x.frequency, reverse=True)
        }

    @staticmethod
    def validate_frequency_uniqueness(param_list: list["CompensationParameter"]) -> None:
        """Validate that all frequencies in a CompensationParameter list are unique.

        Ensures that there are no duplicate frequency values in the parameter list,
        which is essential for proper interpolation and compensation calculations.
        Duplicate frequencies would create ambiguous compensation values.

        Args:
            param_list: List of CompensationParameter objects to validate.

        Raises:
            ValueError: If duplicate frequencies are found, with details about
                       which frequency is duplicated.

        Example:
            >>> params = [
            ...     CompensationParameter(1000.0, 10+5j),
            ...     CompensationParameter(2000.0, 15+3j)
            ... ]
            >>> CompensationParameter.validate_frequency_uniqueness(params)  # No error
            >>>
            >>> duplicate_params = [
            ...     CompensationParameter(1000.0, 10+5j),
            ...     CompensationParameter(1000.0, 15+3j)  # Same frequency!
            ... ]
            >>> CompensationParameter.validate_frequency_uniqueness(duplicate_params)
            ValueError: Duplicate frequency found: 1000.0 Hz
        """
        frequencies = []
        for param in param_list:
            freq = float(param.frequency)
            if freq in frequencies:
                raise ValueError(f"Duplicate frequency found: {freq} Hz")
            frequencies.append(freq)


@dataclass
class Compensation:
    """Comprehensive compensation data container for ACIR/EIS measurement error correction.

    This class serves as the central data structure for managing compensation information
    used to correct systematic errors in impedance measurements. It contains all necessary
    components including the compensation method, calibration data, temperature information,
    and frequency-specific compensation parameters.

    The compensation system supports multiple correction methods:
    - NO_COMPENSATION: Raw measurements without correction
    - SHORT: Correction using short-circuit calibration data
    - GOLDEN_DUT: Correction using known reference device data

    Attributes:
        compensation_method: The type of compensation to apply (from CompensationMethod enum).
                           Determines how compensation_parameters are used in calculations.
        compensation_file_path: Optional path to the file containing compensation data.
                              Used for traceability and reloading calibration information.
        target_temperature: Temperature conditions for optimal compensation accuracy.
                          Compensation may be temperature-dependent for high-precision work.
        compensation_parameters: Dictionary mapping frequencies (Hz) to complex compensation
                               values (Ohms). Core calibration data for error correction.

    Example:
        >>> compensation = Compensation(
        ...     compensation_method=CompensationMethod.SHORT,
        ...     compensation_file_path="/path/to/cal.json",
        ...     compensation_parameters={1000.0: 10+5j, 2000.0: 15+3j}
        ... )
        >>> compensated_z = compensation.get_compensated_impedance(
        ...     frequency=1000.0,
        ...     measured_impedance=100+20j
        ... )
        >>> # Result: 100+20j - 10+5j = 90+15j (SHORT compensation)
    """

    compensation_method: CompensationMethod = CompensationMethod.NO_COMPENSATION
    compensation_file_path: Optional[str] = None
    target_temperature: Optional[CenteredRange] = None
    compensation_parameters: Dict[float, complex] = field(default_factory=dict)

    def to_list(self) -> List[CompensationParameter]:
        """Converts the AllCompensation instance to a list of CompensationParameters."""
        return CompensationParameter.dict_to_list(self.compensation_parameters)

    @classmethod
    def from_file(
        cls,
        method: CompensationMethod,
        file_path: str,
    ) -> "Compensation":
        """Creates an AllCompensation instance from a compensation file.

        Args:
            method: The compensation method to associate with this data
            file_path: Path to the compensation file to load

        Returns:
            AllCompensation: Instance loaded from the file
        """
        compensation_file = CompensationFile.load_from_file(file_path)
        all_compensation = compensation_file.file_to_memory(method, file_path)

        return all_compensation

    def get_compensated_impedance(
        self,
        frequency: float,
        measured_impedance: complex,
        interpolation_mode: "InterpolationMode" = None,
    ) -> complex:
        """Get the compensated impedance value for a specific frequency.

        This method applies compensation based on the compensation method without needing
        to convert between list/dict representations or use separate subtraction methods.

        Args:
            frequency: The frequency for which to get compensated impedance
            measured_impedance: The raw measured impedance value
            interpolation_mode: Interpolation mode for compensation lookup (defaults to NEAREST)

        Returns:
            complex: The compensated impedance value
        """
        # Use Nearest way by default.
        if interpolation_mode is None:
            interpolation_mode = InterpolationMode.NEAREST

        if self.compensation_method == CompensationMethod.NO_COMPENSATION:
            # No compensation - return measured value as-is
            return measured_impedance

        elif (
            self.compensation_method == CompensationMethod.SHORT
            or self.compensation_method == CompensationMethod.GOLDEN_DUT
        ):
            # Apply SHORT compensation using stored compensation parameters
            if self.compensation_parameters:
                compensation_table = ImpedanceTable.from_dict(self.compensation_parameters)
                compensation_value = compensation_table.value_at(frequency, mode=interpolation_mode)
                return measured_impedance - compensation_value
            else:
                # No compensation parameters available, return measured value as-is
                return measured_impedance

        elif self.compensation_method == CompensationMethod.GOLDEN_DUT:
            # Use stored compensation parameters to get compensation value
            if self.compensation_parameters:
                compensation_table = ImpedanceTable.from_dict(self.compensation_parameters)
                compensation_value = compensation_table.value_at(frequency, mode=interpolation_mode)
                return measured_impedance - compensation_value

        elif self.compensation_method == CompensationMethod.SHORT_GOLDEN_DUT:
            # SHORT_GOLDEN_DUT compensation is not currently supported
            raise NotImplementedError("Short-Golden DUT compensation method is not yet supported")

        else:
            raise ValueError(f"Unknown compensation method: {self.compensation_method}")


### ---------------------------------- ###
#   Compensation File Specific classes   #
### ---------------------------------- ###


@dataclass
class CompensationHeader:
    """Represents the header information for a compensation file.

    Attributes:
        temperature_parameter (TemperatureParameter): The temperature parameters
        associated with the compensation.
        comment (str): Optional comment or description for the compensation file.
    """

    temperature_parameter: CenteredRange
    comment: str


@dataclass
class CompensationFile:
    """Represents a compensation file."""

    header: CompensationHeader
    compensation_values: list[CompensationParameter]

    @classmethod
    def memory_to_file(cls, compensation: Compensation, comment: str = "") -> "CompensationFile":
        """Converts the compensation data format to a stored one.

        This converts the class used to store and calculate these between the one used
        in memory (AllCompensation), to the one what we use to save it to file (CompensationFile).
        """
        header = CompensationHeader(
            temperature_parameter=compensation.target_temperature,
            comment=comment,
        )
        return cls(header=header, compensation_values=compensation.to_list())

    def file_to_memory(self, method: CompensationMethod, file_path: str) -> Compensation:
        """Converts this CompensationFile back to an in-memory AllCompensation.

        Args:
            method (CompensationMethod):
                The CompensationMethod to associate with the in-memory data.
            file_path (str): The source file path for this compensation content.

        Returns:
            AllCompensation: An in-memory representation containing temperature and
                a frequency to complex map of compensation values.

        """
        params_dict = CompensationParameter.list_to_dict(self.compensation_values)
        return Compensation(
            compensation_method=method,
            compensation_file_path=file_path,
            target_temperature=self.header.temperature_parameter,
            compensation_parameters=params_dict,
        )

    def to_json(self) -> str:
        """Convert to NI BCQ Toolkit Compensation File JSON schema.

        Returns:
            str: JSON string in the correct format.

        """
        header_obj = {
            "Temperature Parameters": {
                "Temperature": self.header.temperature_parameter.center,
                "Temperature Delta": self.header.temperature_parameter.delta,
            },
            "Comment": self.header.comment,
        }
        comp_list = [cp.to_item_dict() for cp in self.compensation_values]
        return json.dumps(
            {
                "Compensation Header": header_obj,
                "Compensation Value For Each Frequency": comp_list,
            },
            indent=2,
        )

    @classmethod
    def from_json(cls, data: str):
        """Creates a CompensationFile instance from a JSON string.

        Supports the previously defined LabVIEW schema only, to enforce consistency.
        """
        obj = json.loads(data)

        # Check if the parsed JSON is a dictionary
        if not isinstance(obj, dict):
            raise TypeError("Compensation JSON must be in a supported JSON format")

        # Check if required "Compensation Header" key is present
        if "Compensation Header" not in obj:
            raise KeyError("Missing required 'Compensation Header' in compensation JSON")

        # NI BCQ Toolkit Compensation File schema
        hdr = obj["Compensation Header"]
        if not isinstance(hdr, dict):
            raise ValueError("Compensation Header must be in a supported JSON format")

        # Check for compensation values
        rows = obj.get("Compensation Value For Each Frequency", [])
        if not rows:
            raise ValueError("Compensation file must contain at least one frequency value")

        tp = hdr.get("Temperature Parameters", {})
        temperature = float(tp.get("Temperature", 0.0))
        temperature_delta = float(tp.get("Temperature Delta", 0.0))
        comment = hdr.get("Comment", "")
        # TODO: FIX IT LATER, AS IT GETS FIXED IN LABVIEW TOO
        # 0 values are the default not-used values
        if temperature == 0:
            temperature = math.nan
        if temperature_delta == 0:
            temperature_delta = math.nan
        header = CompensationHeader(
            temperature_parameter=CenteredRange(center=temperature, delta=temperature_delta),
            comment=comment,
        )
        values = [CompensationParameter.from_item_dict(row) for row in rows]
        CompensationParameter.validate_frequency_uniqueness(values)
        return cls(header=header, compensation_values=values)

    @classmethod
    def load_from_file(cls, path: str) -> "CompensationFile":
        """Loads a compensation file from the specified path."""
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_json(f.read())

    def save_to_file(self, path: str) -> None:
        """Saves a compensation file to the specified path."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @staticmethod
    def generate_file_path(compensation_method: CompensationMethod, serial_number: str) -> str:
        """Generates the default file path for a compensation file.

        Args:
            compensation_method: The compensation method type (SHORT or GOLDEN_DUT only)
            serial_number: The device serial number

        Returns:
            str: The generated file path in format
                "DEFAULT_COMPENSATION_DIR/z_{method}_SN{serial}_Ch0.json"

        Raises:
            ValueError: If compensation_method is not SHORT or GOLDEN_DUT
        """
        # Only allow SHORT and GOLDEN_DUT compensation methods
        if compensation_method not in (CompensationMethod.SHORT, CompensationMethod.GOLDEN_DUT):
            raise ValueError(
                f"File path generation only supported for SHORT and GOLDEN_DUT methods, "
                f"got {compensation_method.value}"
            )

        # Use enum value directly for filename
        # In the future the Ch0 can be changed to scale based on actual used channel number.
        filename = f"z_{compensation_method.value}_SN{serial_number}_Ch0.json"
        return os.path.join(DEFAULT_COMPENSATION_DIR, filename)


class ImpedanceTable:
    """Single-list table of CompensationParameter with fast lookups via bisect.

    - Stores one ascending-sorted list[CompensationParameter].
    - Uses a frequency-view for O(log n) LOWER/UPPER/NEAREST/LINEAR lookups.
    """

    class _FreqView:
        """Lightweight sequence exposing only frequencies for bisect over params list."""

        def __init__(self, params: List["CompensationParameter"]):
            self._params = params

        def __len__(self) -> int:
            return len(self._params)

        def __getitem__(self, i: int) -> float:
            return self._params[i].frequency

    def __init__(self, params: List["CompensationParameter"]):
        """Initializes the ImpedanceTable with a sorted list of CompensationParameters."""
        CompensationParameter.validate_frequency_uniqueness(params)
        self._params: List[CompensationParameter] = sorted(params, key=lambda p: p.frequency)
        self._freqs = self._FreqView(self._params)

    @classmethod
    def from_params(cls, params: List["CompensationParameter"]) -> "ImpedanceTable":
        """Creates an ImpedanceTable from a list of CompensationParameters."""
        return cls(params)

    @classmethod
    def from_dict(cls, d: Dict[float, complex]) -> "ImpedanceTable":
        """Creates an ImpedanceTable from a dictionary of frequency/impedance pairs."""
        return cls(CompensationParameter.dict_to_list(d))

    @classmethod
    def from_rows(cls, rows: list[Dict[str, Any]]) -> "ImpedanceTable":
        """Creates an ImpedanceTable from a list of rows."""
        params = [CompensationParameter.from_item_dict(row) for row in rows]
        return cls(params)

    @classmethod
    def from_file(cls, path: str) -> "ImpedanceTable":
        """Creates an ImpedanceTable from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("KIT/Impedance file must be a JSON list of frequency/value rows")
        return cls.from_rows(data)

    def _neighbors(self, f: float) -> tuple[int, int]:
        """Finds the indices of the neighboring frequency points."""
        n = len(self._params)
        pos = bisect.bisect_left(self._freqs, f)

        # Check for exact match
        if pos < n and self._freqs[pos] == f:
            # Exact match - both before and after should point to the same index
            return pos, pos

        # No exact match - find neighboring points
        before = min(max(pos - 1, 0), n - 1)
        after = min(max(pos, 0), n - 1)
        return before, after

    def value_at(self, f: float, mode: InterpolationMode = InterpolationMode.NEAREST) -> complex:
        """Returns the compensation value at the specified frequency.

        This depends on the specified interpolation mode.
        """
        before, after = self._neighbors(f)
        fb = self._params[before].frequency
        fa = self._params[after].frequency
        zb = self._params[before].compensation_value
        za = self._params[after].compensation_value

        if mode == InterpolationMode.LOWER:
            return zb
        if mode == InterpolationMode.UPPER:
            return za
        if mode == InterpolationMode.LINEAR:
            if fa == fb:
                return zb
            t = (f - fb) / (fa - fb)
            return complex(zb.real + t * (za.real - zb.real), zb.imag + t * (za.imag - zb.imag))
        # NEAREST: prefer upper neighbor on tie
        return zb if abs(f - fb) < abs(fa - f) else za
