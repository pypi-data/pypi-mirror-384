import json
import re
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union

from starlette.responses import JSONResponse


class BaseInput(ABC):
    """Abstract base class for all input types."""

    def __init__(
        self,
        title: str,
        description: str,
        type: str,
        placeholder: Optional[str] = None,
        default: Optional[Any] = None,
        required: bool = True,
    ):
        self.title = title
        self.description = description
        self.type = type
        self.placeholder = placeholder
        self.default = default
        self.required = required

    def schema(self) -> dict:
        """
        Returns the dictionary representation of the input's configuration.
        """
        return self.__dict__.copy()

    def get_schema(self, request):
        return JSONResponse(self.schema())

    @abstractmethod
    def validate(self, value: Any):
        """
        Validates the given value against the input's rules.
        Raises TypeError or ValueError on failure.
        """
        if self.required and value is None:
            raise ValueError(
                f"'{self.title}' is a required field and cannot be None."
            )

    @staticmethod
    def reconstruct(fields: dict):
        """
        Factory method to reconstruct an Input object from its schema
        dictionary. This acts as a dispatcher.
        """
        input_type = fields.get("type")
        type_to_class_map = {
            "string": InputString,
            "number": InputNumber,
            "integer": InputInteger,
            "multiselect": InputMultiselect,
            "radio": InputRadio,
            "file": InputFile,
            "group": InputGroup,
            "list": InputList,
            "factsheet": InputFactSheet,
        }

        target_class = type_to_class_map.get(input_type)

        if not target_class:
            raise ValueError(
                f"Unknown input type for reconstruction: '{input_type}'"
            )
        return target_class.reconstruct(fields)


class InputString(BaseInput):
    def __init__(
        self,
        title: str,
        description: str,
        min_len: int = 0,
        max_len: Union[int, None] = None,
        regex: Optional[str] = None,
        upper: bool = False,
        lower: bool = False,
        multi_line: bool = True,
        placeholder: Optional[str] = None,
        default: Optional[str] = None,
        required: bool = True,
    ):
        super().__init__(
            title, description, "string", placeholder, default, required
        )
        self.min_len = min_len
        self.max_len = max_len
        self.regex = regex
        self.upper = upper
        self.lower = lower
        self.multi_line = multi_line

    def validate(self, value: str):
        super().validate(value)
        if value is None:
            return
        if not isinstance(value, str):
            raise TypeError(
                f"'{self.title}' expects a string, but received {
                    type(value).__name__
                }."
            )
        if self.max_len:
            if not (self.min_len <= len(value) <= self.max_len):
                raise ValueError(
                    f"'{self.title}' must be between {self.min_len} and {
                        self.max_len
                    } characters long."
                )
        if self.regex and not re.match(self.regex, value):
            raise ValueError(
                f"'{self.title}' does not match the required pattern."
            )
        if self.upper and not value.isupper():
            raise ValueError(f"'{self.title}' must be in uppercase.")
        if self.lower and not value.islower():
            raise ValueError(f"'{self.title}' must be in lowercase.")

    @staticmethod
    def reconstruct(fields: dict):
        init_args = fields.copy()
        init_args.pop("type", None)
        return InputString(**init_args)


class InputNumber(BaseInput):
    def __init__(
        self,
        title: str,
        description: str,
        min_val: Union[int, float, None] = None,
        max_val: Union[int, float, None] = None,
        placeholder: Optional[str] = None,
        default: Optional[Union[int, float]] = None,
        required: bool = True,
    ):
        super().__init__(
            title, description, "number", placeholder, default, required
        )
        self.min_val = min_val
        self.max_val = max_val

    def validate(self, value: Union[int, float]):
        super().validate(value)
        if value is None:
            return
        if not isinstance(value, (int, float)):
            raise TypeError(
                f"'{self.title}' expects a number, but received {
                    type(value).__name__
                }."
            )
        if self.min_val:
            if not self.min_val <= value:
                raise ValueError(
                    f"'{self.title}' must be greater than or equal to {
                        self.min_val
                    }."
                )
        if self.max_val:
            if not value <= self.max_val:
                raise ValueError(
                    f"'{self.title}' must be smaller or equal to {
                        self.min_val
                    } ."
                )

    @staticmethod
    def reconstruct(fields: dict):
        init_args = fields.copy()
        init_args.pop("type", None)
        return InputNumber(**init_args)


