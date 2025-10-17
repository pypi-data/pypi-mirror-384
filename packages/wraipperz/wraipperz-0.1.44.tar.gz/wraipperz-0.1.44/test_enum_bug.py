"""Test case to reproduce the enum bug in pydantic_to_yaml_example"""

from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from wraipperz.parsing.yaml_utils import pydantic_to_yaml_example


class AvailabilityStatus(str, Enum):
    AVAILABLE = "available"
    SECOND_KEEP = "secondKeep"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class Availability(BaseModel):
    # Use snake_case as primary with camelCase aliases for backend
    start_date: date = Field(
        json_schema_extra={
            "example": "2025-08-15",
            "comment": "Start date of availability period",
            "is_attribute": True,
            "field_name": "startDate",
        },
    )
    end_date: date = Field(
        json_schema_extra={
            "example": "2025-08-20",
            "comment": "End date of availability period",
            "is_attribute": True,
            "field_name": "endDate",
        },
    )
    availability: Optional[AvailabilityStatus] = Field(
        default=None,
        json_schema_extra={
            "example": AvailabilityStatus.AVAILABLE.value,
            "options": [e.value for e in AvailabilityStatus],
            "is_attribute": True,
        },
    )


class Actor(BaseModel):
    name: str = Field(json_schema_extra={"example": "John Doe"})

    # Using nested Availability objects in the example
    availability: List[Availability] = Field(
        default=[],
        json_schema_extra={
            "example": [
                Availability(
                    start_date=date(2025, 8, 15),
                    end_date=date(2025, 8, 20),
                    availability=AvailabilityStatus.AVAILABLE.value,  # Passing the value
                )
            ],
            "comment": "Availability of the actor typically found in the email body",
        },
    )


class Actors(BaseModel):
    actors: List[Actor] = Field(
        default_factory=list, json_schema_extra={"comment": "List of actors"}
    )


def test_enum_bug():
    """Test that enum values are properly serialized in nested Pydantic models"""

    # Generate the template
    template = pydantic_to_yaml_example(Actors)

    print("Generated YAML Template:")
    print(template)
    print("\n" + "=" * 50 + "\n")

    # Check if the bug exists
    if '"AvailabilityStatus.AVAILABLE"' in template:
        print("❌ BUG FOUND: Enum is output as representation instead of value")
        print("   Found: 'AvailabilityStatus.AVAILABLE'")
        print("   Expected: 'available'")
        return False
    elif '"available"' in template:
        print("✅ CORRECT: Enum value is properly serialized")
        return True
    else:
        print("⚠️  UNEXPECTED: Neither enum representation nor value found in output")
        return False


if __name__ == "__main__":
    success = test_enum_bug()

    # Also test a simpler case with direct enum in example
    print("\n" + "=" * 50)
    print("Testing simpler case with direct enum value:\n")

    class SimpleModel(BaseModel):
        status: AvailabilityStatus = Field(
            json_schema_extra={
                "example": AvailabilityStatus.AVAILABLE.value,
                "options": [e.value for e in AvailabilityStatus],
            }
        )

    simple_template = pydantic_to_yaml_example(SimpleModel)
    print("Simple model template:")
    print(simple_template)

    if not success:
        exit(1)
