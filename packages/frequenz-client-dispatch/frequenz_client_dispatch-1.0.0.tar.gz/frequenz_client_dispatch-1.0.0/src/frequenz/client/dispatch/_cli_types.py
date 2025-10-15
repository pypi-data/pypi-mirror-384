# License: All rights reserved
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Types for the CLI client."""

import json
from datetime import datetime, timedelta, timezone
from itertools import chain
from typing import Any, Literal, cast

import asyncclick as click
import parsedatetime  # type: ignore
from tzlocal import get_localzone

from frequenz.client.common.microgrid.components import ComponentCategory
from frequenz.client.common.microgrid.electrical_components import (
    ElectricalComponentCategory,
)
from frequenz.client.dispatch.types import (
    BatteryType,
    EvChargerType,
    InverterType,
    TargetCategories,
    TargetComponents,
    TargetIds,
)

# Disable a false positive from pylint
# pylint: disable=inconsistent-return-statements


class FuzzyDateTime(click.ParamType):
    """Try to parse a string as a datetime.

    The parser is very permissive and can handle a wide range of time expressions.
    """

    name = "FuzzyDateTime"

    def __init__(self) -> None:
        """Initialize the parser."""
        self.cal: Any = parsedatetime.Calendar()
        self.local_tz = get_localzone()

    def convert(
        self, value: Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> datetime | Literal["NOW"] | None:
        """Convert the value to a datetime object or the string "NOW"."""
        if isinstance(value, datetime):
            return value

        try:
            if value.upper() == "NOW":
                return "NOW"

            parsed_dt, parse_status = self.cal.parseDT(value, tzinfo=self.local_tz)
            if parse_status == 0:
                self.fail(f"Invalid time expression: {value}", param, ctx)

            # Check if only a date was provided (no time component)
            # parsedatetime returns status 1 for date-only parsing
            if parse_status == 1:
                # Set time to midnight in UTC for date-only inputs
                # First convert to UTC, then set time to midnight
                parsed_dt = parsed_dt.astimezone(timezone.utc).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )

            return cast(datetime, parsed_dt.astimezone(timezone.utc))
        except Exception as e:  # pylint: disable=broad-except
            self.fail(
                f"Could not parse time expression: '{value}'. Error: {e}", param, ctx
            )


class FuzzyTimeDelta(click.ParamType):
    """Try to parse a string as a timedelta.

    Uses parsedatetime and tries to parse it as relative datetime first that
    is then converted to a timedelta.

    If that fails, try to interpret the string as a number of seconds.

    Only returns timedeltas rounded to the nearest second.
    """

    name = "FuzzyTimeDelta"

    def __init__(self) -> None:
        """Initialize the parser."""
        self.cal: Any = parsedatetime.Calendar()
        self.local_tz = get_localzone()

    def convert(
        self, value: Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> timedelta:
        """Convert the value to a timedelta object."""
        if isinstance(value, timedelta):
            return value

        try:
            parsed_dt, parse_status = self.cal.parseDT(value, tzinfo=self.local_tz)
            if parse_status == 0:
                self.fail(f"Invalid time expression: {value}", param, ctx)

            td = cast(timedelta, parsed_dt - datetime.now(self.local_tz))

            # Round to the nearest second
            return timedelta(seconds=round(td.total_seconds()))
        except click.ClickException as e:
            try:
                return timedelta(seconds=int(value))
            except ValueError:
                self.fail(
                    f"Could not parse time expression: '{value}'. Error: {e}",
                    param,
                    ctx,
                )


class FuzzyIntRange(click.ParamType):
    """Try to parse a string as a simple integer range.

    Possible formats:
    - "1"
    - "1,2,3"
    - "1-3"
    - "1..3"
    """

    name = "int_range"

    def convert(
        self, value: Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> list[int]:
        """Convert the value to a list of integers."""
        if isinstance(value, list):
            return value

        try:
            if "," in value:
                return [int(id) for id in value.split(",")]

            if "-" in value:
                start, end = [int(id) for id in value.split("-")]
                return list(range(start, end + 1))

            if ".." in value:
                start, end = [int(id) for id in value.split("..")]
                return list(range(start, end + 1))

            return [int(value)]
        except ValueError:
            self.fail(f"Invalid integer range: {value}", param, ctx)


class TargetComponentParamType(click.ParamType):
    """Click parameter type for targets."""

    name = "target"

    def convert(
        self, value: Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> TargetIds | TargetCategories:
        """Convert the input value into a list of ComponentCategory or IDs.

        Args:
            value: The input value.
            param: The Click parameter object.
            ctx: The Click context object.

        Returns:
            A list of targets, either as component IDs or component categories.
        """
        if isinstance(value, TargetComponents):
            return value

        values = value.split(",")

        if len(values) == 0:
            self.fail("Empty target list", param, ctx)

        error: Exception | None = None
        # Attempt to parse component ids
        try:
            return TargetIds(*[int(id) for id in values])
        except ValueError as e:
            error = e

        def enum_from_str(
            name: str,
        ) -> (
            InverterType
            | BatteryType
            | EvChargerType
            | ElectricalComponentCategory
            | ComponentCategory
        ):
            """Convert a string to an enum member."""
            name = name.strip().upper()
            if name in ElectricalComponentCategory.__members__:
                return ElectricalComponentCategory[name]
            if name in ComponentCategory.__members__:
                return ComponentCategory[name]
            if name in InverterType.__members__:
                return InverterType[name]
            if name in BatteryType.__members__:
                return BatteryType[name]
            if name in EvChargerType.__members__:
                return EvChargerType[name]
            raise KeyError(f"Invalid target specification: {name}")

        # Attempt to parse as component categories, trim whitespace
        try:
            return TargetCategories(*[enum_from_str(cat) for cat in values])
        except KeyError as e:
            error = e

        types_str = ", ".join(
            [f"{type.name}" for type in chain(BatteryType, InverterType, EvChargerType)]
        )

        self.fail(
            f'Invalid component category list or ID list: "{value}".\n'
            f'Error: "{error}"\n\n'
            "Valid formats:\n"
            "- 1,2,3 # A list of component IDs\n"
            "- METER,INVERTER # A list of component categories\n"
            "- NA_ION,SOLAR # A list of component category types (category is derived)\n"
            "Valid categories:\n"
            f"{', '.join([cat.name for cat in ElectricalComponentCategory])}\n"
            "Valid types:\n"
            f"{types_str}\n",
            param,
            ctx,
        )


class JsonDictParamType(click.ParamType):
    """Click parameter type for JSON strings."""

    name = "json"

    def convert(
        self, value: Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> dict[str, Any]:
        """Convert the input value into a dictionary.

        Args:
            value: The input value (string).
            param: The Click parameter object.
            ctx: The Click context object.

        Returns:
            A dictionary parsed from the input JSON string.
        """
        if isinstance(value, dict):  # Already a dictionary
            return value

        try:
            if not value.startswith("{"):
                value = "{" + value
            if not value.endswith("}"):
                value = value + "}"

            return cast(dict[str, Any], json.loads(value))

        except ValueError as e:
            self.fail(f"Invalid JSON string: {value}. Error: {e}", param, ctx)