class InputInteger(BaseInput):
    def __init__(
        self,
        title: str,
        description: str,
        min_val: Union[int, None] = None,
        max_val: Union[int, None] = None,
        placeholder: Optional[str] = None,
        default: Optional[int] = None,
        required: bool = True,
    ):
        super().__init__(
            title, description, "integer", placeholder, default, required
        )
        self.min_val = min_val
        self.max_val = max_val

    def validate(self, value: int):
        super().validate(value)
        if value is None:
            return
        if not isinstance(value, int):
            raise TypeError(
                f"'{self.title}' expects an integer, but received {
                    type(value).__name__
                }."
            )
        if self.min_val:
            if not self.min_val <= value:
                raise ValueError(
                    f"'{self.title}' must be greater tha or equal to {
                        self.min_val
                    }."
                )
        if self.max_val:
            if not value <= self.max_val:
                raise ValueError(
                    f"'{self.title}' must be smaller than or equal to {
                        self.min_val
                    }."
                )

    @staticmethod
    def reconstruct(fields: dict):
        init_args = fields.copy()
        init_args.pop("type", None)
        return InputInteger(**init_args)


class InputMultiselect(BaseInput):
    def __init__(
        self,
        title: str,
        description: str,
        values: List[Union[str, int, float]],
        min_selections: int = 0,
        max_selections: Union[int, None] = None,
        placeholder: Optional[str] = None,
        required: bool = True,
        **args,  # Needed as Multiselect does not support a default value
    ):
        super().__init__(
            title, description, "multiselect", placeholder, None, required
        )
        self.values = values
        self.min_selections = min_selections
        self.max_selections = max_selections
        if not self.max_selections:
            self.max_selections = len(values)

    def validate(self, value: list):
        super().validate(value)
        if value is None:
            return
        if not isinstance(value, list):
            raise TypeError(
                f"'{self.title}' expects a list of selections, but received {
                    type(value).__name__
                }."
            )

        if not (self.min_selections <= len(value) <= self.max_selections):
            raise ValueError(
                f"'{self.title}' must have between {self.min_selections} and {
                    self.max_selections
                } selections."
            )
        if not set(value).issubset(set(self.values)):
            raise ValueError(
                f"'{
                    self.title
                }' contains invalid options. Allowed options are: {
                    self.values
                }."
            )

    @staticmethod
    def reconstruct(fields: dict):
        init_args = fields.copy()
        print(init_args)
        init_args.pop("type", None)
        return InputMultiselect(**init_args)


class InputRadio(BaseInput):
    def __init__(
        self,
        title: str,
        description: str,
        values: List[Union[str, int, float]],
        placeholder: Optional[str] = None,
        default: Optional[Union[str, int, float]] = None,
        required: bool = True,
    ):
        super().__init__(
            title, description, "radio", placeholder, default, required
        )
        self.values = values

    def validate(self, value: Union[str, int, float]):
        super().validate(value)
        if value is None:
            return
        if value not in self.values:
            raise ValueError(
                f"'{self.title}' has an invalid value. Allowed options are: {
                    self.values
                }."
            )

    @staticmethod
    def reconstruct(fields: dict):
        init_args = fields.copy()
        init_args.pop("type", None)
        return InputRadio(**init_args)


