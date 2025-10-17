from datetime import datetime
from typing import Any

from pydantic import BaseModel, GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema


def convert_datetime_to_iso8601_with_z_suffix(dt: datetime) -> str:
    """Convert provided datetime to an ISO 8601 UTC time string

    Parameters
    ----------
    dt: Datetime containing the date time to convert

    Returns
    -------
    A str containing the ISO 8601 UTC formatted time string
    """
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


class FormatBaseModel(BaseModel):
    """A Pydantic BaseModel used for any required formatting of keys and values"""

    class Config:
        # conversion for datetime to datetime string
        json_encoders = {datetime: convert_datetime_to_iso8601_with_z_suffix}

    def model_dump(self):
        """Override the default model_dump method to always exclude None values"""
        return super().model_dump(exclude_none=True)

    def model_dump_json(self):
        """Override the default model_dump_json method to always exclude None values"""
        return super().model_dump_json(exclude_none=True)


class CustomDT(datetime):
    """A convenience class used to strip all datetime objects of timezone information,
    required to bypass Pydantic's automatic inclusion of timezone when parsing JSON
    strings.
    """

    @classmethod
    def validate_no_tz(cls, v: Any, info: core_schema.ValidationInfo) -> Any:
        if isinstance(v, str):
            return datetime.strptime(v, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=None)
        else:
            return v.replace(tzinfo=None)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.with_info_plain_validator_function(
            function=cls.validate_no_tz
        )
