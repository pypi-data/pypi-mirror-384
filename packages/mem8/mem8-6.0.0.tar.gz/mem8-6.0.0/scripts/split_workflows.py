#!/usr/bin/env python3
"""Split workflows.md into separate focused pages."""

from pathlib import Path
import re

def split_workflows():
    """Split the large workflows.md file into focused pages."""

    root = Path(__file__).parent.parent
    workflows_md = root / "documentation" / "docs" / "workflows.md"
    workflows_dir = root / "documentation" / "docs" / "workflows"

    # Read the full file
    content = workflows_md.read_text(encoding='utf-8')

    # Split by main sections (## Phase)
    sections = re.split(r'^## (Phase \d+:.*?)$', content, flags=re.MULTILINE)

    # First section is the intro (before first Phase)
    # Skip the intro as we already have index.md

    # Process phase sections
    phases = {}
    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):
            title = sections[i]
            body = sections[i + 1]
            phases[title] = body

    print(f"Found {len(phases)} phase sections")

    # Extract other sections (utility commands, advanced workflows, best practices)
    utility_match = re.search(r'## Utility Commands.*?(?=## Advanced Workflows|## Best Practices|$)', content, re.DOTALL)
    advanced_match = re.search(r'## Advanced Workflows.*?(?=## Best Practices|$)', content, re.DOTALL)
    best_practices_match = re.search(r'## Best Practices.*$', content, re.DOTALL)

    # Create individual page files
    for phase_title, phase_content in phases.items():
        # Determine filename from title
        if "Phase 1" in phase_title:
            filename = "research.md"
            sidebar_pos = 1
        elif "Phase 2" in phase_title:
            filename = "plan.md"
            sidebar_pos = 2
        elif "Phase 3" in phase_title:
            filename = "implement.md"
            sidebar_pos = 3
        elif "Phase 4" in phase_title:
            filename = "commit.md"
            sidebar_pos = 4
        else:
            continue

        # Write the page
        page_path = workflows_dir / filename
        with open(page_path, 'w', encoding='utf-8') as f:
            f.write(f"---\nsidebar_position: {sidebar_pos}\n---\n\n")
            f.write(f"# {phase_title}\n")
            f.write(phase_content.strip())
            f.write("\n")

        print(f"✓ Created {filename}")

    # Create utility commands page
    if utility_match:
        utility_path = workflows_dir / "utility.md"
        with open(utility_path, 'w', encoding='utf-8') as f:
            f.write("---\nsidebar_position: 5\n---\n\n")
            f.write(utility_match.group(0))
        print("✓ Created utility.md")

    # Create advanced workflows page
    if advanced_match:
        advanced_path = workflows_dir / "advanced.md"
        with open(advanced_path, 'w', encoding='utf-8') as f:
            f.write("---\nsidebar_position: 6\n---\n\n")
            f.write(advanced_match.group(0))
        print("✓ Created advanced.md")

    # Create best practices page
    if best_practices_match:
        practices_path = workflows_dir / "best-practices.md"
        with open(practices_path, 'w', encoding='utf-8') as f:
            f.write("---\nsidebar_position: 7\n---\n\n")
            f.write(best_practices_match.group(0))
        print("✓ Created best-practices.md")

    print("\nAll workflow pages created successfully!")
    print(f"Pages in: {workflows_dir}")

if __name__ == "__main__":
    split_workflows()