class InputFile(BaseInput):
    def __init__(
        self,
        title: str,
        description: str,
        filetypes: List[str],
        placeholder=None,
        default=None,
        required: bool = True,
    ):
        super().__init__(title, description, "file", None, None, required)
        self.filetypes = [
            ft if ft.startswith(".") else f".{ft}" for ft in filetypes
        ]

    def validate(self, value: str):
        super().validate(value)
        if value is None:
            return
        if not isinstance(value, str):
            raise TypeError(
                f"'{self.title}' expects a filename string, but received {
                    type(value).__name__
                }."
            )
        if not value.lower().endswith(tuple(self.filetypes)):
            raise ValueError(
                f"'{self.title}' must be one of the following file types: {
                    self.filetypes
                }."
            )

    @staticmethod
    def reconstruct(fields: dict):
        init_args = fields.copy()
        init_args.pop("type", None)

        return InputFile(**init_args)


class InputFactSheet(BaseInput):
    def __init__(
        self,
        title: str,
        description: str,
        data_groups: List[int],
        placeholder=None,
        default=None,
        required: bool = True,
    ):
        super().__init__(title, description, "factsheet", None, None, required)
        self.data_groups = data_groups

    def validate(self, value: str):
        super().validate(value)
        if value is None:
            return
        if not isinstance(value, dict):
            raise TypeError(
                f"'{
                    self.title
                }' expects a factsheet in dict format, but received {
                    type(value).__name__
                }."
            )
        if value["data_group_id"] not in self.data_groups and self.data_groups:
            raise ValueError(
                f"'{
                    self.title
                }' must be from one of the following Data Groups: {
                    self.data_groups
                }."
            )

    @staticmethod
    def reconstruct(fields: dict):
        init_args = fields.copy()
        init_args.pop("type", None)
        return InputFactSheet(**init_args)


class InputGroup(BaseInput):
    def __init__(
        self,
        title: str,
        description: str,
        values: List[BaseInput],
        placeholder=None,
        default=None,
        required: bool = True,
    ):
        super().__init__(title, description, "group", None, None, required)
        self.values = values

    def schema(self) -> dict:
        schema_dict = super().schema()
        schema_dict["values"] = [child.schema() for child in self.values]
        return schema_dict

    def validate(self, value: dict):
        super().validate(value)
        if value is None:
            return
        if not isinstance(value, dict):
            raise TypeError(
                f"'{self.title}' expects a dictionary, but received {
                    type(value).__name__
                }."
            )
        child_inputs = {child.title: child for child in self.values}
        for title, child_input in child_inputs.items():
            child_input.validate(value.get(title))

    @staticmethod
    def reconstruct(fields: dict):
        init_args = fields.copy()
        init_args.pop("type", None)
        # Recursively reconstruct child objects
        child_schemas = init_args.get("values", [])
        init_args["values"] = [
            BaseInput.reconstruct(child) for child in child_schemas
        ]
        return InputGroup(**init_args)


class InputList(BaseInput):
    def __init__(
        self,
        title: str,
        description: str,
        obj: BaseInput,
        min_items: int = 0,
        max_items: Union[int, None] = None,
        placeholder=None,
        default=None,
        required: bool = True,
    ):
        super().__init__(title, description, "list", None, None, required)
        self.min_items = min_items
        self.max_items = max_items
        self.object = obj

    def schema(self) -> dict:
        schema_dict = super().schema()
        schema_dict["object"] = self.object.schema()
        return schema_dict

    def validate(self, value: list):
        super().validate(value)
        if value is None:
            return
        if not isinstance(value, list):
            raise TypeError(
                f"'{self.title}' expects a list, but received {
                    type(value).__name__
                }."
            )
        if not (self.min_items <= len(value)):
            raise ValueError(
                f"'{self.title}' must contain minimum {self.min_items} items."
            )
        if self.max_items:
            if not (len(value) <= self.max_items):
                raise ValueError(
                    f"'{self.title}' must contain no more than {
                        self.min_items
                    } items."
                )

        for i, item in enumerate(value):
            try:
                self.object.validate(item)
            except (ValueError, TypeError) as e:
                raise type(e)(
                    f"Error in '{self.title}' at index {i}: {e}"
                ) from e

    @staticmethod
    def reconstruct(fields: dict):
        init_args = fields.copy()
        init_args.pop("type", None)

        if "object" in init_args:
            obj_schema = init_args.pop("object")
            init_args["obj"] = BaseInput.reconstruct(obj_schema)
        return InputList(**init_args)


