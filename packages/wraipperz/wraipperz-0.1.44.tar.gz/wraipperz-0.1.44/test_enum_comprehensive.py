"""Comprehensive test for enum serialization in pydantic_to_yaml_example"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from wraipperz.parsing.yaml_utils import pydantic_to_yaml_example


class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class Priority(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class SimpleEnum(Enum):
    OPTION_A = "option_a"
    OPTION_B = "option_b"


def test_direct_enum_object():
    """Test when enum object (not .value) is passed directly"""

    class TestModel(BaseModel):
        status: Status = Field(
            json_schema_extra={
                "example": Status.ACTIVE,  # Passing enum object, not .value
                "comment": "Testing direct enum object",
            }
        )

    result = pydantic_to_yaml_example(TestModel)
    print("Test 1: Direct enum object (not .value)")
    print(result)
    print()

    if "Status.ACTIVE" in result:
        print("❌ BUG: Enum representation found instead of value")
        return False
    elif '"active"' in result:
        print("✅ OK: Enum value properly serialized")
        return True
    else:
        print("⚠️  Unexpected output")
        return False


def test_nested_model_with_enum_object():
    """Test nested model instance with enum object"""

    class Inner(BaseModel):
        status: Status = Field(json_schema_extra={"example": "active"})

    class Outer(BaseModel):
        inner: Inner = Field(
            json_schema_extra={
                "example": Inner(status=Status.ACTIVE),  # Enum object in nested model
                "comment": "Nested model with enum",
            }
        )

    result = pydantic_to_yaml_example(Outer)
    print("Test 2: Nested model with enum object")
    print(result)
    print()

    if "Status.ACTIVE" in result:
        print("❌ BUG: Enum representation found in nested model")
        return False
    elif '"active"' in result:
        print("✅ OK: Enum value properly serialized in nested model")
        return True
    else:
        print("⚠️  Unexpected output")
        return False


def test_list_of_models_with_enum():
    """Test list of model instances with enum fields"""

    class Item(BaseModel):
        name: str
        status: Status
        priority: Optional[Priority] = None

    class Container(BaseModel):
        items: List[Item] = Field(
            json_schema_extra={
                "example": [
                    Item(name="Item1", status=Status.ACTIVE, priority=Priority.HIGH),
                    Item(name="Item2", status=Status.INACTIVE),
                ],
                "comment": "List of items with enum fields",
            }
        )

    result = pydantic_to_yaml_example(Container)
    print("Test 3: List of models with enum fields")
    print(result)
    print()

    has_bug = False
    if "Status.ACTIVE" in result or "Status.INACTIVE" in result:
        print("❌ BUG: Status enum representation found")
        has_bug = True
    if "Priority.HIGH" in result:
        print("❌ BUG: Priority enum representation found")
        has_bug = True

    if not has_bug:
        if '"active"' in result and '"inactive"' in result:
            print("✅ OK: Enum values properly serialized")
            return True
        else:
            print("⚠️  Expected values not found")
            return False
    return False


def test_dict_with_enum_values():
    """Test dictionary containing enum values"""

    class Config(BaseModel):
        settings: Dict[str, Status] = Field(
            json_schema_extra={
                "example": {
                    "server1": Status.ACTIVE,
                    "server2": Status.INACTIVE,
                },
                "comment": "Server status mapping",
            }
        )

    result = pydantic_to_yaml_example(Config)
    print("Test 4: Dictionary with enum values")
    print(result)
    print()

    if "Status.ACTIVE" in result or "Status.INACTIVE" in result:
        print("❌ BUG: Enum representation found in dict values")
        return False
    elif '"active"' in result and '"inactive"' in result:
        print("✅ OK: Enum values in dict properly serialized")
        return True
    else:
        print("⚠️  Unexpected output")
        return False


def test_non_string_enum():
    """Test non-string enum (int enum)"""

    class Task(BaseModel):
        priority: Priority = Field(
            json_schema_extra={
                "example": Priority.HIGH,
                "comment": "Task priority",
                "options": [e.value for e in Priority],
            }
        )

    result = pydantic_to_yaml_example(Task)
    print("Test 5: Non-string (int) enum")
    print(result)
    print()

    if "Priority.HIGH" in result:
        print("❌ BUG: Int enum representation found")
        return False
    elif "3" in result or "priority: 3" in result:
        print("✅ OK: Int enum value properly serialized")
        return True
    else:
        print("⚠️  Unexpected output")
        return False


def test_simple_enum_without_base():
    """Test simple enum without str/int base class"""

    class Model(BaseModel):
        option: SimpleEnum = Field(
            json_schema_extra={
                "example": SimpleEnum.OPTION_A,
                "comment": "Simple enum test",
            }
        )

    result = pydantic_to_yaml_example(Model)
    print("Test 6: Simple enum without str/int base")
    print(result)
    print()

    if "SimpleEnum.OPTION_A" in result:
        print("❌ BUG: Simple enum representation found")
        return False
    elif '"option_a"' in result:
        print("✅ OK: Simple enum value properly serialized")
        return True
    else:
        print("⚠️  Unexpected output")
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("=" * 60)
    print("COMPREHENSIVE ENUM SERIALIZATION TESTS")
    print("=" * 60 + "\n")

    tests = [
        ("Direct enum object", test_direct_enum_object),
        ("Nested model with enum", test_nested_model_with_enum_object),
        ("List of models with enums", test_list_of_models_with_enum),
        ("Dict with enum values", test_dict_with_enum_values),
        ("Non-string (int) enum", test_non_string_enum),
        ("Simple enum without base", test_simple_enum_without_base),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n{'=' * 40}")
        print(f"Running: {name}")
        print("=" * 40)
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append((name, False))
        print()

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {name}")
        if not success:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED - BUG MAY BE PRESENT")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        exit(1)
