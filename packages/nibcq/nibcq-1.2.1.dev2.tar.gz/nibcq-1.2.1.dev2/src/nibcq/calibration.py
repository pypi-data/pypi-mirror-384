"""Provides Calibration Diary support for different nibcq processes."""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Entry:
    """Represents a single calibration entry in a calibration diary.

    Contains the timestamp and temperature information for when a calibration
    was performed on a measurement device. Used to track calibration history
    and determine when recalibration might be needed.

    Attributes:
        timestamp (datetime): When the calibration was performed
        temperature (float): The ambient temperature during calibration in Celsius

    Examples:
        >>> entry = Entry(datetime.now(), 25.5)
        >>> print(entry)
        CalibrationEntry(timestamp=2025-01-01 12:00:00, temperature=25.5)
    """

    timestamp: datetime
    temperature: float

    def __repr__(self):
        """Return a string representation of the CalibrationEntry.

        Returns:
            str: A formatted string showing the timestamp and temperature

        Examples:
            >>> entry = Entry(datetime(2025, 1, 1, 12, 0), 25.5)
            >>> repr(entry)
            'CalibrationEntry(timestamp=2025-01-01 12:00:00, temperature=25.5)'
        """
        return f"CalibrationEntry(timestamp={self.timestamp}, temperature={self.temperature})"


@dataclass
class Settings:
    """Configuration settings for calibration validation and scheduling.

    Contains the parameters that control when a device needs calibration and
    what temperature variations are acceptable. Used by the calibration system
    to determine if recalibration is required based on time elapsed and
    temperature changes.

    Attributes:
        temperature_delta (float): Maximum acceptable temperature difference in Celsius
            between current temperature and last calibration temperature
        days_to_calibration (float): Number of days after which recalibration is required

    Examples:
        >>> settings = Settings(temperature_delta=2.5, days_to_calibration=1.5)
        >>> print(f"Max temp delta: {settings.temperature_delta}°C")
        >>> print(f"Calibration interval: {settings.days_to_calibration} days")
    """

    temperature_delta: float
    days_to_calibration: float

    def __repr__(self):
        """Return a string representation of the Settings.

        Returns:
            str: A formatted string showing temperature delta and days to calibration

        Examples:
            >>> settings = Settings(2.5, 1.5)
            >>> repr(settings)
            'Settings(temperature_delta=2.5, days_to_calibration=1.5)'
        """
        return (
            f"Settings(temperature_delta={self.temperature_delta}, "
            f"days_to_calibration={self.days_to_calibration})"
        )


