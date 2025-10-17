User Guide
==========

This guide covers the core concepts and features of ViewText in detail.

Field Registry
--------------

The Field Registry is the foundation of ViewText. It maps field names to getter functions
that extract values from context dictionaries.

Creating a Registry
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from viewtext import BaseFieldRegistry

    registry = BaseFieldRegistry()

Registering Fields
~~~~~~~~~~~~~~~~~~

Fields are registered with a name and a callable that takes a context dictionary:

.. code-block:: python

    # Simple field getter
    registry.register("username", lambda ctx: ctx["user"]["name"])

    # More complex getter with default values
    registry.register("status", lambda ctx: ctx.get("status", "offline"))

    # Computed fields
    registry.register("full_name", lambda ctx: f"{ctx['first']} {ctx['last']}")

Checking for Fields
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    if registry.has_field("username"):
        getter = registry.get("username")
        value = getter(context)

Formatter System
----------------

Formatters transform raw values into formatted strings. ViewText includes several built-in
formatters and supports custom formatters.

Built-in Formatters
~~~~~~~~~~~~~~~~~~~

**text**

Basic text formatting with optional prefix and suffix:

.. code-block:: python

    formatter_params:
        prefix: "Value: "
        suffix: " units"

**text_uppercase**

Converts text to uppercase:

.. code-block:: text

    "hello" → "HELLO"

**number**

Format numbers with precision and separators:

.. code-block:: yaml

    formatter_params:
        decimals: 2
        thousands_sep: ","
        prefix: "$"
        suffix: " USD"

.. code-block:: text

    1234.567 → "$1,234.57 USD"

**price**

Specialized price formatting:

.. code-block:: yaml

    formatter_params:
        symbol: "$"
        symbol_position: "prefix"  # or "suffix"
        decimals: 2
        thousands_sep: ","

.. code-block:: text

    1234.50 → "$1,234.50"

**datetime**

Format timestamps and datetime objects:

.. code-block:: yaml

    formatter_params:
        format: "%Y-%m-%d %H:%M:%S"

.. code-block:: text

    1234567890 → "2009-02-13 23:31:30"

**relative_time**

Format time differences in human-readable format:

.. code-block:: yaml

    formatter_params:
        format: "short"  # or "long"

.. code-block:: text

    300 → "5m ago"  # short format
    300 → "5 minutes ago"  # long format

**template**

Combine multiple fields using a template string with Python format specifications:

.. code-block:: yaml

    formatter_params:
        template: "{symbol} - ${price:.2f} - {volume}/$"
        fields: ["symbol", "price", "volume"]

.. code-block:: text

    # With context: {"symbol": "BTC", "price": 45234.567, "volume": "1.2M"}
    "BTC - $45234.57 - 1.2M/$"

The template formatter supports:

- Nested field access via dot notation (e.g., ``current_price.usd``)
- Python format specifications (e.g., ``.2f`` for 2 decimal places)
- Multiple fields combined in a single line

Custom Formatters
~~~~~~~~~~~~~~~~~

You can register custom formatters with the FormatterRegistry:

.. code-block:: python

    from viewtext import get_formatter_registry

    def format_percentage(value, **kwargs):
        decimals = kwargs.get("decimals", 1)
        return f"{value:.{decimals}f}%"

    formatter_registry = get_formatter_registry()
    formatter_registry.register("percentage", format_percentage)

Layout Configuration
--------------------

Layouts are defined in TOML files and specify how fields map to output lines.

Basic Layout Structure
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: toml

    [layouts.my_layout]
    name = "My Layout"

    [[layouts.my_layout.lines]]
    field = "field_name"
    index = 0
    formatter = "text"

    [layouts.my_layout.lines.formatter_params]
    prefix = "Label: "

Multiple Layouts
~~~~~~~~~~~~~~~~

A single TOML file can contain multiple layouts:

.. code-block:: toml

    [layouts.compact]
    name = "Compact View"
    # ... lines ...

    [layouts.detailed]
    name = "Detailed View"
    # ... lines ...

Formatter Parameters
~~~~~~~~~~~~~~~~~~~~

Each line can have formatter-specific parameters:

.. code-block:: toml

    [[layouts.demo.lines]]
    field = "price"
    index = 0
    formatter = "price"

    [layouts.demo.lines.formatter_params]
    symbol = "$"
    decimals = 2
    thousands_sep = ","
    symbol_position = "prefix"

Global Formatter Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Define reusable formatter configurations:

.. code-block:: toml

    [formatters.usd_price]
    type = "price"
    symbol = "$"
    decimals = 2
    thousands_sep = ","

    [layouts.product]
    name = "Product Display"

    [[layouts.product.lines]]
    field = "price"
    index = 0
    formatter = "usd_price"

Layout Engine
-------------

The Layout Engine combines field registries, formatters, and layout configurations to
generate formatted output.

Creating an Engine
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from viewtext import LayoutEngine

    # Without field registry (uses context directly)
    engine = LayoutEngine()

    # With field registry
    engine = LayoutEngine(field_registry=registry)

Building Output
~~~~~~~~~~~~~~~

