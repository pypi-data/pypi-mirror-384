# devforge/core/custom_generator.py
import re
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _sanitize_base_path(bp: str) -> Path:
    """
    Ensure that the base path is a valid directory.
    - If a file path is provided, use its parent directory.
    - If the path doesn't exist, try to create it.
    - If creation fails due to permissions, fall back to the current working directory.
    """
    p = Path(bp).expanduser()

    if p.exists() and p.is_file():
        logger.warning("A file was specified instead of a directory: '%s' — using its parent directory.", p)
        p = p.parent

    if not p.exists():
        try:
            p.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            fallback = Path.cwd()
            logger.warning("Permission denied when creating '%s' — using current working directory instead: %s", p, fallback)
            p = fallback

    return p


def _clean_name(raw: str) -> str:
    """
    Remove comments (after ← or #) and decorative drawing characters.
    Returns a cleaned name without tree symbols.
    """
    raw = re.split(r'←|#', raw)[0]
    raw = re.sub(r'[│└├─]+', '', raw)
    return raw.strip()


def create_structure(base_path: str, structure_text: str) -> Optional[Path]:
    """
    Create a directory and file structure from an ASCII tree string.
    Returns the project root Path if successful, or None if it fails.
    """
    base = _sanitize_base_path(base_path)
    lines = [ln.rstrip('\n') for ln in structure_text.splitlines()]

    # Find the first non-empty line to determine the root
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx >= len(lines):
        logger.error("No valid structure found in the provided text.")
        return None

    first = lines[idx].strip()
    root_name = _clean_name(first).rstrip('/')
    if not root_name:
        logger.error("Could not determine project root name from the first line.")
        return None

    project_root = base.joinpath(root_name)
    try:
        project_root.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning("Failed to create project root '%s': %s — using '%s' instead.", project_root, e, base)
        project_root = base

    stack = [(0, project_root)]

    for line in lines[idx + 1:]:
        if not line.strip() or line.strip() == '│':
            continue

        # Determine nesting depth using connectors (├ or └)
        m = re.search(r'[├└]', line)
        if m:
            prefix = line[:m.start()]
            normalized = prefix.replace('│', ' ' * 4)
            depth = (len(normalized) // 4) + 1
        else:
            lead_match = re.match(r'^([ \t│]*)', line)
            lead = lead_match.group(1) if lead_match else ''
            normalized = lead.replace('│', ' ' * 4)
            depth = (len(normalized) // 4) + 1

        # Extract and clean the item name
        name_part = re.sub(r'^.*?[├└]──\s*', '', line)
        name_part = _clean_name(name_part)
        if not name_part:
            continue

        is_dir = line.strip().endswith('/') or name_part.endswith('/')

        # Adjust the stack to point to the correct parent
        while len(stack) > 1 and stack[-1][0] >= depth:
            stack.pop()

        parent_path = Path(stack[-1][1]) if stack else project_root
        current_path = parent_path.joinpath(name_part.rstrip('/'))

        try:
            if is_dir:
                current_path.mkdir(parents=True, exist_ok=True)
                stack.append((depth, current_path))
                logger.debug("Created directory: %s (depth=%s)", current_path, depth)
            else:
                current_path.parent.mkdir(parents=True, exist_ok=True)
                if not current_path.exists():
                    current_path.write_text("", encoding="utf-8")
                    logger.debug("Created file: %s", current_path)
        except PermissionError:
            logger.warning("Permission denied when creating '%s'. Skipping.", current_path)
        except Exception as e:
            logger.error("Error creating '%s': %s", current_path, e)

    logger.info("✅ Project created successfully at: %s", project_root)
    return project_root
