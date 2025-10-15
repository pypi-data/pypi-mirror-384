"""Horilla command-line tool for managing project setup, dependencies, and upgrades."""

import platform
import subprocess
import sys
from pathlib import Path
import shutil

HORILLA_GIT_URL = "https://github.com/CybroOdooDev/HorillaCRM.git"


def install_packages():
    """Install Python dependencies from requirements.txt."""
    current_dir = Path.cwd()
    requirements_file = current_dir / "requirements.txt"

    if not requirements_file.exists():
        print("⚠️  requirements.txt not found. Skipping dependency installation.\n")
        sys.exit(1)

    print("📦 Installing Python dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            check=True,
        )
        print("✅ Dependencies installed successfully.\n")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies.\n")
        sys.exit(1)


def apply_migrations():
    """Apply Django database migrations."""
    current_dir = Path.cwd()
    manage_py = current_dir / "manage.py"

    if not manage_py.exists():
        print("⚠️  manage.py not found. Make sure you are in a Horilla project directory.\n")
        sys.exit(1)

    print("🛠️  Applying database migrations...")
    try:
        subprocess.run([sys.executable, "manage.py", "makemigrations"], check=True)
        subprocess.run([sys.executable, "manage.py", "migrate"], check=True)
        print("✅ Database migrations completed.\n")
    except subprocess.CalledProcessError:
        print("❌ Failed to apply migrations.\n")
        sys.exit(1)


def build_project():
    """Clone and initialize the Horilla project in the current directory."""
    current_dir = Path.cwd()
    git_dir = current_dir / ".git"

    print("🚀 Starting Horilla project setup...\n")

    # 1️⃣ Check for existing repo
    if git_dir.exists():
        print("⚠️  A Git repository already exists here.")
        print("👉  Use 'horillactl upgrade project' instead.\n")
        sys.exit(1)

    # 2️⃣ Ensure directory is clean (only venv allowed)
    allowed_names = {"venv", "horillavenv", ".venv"}
    other_items = [
        item for item in current_dir.iterdir() if item.name not in allowed_names
    ]
    if other_items:
        print("⚠️  Current directory contains files/folders other than a venv.")
        print(
            "👉  Please run in an empty directory or one containing only your virtual environment.\n"
        )
        sys.exit(1)

    # 3️⃣ Clone repo into a temporary folder
    tmp_dir = current_dir / ".horilla_tmp"
    print(f"📦 Step 1: Cloning Horilla project into temporary folder '{tmp_dir.name}'...")
    try:
        subprocess.run(["git", "clone", HORILLA_GIT_URL, str(tmp_dir)], check=True)
        print("✅ Repository successfully cloned.\n")
    except subprocess.CalledProcessError:
        print("❌ Git clone failed. Make sure Git is installed and the URL is correct.\n")
        sys.exit(1)

    # 4️⃣ Move files from temp folder to current folder
    print("📁 Step 2: Moving project files into current directory...")
    for item in tmp_dir.iterdir():
        target = current_dir / item.name
        if not target.exists():
            shutil.move(str(item), str(target))
    tmp_dir.rmdir()
    print("✅ Files moved successfully.\n")

    # 5️⃣ Install packages & run migrations
    install_packages()
    apply_migrations()

    # 6️⃣ Final message
    print("🎉 Horilla project setup complete!")
    print("👉 Next steps:")
    python_cmd = "python" if platform.system() == "Windows" else "python3"
    print(f"   1️⃣ Run: {python_cmd} manage.py runserver")


def upgrade_project():
    """Pull the latest updates for an existing Horilla project."""
    current_dir = Path.cwd()
    git_dir = current_dir / ".git"

    if not git_dir.exists():
        print("⚠️  No existing Horilla project found.")
        print("👉  Use 'horillactl build project' first.")
        sys.exit(1)

    print("🔄 Existing Horilla project detected. Pulling latest changes...")
    try:
        subprocess.run(["git", "pull"], check=True)
        print("\n✅ Horilla project successfully updated to the latest version!")
    except subprocess.CalledProcessError:
        print("❌ Error: Git pull failed. Make sure your repo is clean and accessible.")
        sys.exit(1)


def main():
    """CLI entry point for horillactl."""
    if len(sys.argv) < 3:
        print("Usage:")
        print("  horillactl build project    → Clone and set up a new Horilla project")
        print("  horillactl build packages   → Install Python dependencies")
        print("  horillactl build migrate    → Apply database migrations")
        print("  horillactl upgrade project  → Update existing Horilla project")
        sys.exit(1)

    command = sys.argv[1]
    subcommand = sys.argv[2]

    if command == "build" and subcommand == "project":
        build_project()
    elif command == "build" and subcommand == "packages":
        install_packages()
    elif command == "build" and subcommand == "migrate":
        apply_migrations()
    elif command == "upgrade" and subcommand == "project":
        upgrade_project()
    else:
        print(f"Unknown command: {command} {subcommand}")
        print("Try 'horillactl build project', 'horillactl build packages', or 'horillactl build migrate'")
        sys.exit(1)


if __name__ == "__main__":
    main()
