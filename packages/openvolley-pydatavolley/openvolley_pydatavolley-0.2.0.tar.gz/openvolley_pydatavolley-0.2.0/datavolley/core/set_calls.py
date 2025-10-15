# datavolley/core/setter_calls.py

import re
from typing import Dict, List, Optional


def extract_setter_calls(raw_content: str) -> List[Dict]:
    """
    Extract setter call data from DVW file content.

    Args:
        raw_content: Raw DVW file content

    Returns:
        List of setter call dictionaries
    """
    # Find the [3SETTERCALL] section that ends at the next [3 section
    setter_pattern = r"\[3SETTERCALL\](.*?)(?=\[3|\n\n|$)"
    match = re.search(setter_pattern, raw_content, re.DOTALL)

    if not match:
        return []

    setter_section = match.group(1).strip()
    lines = [line.strip() for line in setter_section.split("\n") if line.strip()]

    setter_calls = []

    # Parse each setter call line
    for line in lines:
        if line:
            call_data = parse_setter_call_line(line)
            if call_data:
                setter_calls.append(call_data)

    return setter_calls


def parse_setter_call_line(line: str) -> Optional[Dict]:
    """
    Parse a single setter call line split by semicolons.

    Args:
        line: Single setter call data line

    Returns:
        Dictionary with setter call information or None if invalid
    """
    # Split by semicolon
    parts = line.split(";")

    # Need at least the basic fields
    if len(parts) < 3:
        return None

    try:
        call_data = {
            "code": parts[0] if parts[0] else None,  # K1, KM, etc.
            "field_1": parts[1] if len(parts) > 1 else None,  # Usually empty
            "description": parts[2] if parts[2] else None,  # Quick ahead, Push, etc.
            "field_3": parts[3] if len(parts) > 3 else None,  # Usually empty
            "color_code": int(parts[4])
            if len(parts) > 4 and parts[4].isdigit()
            else None,  # Color coding
            "position_1": int(parts[5])
            if len(parts) > 5 and parts[5].isdigit()
            else None,  # Position info
            "position_2": int(parts[6])
            if len(parts) > 6 and parts[6].isdigit()
            else None,  # Position info
            "position_3": int(parts[7])
            if len(parts) > 7 and parts[7].isdigit()
            else None,  # Position info
            "additional_codes": parts[8]
            if len(parts) > 8 and parts[8]
            else None,  # Additional codes (comma-separated)
            "field_9": int(parts[9])
            if len(parts) > 9 and parts[9].isdigit()
            else None,  # Additional field
            "raw_data": parts,
        }

        # Parse additional codes if present (comma-separated values)
        if call_data["additional_codes"]:
            call_data["additional_codes_list"] = [
                code.strip()
                for code in call_data["additional_codes"].split(",")
                if code.strip()
            ]
        else:
            call_data["additional_codes_list"] = []

        return call_data

    except (ValueError, IndexError) as e:
        print(f"Error parsing setter call line: {line}")
        print(f"Error: {e}")
        return None
