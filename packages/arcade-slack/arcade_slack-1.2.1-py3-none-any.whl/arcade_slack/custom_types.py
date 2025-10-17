from typing import NewType


class PositiveNonZeroInt(int):
    def __new__(cls, value: str | int, name: str = "value") -> "PositiveNonZeroInt":
        def validate(val: int) -> int:
            if val < 1:
                raise ValueError(f"{name} must be a positive non-zero integer, got {val}")
            return val

        try:
            value = int(value)
        except ValueError:
            raise ValueError(f"{name} must be a valid integer, got {value!r}")

        validated_value = validate(value)
        instance = super().__new__(cls, validated_value)
        return instance


SlackOffsetSecondsFromUTC = NewType("SlackOffsetSecondsFromUTC", int)  # observe it can be negative
SlackPaginationNextCursor = str | None
SlackUserFieldId = NewType("SlackUserFieldId", str)
SlackUserId = NewType("SlackUserId", str)
SlackTeamId = NewType("SlackTeamId", str)
SlackTimestampStr = NewType("SlackTimestampStr", str)
