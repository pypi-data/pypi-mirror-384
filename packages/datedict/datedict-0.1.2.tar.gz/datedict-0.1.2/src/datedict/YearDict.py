from decimal import Decimal

from .common import to_decimal, ZERO


class YearDict:
    def __init__(
        self,
        start_year=2025,
        end_year=2025,
        initial_value: Decimal | int | float = ZERO,
    ):
        self.start_year: int = start_year
        self.end_year: int = end_year
        iv: Decimal = to_decimal(initial_value)
        self.data: dict[int, Decimal] = {
            y: iv for y in range(self.start_year, self.end_year + 1)
        }

    def __getitem__(self, year: int) -> Decimal:
        return self.data[year]

    def __setitem__(self, year: int, value):
        self.data[int(year)] = to_decimal(value)

    def override(self, data: dict[int, Decimal | float | int | str]) -> "YearDict":
        if not data:
            raise ValueError("Data cannot be empty.")
        ys = sorted(data.keys())
        # enforce contiguous coverage
        if ys != list(range(ys[0], ys[-1] + 1)):
            raise ValueError("Data must cover all years in the contiguous range.")
        self.start_year, self.end_year = ys[0], ys[-1]  # inclusive
        self.data = {
            y: to_decimal(data[y]) for y in range(self.start_year, self.end_year + 1)
        }
        return self

    def fit(self, start_year: int, end_year: int, initial_value: Decimal = ZERO):
        self.start_year, self.end_year = int(start_year), int(end_year)
        iv = to_decimal(initial_value)
        self.data = {
            y: to_decimal(self.data[y]) if y in self.data else iv
            for y in range(self.start_year, self.end_year + 1)
        }
        return self

    def non_negative(self) -> "YearDict":
        out = YearDict(self.start_year, self.end_year)
        out.data = {y: (v if v >= ZERO else ZERO) for y, v in self.data.items()}
        return out

    def sum(
        self, start_year: int | None = None, end_year: int | None = None
    ) -> Decimal:
        sy = self.start_year if start_year is None else int(start_year)
        ey = self.end_year if end_year is None else int(end_year)
        return sum((self.data[y] for y in range(sy, ey + 1) if y in self.data), ZERO)

    def __mul__(self, other):
        result = YearDict(self.start_year, self.end_year)
        if isinstance(other, (int, float, Decimal)):
            result.data = {
                year: Decimal(value) * Decimal(str(other))
                for year, value in self.data.items()
            }
        elif isinstance(other, YearDict):
            result.data = {
                year: Decimal(self.data[year]) * Decimal(other.data[year])
                for year in self.data.keys() & other.data.keys()
            }
        else:
            return NotImplemented
        return result

    def __rmul__(self, other):
        return self.__mul__(other)

    def __add__(self, other):
        result = YearDict(self.start_year, self.end_year)
        if isinstance(other, (int, float, Decimal)):
            result.data = {
                year: value + Decimal(str(other)) for year, value in self.data.items()
            }
        elif isinstance(other, YearDict):
            result.data = {
                year: Decimal(self.data[year]) + Decimal(other.data[year])
                for year in self.data.keys() & other.data.keys()
            }
        else:
            return NotImplemented
        return result

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return self.__add__(-1 * other)

    def __str__(self):
        return "\n".join(f"{y}: {v}" for y, v in sorted(self.data.items()))

    def __repr__(self):
        return f"{self.data!r}"

    def to_array(self):
        return [self.data[y] for y in range(self.start_year, self.end_year + 1)]

    def to_dict(self):
        return dict(self.data)