def save_schema_to_json(filename: str, schema: dict):
    """Saves a schema dictionary to a JSON file."""
    with open(filename, "w") as f:
        json.dump(schema, f, indent=4)
    print(f"✅ Successfully saved schema to {filename}")


def create_simple_schema() -> BaseInput:
    """Creates a schema using string, number, and integer types."""
    return InputGroup(
        title="Simple Data Form",
        description=(
            "Basic fields demonstrating string,number, and integer validation."
        ),
        values=[
            InputString(
                title="Username",
                description="Must be between 5-15 alphanumeric characters.",
                min_len=5,
                max_len=15,
                regex=r"^[a-zA-Z0-9]+$",
                placeholder="e.g., janedoe99",
                default="guest",
            ),
            InputNumber(
                title="Price",
                description=(
                    "The product price (float allowed). Must be positive."
                ),
                min_val=0.01,
                placeholder="e.g., 49.99",
                required=True,
            ),
            InputInteger(
                title="Quantity",
                description="The number of items to order. Max is 100.",
                min_val=1,
                max_val=100,
                default=1,
            ),
            InputString(
                title="API Key (Uppercase)",
                description="A 20-character key that must be all uppercase.",
                min_len=20,
                max_len=20,
                upper=True,
                required=False,
            ),
        ],
    )


def create_middle_schema() -> BaseInput:
    """Creates a schema including radio, multiselect, and factsheet."""
    return InputGroup(
        title="Intermediate Data Form",
        description="Includes choice and file inputs.",
        values=[
            # String/Number/Integer from simple
            InputString(
                title="Full Name",
                description="Your first and last name.",
                placeholder="e.g., John Smith",
                required=True,
            ),
            InputInteger(
                title="Years Experience",
                description="Must be a non-negative integer.",
                min_val=0,
                default=0,
            ),
            # New types: Radio, Multiselect, FactSheet
            InputRadio(
                title="Subscription Tier",
                description="Choose your subscription level.",
                values=["Basic", "Standard", "Premium"],
                default="Standard",
            ),
            InputMultiselect(
                title="Preferred Contact Methods",
                description="Select 1 to 3 ways we can reach you.",
                values=["Email", "Phone", "SMS", "Post"],
                min_selections=1,
                max_selections=3,
            ),
            InputFactSheet(
                title="Source Data Factsheet",
                description=(
                    "Link to a factsheet from an authorized data group."
                ),
                data_groups=[101, 102],
                required=True,
            ),
            InputFile(
                title="Profile Picture",
                description="Upload an image file.",
                # Testing extension normalization
                filetypes=[".png", ".jpeg", "gif"],
                required=False,
            ),
        ],
    )


def create_advanced_schema() -> BaseInput:
    """Creates a schema with nested InputGroup and InputList."""
    # Define a reusable child group for a list
    user_detail_group = InputGroup(
        title="Contact Detail",
        description="A single contact entry.",
        values=[
            InputString(
                title="Email",
                description="The user's email address.",
                regex=r"[^@]+@[^@]+\.[^@]+",
            ),
            InputNumber(
                title="Hourly Rate",
                description="The person's rate, must be > 10.",
                min_val=10.01,
                required=False,
            ),
            InputRadio(
                title="Status",
                description="Current employment status.",
                values=["Active", "Inactive"],
                default="Active",
            ),
        ],
    )

    return InputGroup(
        title="Advanced Application Form",
        description="A form demonstrating complex nested structures.",
        values=[
            InputString(
                title="Company Name",
                description="The name of the organization.",
                min_len=2,
            ),
            InputFactSheet(
                title="Company's Financial Data",
                description="Required financial factsheet.",
                data_groups=[200],
            ),
            # Nested Group
            InputGroup(
                title="Administrative Contact",
                description="Key person's details.",
                values=[
                    InputString(
                        title="Name", description="Contact name.", min_len=3
                    ),
                    InputString(
                        title="Phone",
                        description="Contact phone.",
                        regex=r"^\d{10}$",
                    ),
                ],
            ),
            # List of complex objects
            InputList(
                title="Team Members",
                description="Add 1 to 5 team members with their details.",
                obj=user_detail_group,  # Uses the reusable group defined above
                min_items=1,
                max_items=5,
            ),
            InputMultiselect(
                title="Regions",
                description=(
                    "Select all applicable operational regions (up to all 3)."
                ),
                values=["North America", "Europe", "Asia"],
                min_selections=0,
                max_selections=3,
            ),
        ],
    )


