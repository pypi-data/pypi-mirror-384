from datetime import date
from decimal import Decimal

from datetime import timedelta

from .common import _to_decimal, _Z


class DateDict:
    def __init__(self, data=dict()):
        self.data: dict[str, Decimal | None] = data

    def create(self, start_date, end_date, value: Decimal) -> "DateDict":
        """
        Create a new graph with a specified range and value.
        The range is defined by start_date and end_date.
        If the value is None, it will not be included in the graph.
        """
        start = (
            date.fromisoformat(start_date)
            if isinstance(start_date, str)
            else start_date
        )
        end = date.fromisoformat(end_date) if isinstance(end_date, str) else end_date
        self.data = {
            date.strftime("%Y-%m-%d"): (value if value is not None else None)
            for date in (
                start + timedelta(days=i) for i in range((end - start).days + 1)
            )
        }
        return self

    def get(self, key: str, default: Decimal) -> Decimal:
        """
        Get the value for a specific date. If the date does not exist, return the default value.
        The date should be in the format yyyy-mm-dd.
        If the value is None, return the default value.
        """
        return self.data.get(key) or default

    def __getitem__(self, key) -> Decimal | None:
        return self.data.get(key, None)

    def __setitem__(self, key: str, value) -> None:
        self.data[key] = value

    def crop(self, start: str | None = None, end: str | None = None) -> "DateDict":
        """
        Crop the graph data to a specific range defined by start and end.
        If any of the parameters is None, it will not filter by that parameter.
        """
        if start is None and end is None:
            return self
        return DateDict(
            {
                k: v
                for k, v in self.data.items()
                if (start is None or k >= start) and (end is None or k <= end)
            }
        )

    def sum(self: "DateDict") -> Decimal:
        """
        Calculate the sum of all values in the graph.
        If a value is None, it is treated as zero.
        """
        return Decimal(
            sum(value if value is not None else _Z for value in self.data.values())
        )

    def __add__(self, other: "Decimal | DateDict") -> "DateDict":
        if isinstance(other, Decimal):
            return DateDict(
                {
                    k: (v + other if v is not None else None)
                    for k, v in self.data.items()
                }
            )
        else:
            return DateDict(
                {
                    k: ((v + (other.data.get(k) or _Z) if v is not None else None))
                    for k, v in self.data.items()
                }
            )

    def __mul__(self, other: "Decimal | DateDict") -> "DateDict":
        if isinstance(other, Decimal):
            return DateDict(
                {
                    k: (v * other if v is not None else None)
                    for k, v in self.data.items()
                }
            )
        elif isinstance(other, DateDict):
            return DateDict(
                {
                    k: ((v * (other.data.get(k) or _Z) if v is not None else None))
                    for k, v in self.data.items()
                }
            )

    def __sub__(self, other: "Decimal | DateDict") -> "DateDict":
        return self + (other * Decimal(-1))

    def __truediv__(self, other: "Decimal | DateDict") -> "DateDict":
        if isinstance(other, Decimal):
            return DateDict(
                {
                    k: (v / other if v is not None else None)
                    for k, v in self.data.items()
                }
            )
        elif isinstance(other, DateDict):
            return DateDict(
                {
                    k: ((v / (other.data.get(k) or _Z) if v is not None else None))
                    for k, v in self.data.items()
                }
            )

    def to_dict(self) -> dict[str, Decimal | None]:
        """
        Convert the graph data to a dictionary.
        This is useful for serialization or returning as a response.
        """
        return self.data.copy()

    def average(self) -> Decimal:
        """
        Calculate the average of all values in the graph.
        If there are no valid values, return Decimal(0).
        """
        valid_values = [v for v in self.data.values() if v is not None]
        if not valid_values:
            return _Z
        return Decimal(sum(valid_values)) / len(valid_values)
