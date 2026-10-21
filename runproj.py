"""
Single-command launcher for the complete Forest Fire Surveillance Platform.
Starts the FastAPI Backend and Vite React Frontend concurrently,
handles database initialization, and opens the dashboard in your default browser.
"""

import sys
import os
import time
import signal
import subprocess
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

# Resolve python interpreter
PYTHON_EXE = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable


def banner():
    print("=" * 68)
    print(" 🔥 FireNet-XAI: Real-Time Explainable Forest Fire Surveillance 🔥")
    print("=" * 68)
    print(f"[*] Project Root:        {PROJECT_ROOT}")
    print(f"[*] Python Interpreter:  {PYTHON_EXE}")
    print(f"[*] Backend Endpoint:    http://127.0.0.1:8000")
    print(f"[*] API Documentation:   http://127.0.0.1:8000/docs")
    print(f"[*] Frontend Dashboard:  http://localhost:5173")
    print("=" * 68)


def check_prerequisites():
    """Validates model checkpoints and database initialization."""
    print("\n[1/4] Verifying model weights and database setup...")

    # 1. Check model checkpoint
    checkpoint_path = PROJECT_ROOT / "artifacts" / "checkpoints" / "firenet_best.pt"
    if not checkpoint_path.exists():
        print("[!] No checkpoint found. Initializing FireNetCNN weights via synthetic training...")
        train_cmd = [
            PYTHON_EXE,
            str(PROJECT_ROOT / "scripts" / "train_model.py"),
            "--use-synthetic",
            "--epochs", "3",
            "--batch-size", "8"
        ]
        subprocess.run(train_cmd, check=True)
    else:
        print("[✓] Model checkpoint verified: artifacts/checkpoints/firenet_best.pt")

    # 2. Check and seed database
    try:
        seed_cmd = [PYTHON_EXE, str(PROJECT_ROOT / "scripts" / "seed_database.py")]
        subprocess.run(seed_cmd, check=True, stdout=subprocess.DEVNULL)
        print("[✓] Database tables and surveillance towers verified.")
    except Exception as e:
        print(f"[-] Database seed notice: {e}")

    # 3. Check frontend node_modules
    if not (FRONTEND_DIR / "node_modules").exists():
        print("[!] Frontend node_modules not found. Installing npm dependencies...")
        subprocess.run(["npm", "install"], cwd=str(FRONTEND_DIR), shell=True, check=True)
    print("[✓] Frontend dependencies ready.")


def kill_process_tree(proc):
    """Cleanly terminates a process and all its children on Windows/Unix."""
    if proc is None or proc.poll() is not None:
        return
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            proc.terminate()
            proc.wait(timeout=3)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def main():
    banner()
    check_prerequisites()

    processes = []

    def shutdown(sig=None, frame=None):
        print("\n\n" + "=" * 68)
        print("[*] Gracefully stopping backend and frontend services...")
        print("=" * 68)
        for p in processes:
            kill_process_tree(p)
        print("[✓] All services stopped. Goodbye!")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # 1. Launch FastAPI Backend
    print("\n[2/4] Starting FastAPI Backend on http://127.0.0.1:8000 ...")
    backend_cmd = [
        PYTHON_EXE,
        "-m", "uvicorn",
        "backend.main:app",
        "--host", "127.0.0.1",
        "--port", "8000"
    ]
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=str(PROJECT_ROOT)
    )
    processes.append(backend_proc)

    # Give backend a moment to bind port 8000
    time.sleep(2)

    # 2. Launch Vite React Frontend
    print("[3/4] Starting Vite React Frontend on http://localhost:5173 ...")
    frontend_cmd = "npm run dev"
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=str(FRONTEND_DIR),
        shell=True
    )
    processes.append(frontend_proc)

    # 3. Launch browser
    time.sleep(2)
    print("[4/4] Opening dashboard in browser: http://localhost:5173")
    try:
        webbrowser.open("http://localhost:5173")
    except Exception:
        pass

    print("\n" + "=" * 68)
    print("🚀 System is ACTIVE and LIVE!")
    print("   • Dashboard:   http://localhost:5173")
    print("   • Swagger API: http://127.0.0.1:8000/docs")
    print("   • Press Ctrl+C at any time to cleanly stop all services.")
    print("=" * 68 + "\n")

    # Monitor loop
    try:
        while True:
            # Check if any process died unexpectedly
            if backend_proc.poll() is not None:
                print(f"[!] Backend process exited with code {backend_proc.returncode}")
                break
            if frontend_proc.poll() is not None:
                print(f"[!] Frontend process exited with code {frontend_proc.returncode}")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        shutdown()


if __name__ == "__main__":
    main()