simple_data = {
    "Username": "validuser1",
    "Price": 125.50,
    "Quantity": 5,
    "API Key (Uppercase)": "ABCDEFGHIJKLMNOPQRST",
}

middle_data = {
    "Full Name": "Alice Tester",
    "Years Experience": 3,
    "Subscription Tier": "Premium",
    "Preferred Contact Methods": ["Email", "Phone"],
    "Source Data Factsheet": {"id": "FS-1234", "data_group_id": 102},
    "Profile Picture": "avatar.PNG",
}

advanced_data = {
    "Company Name": "Tech Corp",
    "Company's Financial Data": {"id": "FIN-456", "data_group_id": 200},
    "Administrative Contact": {"Name": "Bob", "Phone": "1234567890"},
    "Team Members": [
        {
            "Email": "jane@example.com",
            "Hourly Rate": 55.50,
            "Status": "Active",
        },
        {
            "Email": "ceo@bigcorp.com",
            "Hourly Rate": 100.00,
            "Status": "Inactive",
        },
    ],
    "Regions": ["Europe"],
}

# --- Validation Logic ---


def test_validation(form_generator, data: dict, name: str):
    """
    Generates the form, reconstructs it from schema, and validates the data.
    """
    print(f"\n--- Testing {name} Validation ---")
    original_form = form_generator()
    original_schema = original_form.schema()

    # 1. Reconstruct from schema (to test reconstruction integrity)
    reconstructed_form = BaseInput.reconstruct(original_schema)

    # 2. Validate the data
    try:
        reconstructed_form.validate(data)
        print(f"✅ Data for **{name}** passed validation.")
    except Exception as e:
        print(f"❌ Data for **{name}** FAILED validation.")
        print(f"Error: {e}")
        # Optionally, print the failing data for debugging
        # pprint(data)

    # 3. Optional: Test a deliberate failure (e.g., Simple - bad price)
    if name == "Simple":
        bad_data = data.copy()
        bad_data["Price"] = -10.0  # Fails min_val=0.01
        try:
            reconstructed_form.validate(bad_data)
            print("❌ Failure test unexpectedly PASSED.")
        except ValueError as e:
            print(
                f"✅ Failure test passed: Caught expected error: {e.args[0]}"
            )


if __name__ == "__main__":
    print("--- Generating and Saving JSON Schemas ---")

    # 1. Simple Schema
    simple_form = create_simple_schema()
    simple_schema = simple_form.schema()
    save_schema_to_json("simple.json", simple_schema)

    # 2. Middle Schema
    middle_form = create_middle_schema()
    middle_schema = middle_form.schema()
    save_schema_to_json("middle.json", middle_schema)

    # 3. Advanced Schema
    advanced_form = create_advanced_schema()
    advanced_schema = advanced_form.schema()
    save_schema_to_json("advanced.json", advanced_schema)

    print("\n--- Example Verification (Optional but Recommended) ---")
    # You can reuse the verification logic from your original script

    # Verify the Advanced Form Reconstruction
    reconstructed_advanced = BaseInput.reconstruct(advanced_schema)
    if advanced_schema == reconstructed_advanced.schema():
        print("✅ Advanced schema reconstruction verified.")
    else:
        print("❌ Advanced schema reconstruction failed.")
        # 1. Test Simple Form
    test_validation(create_simple_schema, simple_data, "Simple")

    # 2. Test Middle Form
    test_validation(create_middle_schema, middle_data, "Middle")

    # 3. Test Advanced Form
    test_validation(create_advanced_schema, advanced_data, "Advanced")
