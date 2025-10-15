# 🐍🏗️ pyvider.cty

⚠️ **PREVIEW RELEASE** ⚠️

This is a preview release of pyvider.cty. While the core functionality is complete and well-tested, this release is intended for early adopters and feedback gathering. Please report any issues or suggestions.

## Overview

`pyvider.cty` is a pure-Python implementation of the [go-cty](https://github.com/zclconf/go-cty) type system, providing strong type validation and serialization capabilities for configuration data. It's designed to work seamlessly with Terraform providers and other HashiCorp ecosystem tools.

## Features

- 🎯 **Complete Type System**: Primitives, collections, and structural types.
- 🔄 **Cross-Language Compatibility**: Interoperates with go-cty via JSON and MessagePack.
- 🛡️ **Type Safety**: Strong validation at value creation.
- 🏷️ **Marks System**: Attach metadata without modifying values.
- 🗺️ **Path Navigation**: Type-safe access to nested data.
- ⚡ **Full Standard Library**: A comprehensive suite of functions for data manipulation.

## Installation

```bash
uv add pyvider-cty
```

## Quick Start

```python
from pyvider.cty import CtyObject, CtyString, CtyNumber, CtyList
from pyvider.cty.exceptions import CtyValidationError

# 1. Define a type schema for a user profile.
# 'age' is an optional attribute.
user_type = CtyObject(
    attribute_types={
        "name": CtyString(),
        "age": CtyNumber(),
        "hobbies": CtyList(element_type=CtyString())
    },
    optional_attributes={"age"}
)

# 2. Create raw Python data that matches the schema.
user_data = {
    "name": "Alice",
    "hobbies": ["reading", "hiking"]
}

# 3. Validate the data. This returns an immutable CtyValue.
try:
    user_val = user_type.validate(user_data)
    print("✅ Validation successful!")

    # 4. Access data from the CtyValue.
    # Accessing attributes returns another CtyValue. Use .raw_value to get the Python type.
    print(f"Name: {user_val['name'].raw_value}")

    # The optional 'age' attribute is present but is a null CtyValue.
    print(f"Age: {user_val['age'].raw_value} (Is Null: {user_val['age'].is_null})")

    print("Hobbies:")
    for hobby_val in user_val['hobbies']:
        print(f"- {hobby_val.raw_value}")

except CtyValidationError as e:
    print(f"❌ Validation failed: {e}")
```

## Documentation

The complete user guide can be found in the `docs/` directory, starting with the [index](docs/index.md).

## Known Limitations

- **Python 3.13+ Required**: Due to advanced type features used.
- **Performance**: The library is not yet optimized for performance-critical applications involving very large or deeply nested data structures. Performance is reasonable for typical use cases.

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.
# CI Test
