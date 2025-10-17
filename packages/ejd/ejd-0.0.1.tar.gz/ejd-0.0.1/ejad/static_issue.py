import os
import sys

def fix_static_issue(file_path):
    """Simulate fixing a static issue in the given file."""
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found -> {file_path}")
        sys.exit(1)

    print(f"🔧 Fixing static issue in: {file_path}")
    # Example operation: add a header line
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    fixed_content = "# Fixed static issue\n" + content

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)

    print(f"✅ Static issue fixed successfully in {file_path}")
