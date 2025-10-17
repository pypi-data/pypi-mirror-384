import os
import subprocess
from pathlib import Path
import textwrap
import json

def cli_main():
    print("Welcome to FastAPI + React setup wizard\n")

    # Get project name
    project_name = input("Enter project name (default: myapp): ").strip() or "myapp"
    project_dir = Path(project_name)
    project_dir.mkdir(exist_ok=True)

    # --- Backend setup ---
    backend_dir = project_dir / "backend"
    backend_dir.mkdir(exist_ok=True)

    # Read backend template from file
    backend_template_path = Path(__file__).parent / "backend_template.py"
    backend_code = backend_template_path.read_text()
    (backend_dir / "main.py").write_text(backend_code)
    print("Backend created successfully!\n")

    # --- Create requirements.txt ---
    req_file = backend_dir / "requirements.txt"
    req_file.write_text("fastapi\nuvicorn\n")
    print(f"requirements.txt created at {req_file.resolve()}")

    # --- Always use default venv name ---
    venv_name = "venv"
    venv_dir = project_dir / venv_name
    print(f"\nCreating virtual environment '{venv_name}'...")
    if os.name == "nt":
        venv_cmd = ["python", "-m", "venv", venv_name]
        activate_cmd = f"{venv_name}\\Scripts\\activate"
    else:
        venv_cmd = ["python3", "-m", "venv", venv_name]
        activate_cmd = f"source {venv_name}/bin/activate"
    subprocess.run(venv_cmd, cwd=project_dir, check=True)
    print(f"Virtual environment created at {venv_dir.resolve()}")

    # --- Frontend setup (interactive) ---
    print("Launching React/Vite setup wizard...\n")
    subprocess.run(
        ["npx", "create-launcher"],
        cwd=project_dir,
        check=True,
        stdin=None,
        stdout=None,
        stderr=None
    )

    # --- Detect frontend folder ---
    created_dirs = [d for d in project_dir.iterdir() if d.is_dir() and d.name not in ["backend", venv_name]]
    if not created_dirs:
        print("Could not detect frontend folder. Please check the create-launcher output.")
        return
    frontend_dir = created_dirs[0]

    print(f"\nDetected frontend directory: {frontend_dir.name}")

    # --- Write frontend template to App.jsx or App.tsx ---
    frontend_template_path = Path(__file__).parent / "frontend_template.jsx"
    frontend_code = frontend_template_path.read_text()
    app_file = frontend_dir / "src" / "App.jsx"
    if not app_file.exists():
        app_file = frontend_dir / "src" / "App.tsx"
    if app_file.exists():
        app_file.write_text(frontend_code)
        print("Updated frontend App.jsx to show FastAPI + React message.")
    else:
        print("Could not find App.jsx or App.tsx to modify automatically.")

    # --- Add Vite proxy if vite.config.ts or vite.config.js exists ---
    vite_config = None
    for config_name in ["vite.config.ts", "vite.config.js"]:
        config_path = frontend_dir / config_name
        if config_path.exists():
            vite_config = config_path
            break
    if vite_config:
        vite_config.write_text(textwrap.dedent("""
            import { defineConfig } from 'vite'
            import react from '@vitejs/plugin-react'

            export default defineConfig({
              plugins: [react()],
              server: {
                proxy: {
                  '/api': 'http://localhost:8000',
                },
              },
            })
        """))
        print("Added Vite proxy to forward /api to FastAPI backend.")

    # --- Final instructions ---
    print(textwrap.dedent(f"""
    All done!

    To activate your environment and install backend dependencies, run:
        cd {project_name}
        {activate_cmd}
        pip install -r backend/requirements.txt

    Start backend:
        cd backend
        uvicorn main:app --reload

    Start frontend:
        cd {frontend_dir.name}
        npm run dev

    Then open http://localhost:5173 in your browser
    """))
