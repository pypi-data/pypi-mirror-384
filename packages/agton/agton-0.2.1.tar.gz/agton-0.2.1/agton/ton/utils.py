from decimal import Decimal, ROUND_DOWN

from .cell.cell import Cell
from .cell.builder import begin_cell

def to_units(value: str | float | int, decimals: int) -> int:
    try:
        tons = Decimal(str(value))
        nanounits = (tons * 10**decimals).to_integral_value(rounding=ROUND_DOWN)
        return int(nanounits)
    except Exception as e:
        raise ValueError(f"Invalid input for conversion: {value}") from e

def from_units(units: int, decimals: int) -> str:
    try:
        tons = Decimal(units) / 10**decimals
        return str(tons.normalize())
    except Exception as e:
        raise ValueError(f"Invalid input for conversion: {units}") from e

def to_nano(value: str | float | int) -> int:
    return to_units(value, 9)

def from_nano(units: int) -> str:
    return from_units(units, 9)

def comment(s: str) -> Cell:
    return (
        begin_cell()
        .store_uint(0, 32)
        .store_snake_string(s)
        .end_cell()
    )
