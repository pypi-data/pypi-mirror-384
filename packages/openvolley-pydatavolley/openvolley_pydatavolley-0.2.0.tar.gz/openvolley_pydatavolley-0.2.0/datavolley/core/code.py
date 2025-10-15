# datavolley/core/code.py

import re
from typing import Dict, Optional


def parse_play_code(raw_content: str, code: str) -> Optional[Dict]:
    """
    Parse a volleyball play code into its components.

    DVW play codes have the format: [*|a][player][skill][evaluation][attack_combo][zone][evaluation_details]

    Examples:
        *19SM+~~~78A~~~00 - Home team player 19, serve (S), positive evaluation (+), middle attack (M)
        a02RM-~~~58AM~~00B - Visiting team player 02, reception (R), negative evaluation (-), middle attack (M)
        *08EH#~~~~8C~~~00 - Home team player 08, attack (E), error (#), high ball (H)

    Args:
        raw_content: Raw DVW file content
        code: The play code string to parse

    Returns:
        Dictionary with parsed code components or None if invalid
    """
    if not code or len(code) < 4:
        return None

    parsed = {
        "code": code,
        "team": None,
        "player_number": None,
        "player_name": None,
        "player_id": None,
        "skill": None,
        "skill_type": None,
        "evaluation_code": None,
        "set_code": None,
        "start_zone": None,
        "end_zone": None,
        "end_subzone": None,
        "num_players_numeric": None,
        "skill_subtype": None,
        "attack_code": None,
        "custom_code": None,
    }

    # Extract Team using inline team extraction (avoid circular imports)
    teams = _extract_teams_lightweight(raw_content)
    if code.startswith("*"):
        parsed["team"] = teams.get("team_1")
    elif code.startswith("a"):
        parsed["team"] = teams.get("team_2")

    # Extract Player Number (positions 1-2)
    try:
        player_number = code[1:3]
        if player_number.isdigit():
            parsed["player_number"] = int(player_number)
    except (IndexError, ValueError):
        pass

    # Extract Player details using inline player extraction (avoid circular imports)
    players = _extract_players_lightweight(raw_content)
    if code.startswith("*") and parsed["player_number"]:
        player = next(
            (
                p
                for p in players["home"]
                if int(p["player_number"]) == parsed["player_number"]
            ),
            None,
        )
        if player:
            parsed["player_name"] = player["full_name"]
            parsed["player_id"] = player["player_id"]
    elif code.startswith("a") and parsed["player_number"]:
        player = next(
            (
                p
                for p in players["visiting"]
                if int(p["player_number"]) == parsed["player_number"]
            ),
            None,
        )
        if player:
            parsed["player_name"] = player["full_name"]
            parsed["player_id"] = player["player_id"]

    # Extract Skill (position 3, or position 1 for point codes)
    if len(code) > 3:
        skill_mapping = {
            "S": "Serve",
            "R": "Reception",
            "E": "Set",
            "A": "Attack",
            "D": "Dig",
            "B": "Block",
            "F": "Freeball",
            "p": "Point",
        }
        # Point codes have format *p01:00 where 'p' is at position 1
        if len(code) > 1 and code[1] == "p":
            parsed["skill"] = "Point"
        else:
            skill_code = code[3]
            parsed["skill"] = skill_mapping.get(skill_code, "")

    # Extract Evaluation (position 4)
    if len(code) > 4:
        parsed["evaluation_code"] = code[5]

    # Extract Attack combination
    if len(code) > 6 and code[3] == "A" and code[6:8] != "~~":
        parsed["attack_code"] = code[6:8]

    # Extract Set codes
    if len(code) > 6 and code[3] == "E" and code[6:8] != "~~":
        parsed["set_code"] = code[6:8]

    # Extract Blockers
    if len(code) > 13 and parsed["skill"] == "Attack":
        try:
            parsed["num_players_numeric"] = int(code[13])
        except (ValueError, IndexError):
            pass

    # Extract Zones (positions 9-11)
    if len(code) > 9:
        parsed["start_zone"] = code[9] if code[9] != "~" else None
    if len(code) > 10:
        parsed["end_zone"] = code[10] if code[10] != "~" else None
    if len(code) > 11:
        parsed["end_subzone"] = code[11] if code[11] != "~" else None

    # Extract custom code (after last ~ and before end of string)
    if len(code) > 14:
        last_tilde_idx = code.rfind("~")
        if last_tilde_idx != -1 and last_tilde_idx < len(code) - 1:
            potential_custom = code[last_tilde_idx + 1 :]
            if potential_custom and potential_custom != "":
                parsed["custom_code"] = potential_custom

    # Extract skill_type (position 4) - full description like "High ball attack"
    if parsed["skill"] and len(code) > 4:
        parsed["skill_type"] = extract_skill_type(code, parsed["skill"])

    # Extract Skill subtype
    if parsed["skill"]:
        parsed["skill_subtype"] = extract_skill_subtype(code, parsed["skill"])

    return parsed