.. code-block:: python

    context = {
        "temp": 72.5,
        "humidity": 65,
        "city": "San Francisco"
    }

    lines = engine.build_line_str(layout, context)

    # lines is a list of strings, one per line
    for i, line in enumerate(lines):
        print(f"Line {i}: {line}")

Field Resolution
~~~~~~~~~~~~~~~~

The engine resolves fields in this order:

1. Check field registry (if provided)
2. Check context dictionary directly
3. Return None if not found

This allows mixing registered fields with direct context values.

Layout Loader
-------------

The LayoutLoader handles loading and parsing TOML configuration files.

Loading Layouts
~~~~~~~~~~~~~~~

.. code-block:: python

    from viewtext import LayoutLoader

    # Load from specific file
    loader = LayoutLoader("config/layouts.toml")

    # Load from default location (./layouts.toml)
    loader = LayoutLoader()

    # Get a specific layout
    layout = loader.get_layout("weather")

Getting Formatter Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get global formatter configuration
    params = loader.get_formatter_params("usd_price")

Error Handling
--------------

ViewText raises specific exceptions for common errors:

.. code-block:: python

    from viewtext import LayoutLoader, BaseFieldRegistry

    # FileNotFoundError
    try:
        loader = LayoutLoader("missing.toml")
        loader.load()
    except FileNotFoundError as e:
        print(f"Config file not found: {e}")

    # ValueError for unknown layout
    try:
        layout = loader.get_layout("nonexistent")
    except ValueError as e:
        print(f"Layout error: {e}")

    # ValueError for unknown field
    registry = BaseFieldRegistry()
    try:
        getter = registry.get("unknown_field")
    except ValueError as e:
        print(f"Field error: {e}")

Best Practices
--------------

1. **Separate concerns**: Keep field logic in the registry, formatting in formatters,
   and layout structure in TOML files

2. **Use meaningful names**: Choose descriptive field and layout names

3. **Provide defaults**: Use `.get()` with defaults in field getters for optional data

4. **Validate data**: Formatters should handle None and invalid values gracefully

5. **Reuse formatters**: Define global formatter configurations for consistency

6. **Test layouts**: Verify layouts with sample data before deployment

Command Line Interface
----------------------

ViewText includes a CLI for inspecting and testing layouts.

Basic Commands
~~~~~~~~~~~~~~

.. code-block:: bash

    # List all available layouts
    viewtext list

    # Show specific layout configuration
    viewtext show weather

    # Show field mappings from config
    viewtext fields

    # Show all available formatters
    viewtext formatters

    # Render a layout with mock data
    viewtext render weather

    # Show configuration info
    viewtext info

Global Config Option
~~~~~~~~~~~~~~~~~~~~

Use the ``--config`` or ``-c`` option to specify a custom configuration file:

.. code-block:: bash

    # Global option can be placed before any command
    viewtext -c examples/layouts.toml list
    viewtext --config my_layouts.toml show weather
    viewtext -c custom.toml render crypto_ticker

The default config file is ``layouts.toml`` in the current directory.

CLI Output
~~~~~~~~~~

The CLI provides rich formatted output with tables and colors:

.. code-block:: bash

    $ viewtext list

    Configuration File: layouts.toml

    ┌────────────────┬─────────────────────┬───────┐
    │ Layout Name    │ Display Name        │ Lines │
    ├────────────────┼─────────────────────┼───────┤
    │ weather        │ Weather Display     │     6 │
    │ crypto_ticker  │ Crypto Ticker       │     5 │
    └────────────────┴─────────────────────┴───────┘

    Total layouts: 2

Advanced Usage
--------------

Singleton Pattern
~~~~~~~~~~~~~~~~~

ViewText provides singleton accessors for global instances:

.. code-block:: python

    from viewtext import (
        get_layout_engine,
        get_formatter_registry,
        get_layout_loader
    )

    # These return global singleton instances
    engine = get_layout_engine(field_registry=registry)
    formatters = get_formatter_registry()
    loader = get_layout_loader("layouts.toml")

Dynamic Layouts
~~~~~~~~~~~~~~~

Build layouts dynamically from data:

.. code-block:: python

    def create_dynamic_layout(fields):
        layout = {
            "name": "Dynamic Layout",
            "lines": []
        }

        for i, field in enumerate(fields):
            layout["lines"].append({
                "field": field,
                "index": i,
                "formatter": "text"
            })

        return layout

    # Use the dynamic layout
    layout = create_dynamic_layout(["temp", "humidity", "pressure"])
    lines = engine.build_line_str(layout, context)

Context Factories
~~~~~~~~~~~~~~~~~

Create reusable context builders:

.. code-block:: python

    class WeatherContext:
        def __init__(self, api_data):
            self.data = api_data

        def to_context(self):
            return {
                "temp": self.data["main"]["temp"],
                "humidity": self.data["main"]["humidity"],
                "city": self.data["name"],
                "timestamp": self.data["dt"]
            }

    weather = WeatherContext(api_response)
    lines = engine.build_line_str(layout, weather.to_context())
