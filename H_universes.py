from pathlib import Path
import importlib.util
import itertools
import sys

source_path = Path("/mnt/data/generate_h_manifold_states.py")
text = source_path.read_text(encoding="utf-8")

old = '''def describe(rotations, axes) -> str:
    rotation_parts = [
        rotations[p].description
        for p in ("xy", "zw", "xz", "yw", "xw", "yz")
        if rotations[p].description
    ]
    axis_parts = [
        axes[a].description
        for a in ("x", "y", "z", "w")
        if axes[a].description
    ]

    if rotation_parts and axis_parts:
        return "; ".join(rotation_parts) + " | " + "; ".join(axis_parts)
    if rotation_parts:
        return "; ".join(rotation_parts)
    if axis_parts:
        return "; ".join(axis_parts)
    return "baseline H; no active dynamics"
'''

new = '''def describe(rotations, axes) -> str:
    """
    Consolidate all like-action properties into compact groups.

    Example:
        contraction: x+y | expansion: z | clockwise rotation: yw+zw
    """
    groups = []

    axis_group_specs = (
        ("contraction", "contract"),
        ("expansion", "expand"),
        ("changing contraction", "changing_contract"),
        ("changing expansion", "changing_expand"),
    )
    for label, key in axis_group_specs:
        members = [
            axis
            for axis in ("x", "y", "z", "w")
            if axes[axis].key == key
        ]
        if members:
            groups.append(f"{label}: {'+'.join(members)}")

    rotation_group_specs = (
        ("clockwise rotation", "cw"),
        ("widdershins rotation", "ccw"),
    )
    for label, key in rotation_group_specs:
        members = [
            plane
            for plane in ("xy", "zw", "xz", "yw", "xw", "yz")
            if rotations[plane].key == key
        ]
        if members:
            groups.append(f"{label}: {'+'.join(members)}")

    return " | ".join(groups) if groups else "baseline H; no active dynamics"
'''

if old not in text:
    raise RuntimeError("Could not locate the original describe() function.")

updated = text.replace(old, new)

updated_path = Path("/mnt/data/generate_h_manifold_states_grouped.py")
updated_path.write_text(updated, encoding="utf-8")

spec = importlib.util.spec_from_file_location("h_grouped", updated_path)
module = importlib.util.module_from_spec(spec)
sys.modules["h_grouped"] = module
spec.loader.exec_module(module)

preview_path = Path("/mnt/data/h_manifold_grouped_preview.txt")
with preview_path.open("w", encoding="utf-8", newline="\n") as handle:
    for index, compass, description in itertools.islice(module.iter_states("basic"), 40):
        handle.write(f"{index:>6}\t{compass}\t{description}\n")

print(updated_path)
print(preview_path)