class Diary:
    """Manages calibration diary operations for tracking device calibration history.

    Handles reading, writing, and parsing calibration entries in CSV format.
    Each entry contains a timestamp and temperature from when calibration was
    performed. The diary is used to determine when recalibration is needed
    based on elapsed time and temperature changes.

    Attributes:
        file_path (str): Path to the calibration diary CSV file

    Examples:
        >>> diary = Diary("/path/to/calibration.csv")
        >>> entry = diary.last_entry
        >>> print(f"Last calibrated at {entry.timestamp}")
    """

    file_path: str

    def __init__(self, file_path: str, settings: Optional[Settings] = None):
        """Initialize a Calibration Diary with the specified file location.

        Creates a new calibration diary instance that can read and write
        calibration entries to the specified CSV file. If the file doesn't
        exist, it will be created when the first entry is added.

        Args:
            file_path (str): Path to the calibration diary CSV file.
                Will be created if it doesn't exist.
            settings (Settings, optional): Calibration settings for validation.
                If None, default settings will be used.

        Raises:
            ValueError: If file_path is empty or None
            PermissionError: If the file path is not writable

        Examples:
            >>> diary = Diary("/path/to/calibration.csv")
            >>> diary = Diary("calibration.csv", Settings(2.5, 1.5))
        """
        if not file_path:
            raise ValueError("File path cannot be empty")
        self.file_path = file_path
        self.settings = settings or Settings(temperature_delta=2, days_to_calibration=1)

    @property
    def last_entry(self):
        """Get the most recent calibration entry from the diary.

        Reads the calibration diary file and returns the latest calibration
        entry containing timestamp and temperature information. This is used
        to determine when the device was last calibrated and under what
        temperature conditions.

        Returns:
            Entry: The most recent calibration entry with timestamp and temperature

        Raises:
            FileNotFoundError: If the calibration diary file doesn't exist
            ValueError: If the diary file format is invalid or corrupted
            PermissionError: If the file cannot be read due to permissions

        Examples:
            >>> diary = Diary("calibration.csv")
            >>> entry = diary.last_entry
            >>> print(f"Last calibrated: {entry.timestamp} at {entry.temperature}°C")
        """
        return self._load_last_entry()

    @staticmethod
    def _parse_calibration_line(line: str):
        """Parse a single calibration entry line from the diary file.

        Parses calibration entries in the format '2025-7-7 - 11:54 - 29,1 C'
        and extracts the timestamp and temperature information. Handles both
        comma and period decimal separators for international compatibility.

        Args:
            line (str): A single line from the calibration diary file containing
                date, time, and temperature information separated by ' - '

        Returns:
            tuple[datetime, float]: A tuple containing the parsed datetime
                and temperature value in Celsius

        Raises:
            ValueError: If the line format is invalid or cannot be parsed

        Examples:
            >>> dt, temp = Diary._parse_calibration_line("2025-1-1 - 12:00 - 25.5 C")
            >>> print(f"Parsed: {dt} at {temp}°C")
        """
        # Remove trailing newline and ' C' if present
        line = line.strip()
        if line.endswith(" C"):
            line = line[:-2].strip()
        # Split into date, time, and temperature
        parts = line.split(" - ")
        if len(parts) != 3:
            raise ValueError(f"Invalid calibration entry format: {line}")
        date_str, time_str, temp_str = parts
        # Parse datetime and temperature
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        try:
            temperature = float(temp_str)
        except ValueError:
            # Try replacing ',' with '.' for decimal separator
            try:
                temperature = float(temp_str.replace(",", "."))
            except ValueError:
                raise ValueError(f"Cannot parse temperature value: {temp_str}")
        return dt, temperature

    @staticmethod
    def _detect_decimal_separator(line: str) -> str:
        """Detect the decimal separator used in existing calibration entries.

        Analyzes the format of existing calibration entries to determine
        whether comma or period is used as the decimal separator. This
        ensures new entries match the existing format for consistency.

        Args:
            line (str): A line from the calibration file to analyze for
                decimal separator format

        Returns:
            str: ',' if comma is detected as decimal separator, '.' otherwise

        Examples:
            >>> separator = Diary._detect_decimal_separator("2025-1-1 - 12:00 - 25,5 C")
            >>> print(separator)  # Output: ','
            >>> separator = Diary._detect_decimal_separator("2025-1-1 - 12:00 - 25.5 C")
            >>> print(separator)  # Output: '.'
        """
        # Check the last line (most recent entry) for decimal separator
        if line.strip():
            # Extract temperature part and check for comma
            parts = line.split(" - ")
            if len(parts) >= 3:
                temp_part = parts[2].replace(" C", "").strip()
                if "," in temp_part:
                    return ","
                # If period not exist, or there are no line, prefer period (standard).
        return "."

    @staticmethod
    def _format_float(value: float, precision: int = 1, decimal_separator: str = None) -> str:
        """Format a float using the specified or auto-detected decimal separator.

        Args:
            value: The float value to format
            precision: Number of decimal places
            decimal_separator: Decimal separator to use ('.' or ','). If None, uses '.'

        Returns:
            Formatted float string with the specified decimal separator
        """
        # Format with standard '.' separator first
        format_str = f"{{:.{precision}f}}"
        formatted = format_str.format(value)

        # Replace decimal separator if specified
        if decimal_separator == ",":
            formatted = formatted.replace(".", ",")

        return formatted

    def _load_last_entry(self) -> Entry | None:
        """Load the last calibration entry from the file."""
        try:
            lines = []
            with open(self.file_path, "r") as file:
                lines = file.readlines()
            if lines:
                # Parse the last line as a CalibrationEntry
                last_line = lines[-1].strip()
                # Expected format: "%Y-%m-%d - %H:%M - Temperature C"
                dt, temp = self._parse_calibration_line(last_line)
                return Entry(timestamp=dt, temperature=temp)
        except FileNotFoundError:
            # If no such file exists yet, then there are no calibration entries existing yet.
            return None
        except Exception as e:
            raise RuntimeError(f"Unexpected Error while reading file {self.file_path}: {e}")

    def add_new_entry(self, entry: Entry):
        """Add a new calibration entry to the diary."""
        try:
            # Ensure the parent directory exists
            folder_dir = os.path.dirname(self.file_path)
            if folder_dir != "":
                os.makedirs(folder_dir, exist_ok=True)

            # Read existing lines (if file exists)
            lines = []
            if os.path.exists(self.file_path):
                with open(self.file_path, "r") as file:
                    lines = file.readlines()
            # Keep only the latest 99 lines (if there are more)
            if len(lines) >= 100:
                lines = lines[-99:]

            # Prepare the new entry line
            # Use default decimal separator if no existing lines, otherwise detect from last line
            decimal_separator = "." if not lines else Diary._detect_decimal_separator(lines[-1])
            formatted_temp = Diary._format_float(
                value=entry.temperature,
                precision=1,
                decimal_separator=decimal_separator,
            )
            # Always finish with an empty line (\n at the end)
            new_line = f"{entry.timestamp.strftime('%Y-%m-%d - %H:%M')} - {formatted_temp} C\n"
            lines.append(new_line)

            # Write back the latest 100 lines (including the new one)
            with open(self.file_path, "w") as file:
                file.writelines(lines)

            # TODO Remove
            self._last_entry = entry
        except Exception as e:
            # TODO: Raise the correct error instead of general RuntimeError.
            raise RuntimeError(
                f"Unexpected Error while writing to Calibration file {self.file_path}: {e}"
            )
