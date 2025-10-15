"""Fix ordered list numbering from '1. 1. 1.' to '1. 2. 3.' style."""

from pathlib import Path
import re


def fix_ordered_lists(file_path: Path) -> bool:
    """Fix ordered list numbering in a markdown file.

    Args:
        file_path: Path to the markdown file

    Returns:
        True if file was modified, False otherwise

    """
    content = file_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    modified = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this line starts with "1. "
        if re.match(r"^(\s*)1\.\s", line):
            indent = re.match(r"^(\s*)", line).group(1)

            # Found start of an ordered list
            list_count = 1

            # Continue through consecutive list items
            j = i
            while j < len(lines):
                current_line = lines[j]

                # Check if it's a list item with same indentation
                if re.match(rf"^{re.escape(indent)}1\.\s", current_line):
                    # Replace with correct number
                    lines[j] = re.sub(
                        rf"^{re.escape(indent)}1\.",
                        f"{indent}{list_count}.",
                        current_line,
                        count=1,
                    )
                    if list_count > 1:  # Changed something other than first item
                        modified = True
                    list_count += 1
                    j += 1
                # Check if it's continuation of previous item (indented)
                elif (
                    current_line.startswith(indent + "  ") or current_line.strip() == ""
                ):
                    j += 1
                else:
                    # End of list
                    break

            i = j
        else:
            i += 1

    if modified:
        file_path.write_text("\n".join(lines), encoding="utf-8")
        return True

    return False


def main() -> None:
    """Fix all markdown files in the project."""
    project_root = Path(__file__).parent.parent

    # Find all markdown files
    md_files = []
    for pattern in ["**/*.md"]:
        md_files.extend(project_root.glob(pattern))

    # Exclude certain directories
    exclude_dirs = {".venv", "target", "dist", ".git", "htmlcov"}
    md_files = [f for f in md_files if not any(ex in f.parts for ex in exclude_dirs)]

    modified_files = []
    for md_file in md_files:
        try:
            if fix_ordered_lists(md_file):
                modified_files.append(md_file)
                print(f"[OK] Fixed: {md_file.relative_to(project_root)}")
        except Exception as e:
            print(f"[ERROR] {md_file.relative_to(project_root)}: {e}")

    print(f"\n{'=' * 60}")
    print(f"Modified {len(modified_files)} file(s)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