def extract_skill_type(code: str, skill: str) -> Optional[str]:
    """
    Extract skill type description from position 4 of the code.

    This returns descriptions like "High ball attack", "Jump-float serve", etc.

    Args:
        code: The play code
        skill: The skill name (Serve, Reception, Attack, etc.)

    Returns:
        Skill type description or None
    """
    # Point and Freeball don't have type codes
    if skill in ["Point", "Freeball", ""]:
        return None

    if len(code) <= 4:
        return None

    type_code = code[4]

    if skill == "Serve":
        serve_type_map = {
            "H": "Float serve",
            "M": "Jump-float serve",
            "Q": "Jump serve",
            "T": "Topspin serve",
            "O": "Other serve",
            "N": "Hybrid serve",
        }
        return serve_type_map.get(type_code)

    elif skill == "Reception":
        reception_type_map = {
            "H": "Float serve reception",
            "M": "Jump-float serve reception",
            "Q": "Jump serve reception",
            "T": "Topspin serve reception",
            "O": "Other serve reception",
            "N": "Hybrid serve reception",
        }
        return reception_type_map.get(type_code)

    elif skill in ["Attack", "Block", "Dig", "Set"]:
        attack_type_map = {
            "H": f"High ball {skill.lower()}",
            "M": f"Half ball {skill.lower()}",
            "Q": f"Quick ball {skill.lower()}",
            "T": f"Head ball {skill.lower()}",
            "U": f"Super ball {skill.lower()}",
            "F": f"Fast ball {skill.lower()}",
            "N": f"Slide ball {skill.lower()}",
            "O": f"Other {skill.lower()}",
        }
        return attack_type_map.get(type_code)

    return None


def extract_skill_subtype(code: str, skill: str) -> Optional[str]:
    """
    Extract skill subtype from the code based on skill type.

    Args:
        code: The play code
        skill: The skill name (Serve, Reception, Attack, etc.)

    Returns:
        Skill subtype description or None
    """

    # Serve subtypes (position 4)
    serve_subtype_map = {
        "Q": "Jump Spin",  # Updated to match your requirement
        "M": "Jump Float",
        "T": "Standing Float",
        "H": "Float",  # Updated to match your requirement
        "O": "Serve Other",
        "N": "Hybrid",
    }

    # Attack subtypes (position 12)
    attack_subtypes = {
        "H": "Hard",
        "P": "Soft spike",
        "T": "Tip",
        "O": "Other attack",
    }

    # Set subtypes (position 4)
    set_subtypes = {
        "1": "1 hand set",
        "2": "2 hands set",
        "3": "Bump set",
        "4": "Other set",
        "5": "Underhand set",
    }

    # Block subtypes (position 4)
    block_subtypes = {
        "0": "No block",
        "1": "1 player block",
        "2": "2 player block",
        "3": "3 player block",
        "4": "Hole block",
    }

    if skill == "Serve" and len(code) > 4:
        subtype_code = code[4]
        return serve_subtype_map.get(subtype_code, None)

    elif skill == "Reception" and len(code) > 4:
        # Use the same serve subtype map for reception
        subtype_code = code[4]
        return serve_subtype_map.get(subtype_code, None)

    elif skill == "Attack" and len(code) > 12:
        # Attack subtype is at position 12 (index 12:13)
        # Example: 'a15AN-CF~23DT2~-5F' -> 'T' at position 12
        subtype_code = code[12]
        if subtype_code != "~":
            return attack_subtypes.get(subtype_code, None)
        return None

    elif skill == "Set" and len(code) > 4:
        subtype_code = code[4]
        return set_subtypes.get(subtype_code, None)

    elif skill == "Block" and len(code) > 4:
        subtype_code = code[4]
        return block_subtypes.get(subtype_code, None)

    elif skill == "Dig" and len(code) > 4:
        # Dig uses same subtypes as serve/reception
        subtype_code = code[4]
        return serve_subtype_map.get(subtype_code, None)

    return None


def _extract_teams_lightweight(raw_content: str) -> Dict:
    """
    Lightweight team extraction to avoid circular imports.
    """
    teams_pattern = r"\[3TEAMS\](.*?)(?=\[3|\n\n|$)"
    match = re.search(teams_pattern, raw_content, re.DOTALL)

    if not match:
        return {}

    teams_section = match.group(1).strip()
    lines = [line.strip() for line in teams_section.split("\n") if line.strip()]

    teams_data = {}
    for i, line in enumerate(lines):
        if line:
            parts = line.split(";")
            if len(parts) >= 2:
                if i == 0:
                    teams_data["team_1"] = parts[1] if parts[1] else None
                elif i == 1:
                    teams_data["team_2"] = parts[1] if parts[1] else None

    return teams_data


def _extract_players_lightweight(raw_content: str) -> Dict:
    """
    Lightweight player extraction to avoid circular imports.
    """
    players = {"home": [], "visiting": []}

    # Extract home team players
    home_pattern = r"\[3PLAYERS-H\](.*?)(?=\[3PLAYERS-V\]|\[3|\n\n|$)"
    home_match = re.search(home_pattern, raw_content, re.DOTALL)

    if home_match:
        home_section = home_match.group(1).strip()
        players["home"] = _parse_player_lines_lightweight(home_section)

    # Extract visiting team players
    visiting_pattern = r"\[3PLAYERS-V\](.*?)(?=\[3|\n\n|$)"
    visiting_match = re.search(visiting_pattern, raw_content, re.DOTALL)

    if visiting_match:
        visiting_section = visiting_match.group(1).strip()
        players["visiting"] = _parse_player_lines_lightweight(visiting_section)

    return players


def _parse_player_lines_lightweight(section_content: str):
    """
    Lightweight player line parsing.
    """
    players = []
    lines = [line.strip() for line in section_content.split("\n") if line.strip()]

    for line in lines:
        parts = line.split(";")
        if len(parts) >= 10:
            try:
                player_number = parts[1] if len(parts) > 1 and parts[1] else "0"
                last_name = parts[9] if len(parts) > 9 and parts[9] else None
                first_name = parts[10] if len(parts) > 10 and parts[10] else None
                player_id = (
                    parts[8]
                    if len(parts) > 8 and parts[8]
                    else f"player_{player_number}"
                )

                full_name = (
                    " ".join(list(filter(None, [first_name, last_name]))) or None
                )

                player = {
                    "player_number": player_number,
                    "player_id": player_id,
                    "full_name": full_name,
                }
                players.append(player)
            except (ValueError, IndexError):
                continue

    return players
