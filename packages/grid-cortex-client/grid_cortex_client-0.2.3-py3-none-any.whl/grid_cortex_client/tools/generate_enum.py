#!/usr/bin/env python3
"""
Regenerate model_type.py from the live BaseModel registry.

This script automatically generates the ModelType enum with rich docstrings
and examples by introspecting the BaseModel registry. This ensures the enum
stays in sync with registered models while remaining static for GRID-Rake.

Usage:
    python -m grid_cortex_client.tools.generate_enum
"""

from pathlib import Path
import inspect
import importlib
import pkgutil
import sys

# Add the src directory to the path so we can import grid_cortex_client
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from grid_cortex_client.models.base_model import registry  # noqa: E402
import grid_cortex_client.models as _models  # noqa: E402

# Import every wrapper by iterating sibling modules dynamically. This avoids
# hardcoding and ensures zero manual upkeep.
for module_info in pkgutil.iter_modules(_models.__path__):  # type: ignore[attr-defined]
    name = module_info.name
    if name.startswith("__") or name in {"base_model", "model_enum"}:
        continue
    importlib.import_module(f"{_models.__name__}.{name}")

TARGET = Path(__file__).parent.parent.parent / "grid_cortex_client" / "model_type.py"


def fmt_member(py_name: str, cls) -> str:
    """Return one properly indented enum member block with CortexClient.run() focused docs."""
    # Get the run method which has the actual model-specific parameters and docs
    run_fn = getattr(cls, "run", None)
    run_doc = inspect.getdoc(run_fn) or ""

    # Extract type information from the run method signature
    sig = inspect.signature(run_fn)
    type_info = {}
    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue
        if param.annotation != inspect.Parameter.empty:
            type_info[param_name] = str(param.annotation)

    # Extract return type
    return_type = None
    if sig.return_annotation != inspect.Signature.empty:
        return_type = str(sig.return_annotation)

    # Parse the run method docstring to add type information
    lines = run_doc.splitlines()
    new_lines = []
    in_args = False
    in_returns = False
    added_return_type = False  # ensure we inject return type only once

    for line in lines:
        if line.strip().startswith("Args:"):
            in_args = True
            in_returns = False
            new_lines.append(line)
            continue
        elif line.strip().startswith("Returns:"):
            in_args = False
            in_returns = True
            # Use simple "Returns:" format that GRID-Rake can parse
            new_lines.append("Returns:")
            continue
        elif in_args and line.strip().startswith(
            ("Returns:", "Raises:", "Example:", "Examples:")
        ):
            in_args = False
            in_returns = False
            new_lines.append(line)
            continue
        elif in_returns and line.strip().startswith(
            ("Raises:", "Example:", "Examples:")
        ):
            in_returns = False
            new_lines.append(line)
            continue
        elif (
            in_returns
            and line.startswith("    ")
            and not line.strip().startswith(("Raises:", "Example:", "Examples:"))
        ):
            # First descriptive line after 'Returns:' – attach type once.
            if return_type and not added_return_type:
                # Check if the line already has a type annotation (contains ":")
                if ":" in line.strip() and not line.strip().startswith("-"):
                    # Line already has type annotation, don't add another one
                    new_lines.append(line)
                    added_return_type = True
                else:
                    # Line doesn't have type annotation, add it
                    new_lines.append(f"    {return_type}: {line.strip()}")
                    added_return_type = True
            else:
                # This is a continuation line - preserve original indentation if it's already 8 spaces
                if line.startswith("        ") and not line.strip().startswith("-"):
                    # Already properly indented, keep as is
                    new_lines.append(line)
                elif line.strip() and not line.strip().startswith("-"):
                    # Indent continuation lines with 8 spaces to show they're part of the same return
                    new_lines.append("        " + line.strip())
                else:
                    new_lines.append(line)
            continue
        elif in_args and line.startswith("    ") and ":" in line:
            if not line.strip().startswith(
                ("Returns:", "Raises:", "Example:", "Examples:")
            ):
                # This is a parameter line (indented with 4 spaces and contains a colon)
                # Extract parameter name and description
                param_line = line.strip()
                if ":" in param_line:
                    param_name = param_line.split(":")[0].strip()
                    param_desc = param_line.split(":", 1)[1].strip()
                    if param_name in type_info:
                        # Add type annotation to the parameter line
                        new_lines.append(
                            f"    {param_name} ({type_info[param_name]}): {param_desc}"
                        )
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
            continue
        else:
            new_lines.append(line)

    # Join the modified docstring
    modified_doc = "\n".join(new_lines)

    # Extract examples from the run method docstring dynamically
    example_lines = []
    if "Examples:" in modified_doc:
        # Find the Examples section in the original docstring
        lines = modified_doc.splitlines()
        in_examples = False
        for i, line in enumerate(lines):
            if line.strip().startswith("Examples:"):
                in_examples = True
                example_lines.append(line)
                continue
            elif in_examples and line.strip().startswith(
                ("Raises:", "Args:", "Returns:")
            ):
                # End of examples section
                break
            elif in_examples and (
                line.strip().startswith(">>>")
                or line.strip().startswith("...")
                or line.strip() == ""
            ):
                # This is part of the examples section (including empty lines for formatting)
                example_lines.append(line)
            elif (
                in_examples
                and not line.strip().startswith((">>>", "...", ""))
                and line.strip()
            ):
                # This is the end of the examples section (non-empty line that's not part of example)
                break
    else:
        # No examples found, create a basic one
        example_lines = [
            "Examples:",
            "    >>> from grid_cortex_client import CortexClient, ModelType",
            "    >>> client = CortexClient()",
            f"    >>> result = client.run(ModelType.{py_name}, ...)",
        ]

    # Use the original docstring as-is if it has examples, otherwise add basic ones
    if "Examples:" not in modified_doc and "Example:" not in modified_doc:
        # If no example section exists, add one
        modified_doc += "\n\n" + "\n".join(example_lines)

    # Indent docstring body by 4 spaces to fit inside the enum class block
    indented = "\n".join(
        ("    " + line) if line else "" for line in modified_doc.splitlines()
    )

    return f'    {py_name} = "{cls.model_id}"\n    """\n{indented}\n    """'


def main():
    """Generate the ModelType enum file."""
    print("🔍 Discovering registered models...")

    # Get all registered models
    registry_dict = registry()
    if not registry_dict:
        print("❌ No models found in registry!")
        return 1

    print(f"📋 Found {len(registry_dict)} models: {list(registry_dict.keys())}")

    # Generate enum members
    enum_body = "\n".join(
        fmt_member(model_id.upper().replace("-", "_"), cls)
        for model_id, cls in sorted(registry_dict.items())
    )

    template = f'''"""
AUTO-GENERATED enum of all model IDs for CortexClient.run().

Use with: client.run(ModelType.MODEL_NAME, **kwargs)

Run   python -m grid_cortex_client.tools.generate_enum
whenever you add/remove a model.  Never edit manually – GRID-Rake
needs this file to exist in the source tree so that Griffe can
scrape the rich doc-strings and examples.
"""
from enum import Enum


class ModelType(Enum):
{enum_body}
'''

    # Write the file
    TARGET.write_text(template)
    print(f"✅ Regenerated {TARGET}")
    print(f"📊 Generated {len(registry_dict)} enum members")

    return 0


if __name__ == "__main__":
    sys.exit(main())
