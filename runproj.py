"""
Single-command launcher for the complete Forest Fire Surveillance Platform.
Starts the FastAPI Backend and Vite React Frontend concurrently,
handles database initialization, detects free ports to prevent port conflicts,
and opens the dashboard in your default browser.
"""

import sys
import os
import time
import signal
import socket
import subprocess
import webbrowser
from pathlib import Path

# Ensure safe stdout encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

# Resolve python interpreter
PYTHON_EXE = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Checks if a TCP port is currently occupied."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


def find_available_port(preferred_port: int, host: str = "127.0.0.1", max_attempts: int = 20) -> int:
    """Finds an available TCP port starting from preferred_port."""
    port = preferred_port
    while is_port_in_use(port, host) and max_attempts > 0:
        port += 1
        max_attempts -= 1
    return port


def wait_for_port(port: int, host: str = "127.0.0.1", timeout: float = 12.0) -> bool:
    """Blocks until a port is accepting TCP connections or timeout expires."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_in_use(port, host):
            return True
        time.sleep(0.3)
    return False


def load_env_ports():
    """Reads API_PORT and FRONTEND_PORT from .env if present."""
    api_port = 8010
    frontend_port = 5180
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("API_PORT="):
                    val = line.split("=", 1)[1].strip()
                    if val.isdigit():
                        api_port = int(val)
                elif line.startswith("FRONTEND_PORT="):
                    val = line.split("=", 1)[1].strip()
                    if val.isdigit():
                        frontend_port = int(val)
        except Exception:
            pass
    return api_port, frontend_port


def banner(backend_port: int, frontend_port: int):
    print("=" * 68)
    print("   FireNet-XAI: Real-Time Explainable Forest Fire Surveillance")
    print("=" * 68)
    print(f"[*] Project Root:        {PROJECT_ROOT}")
    print(f"[*] Python Interpreter:  {PYTHON_EXE}")
    print(f"[*] Backend Endpoint:    http://127.0.0.1:{backend_port}")
    print(f"[*] API Documentation:   http://127.0.0.1:{backend_port}/docs")
    print(f"[*] Frontend Dashboard:  http://localhost:{frontend_port}")
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
        print("[OK] Model checkpoint verified: artifacts/checkpoints/firenet_best.pt")

    # 2. Check and seed database
    try:
        seed_cmd = [PYTHON_EXE, str(PROJECT_ROOT / "scripts" / "seed_database.py")]
        subprocess.run(seed_cmd, check=True, stdout=subprocess.DEVNULL)
        print("[OK] Database tables and surveillance towers verified.")
    except Exception as e:
        print(f"[-] Database seed notice: {e}")

    # 3. Check frontend node_modules
    if not (FRONTEND_DIR / "node_modules").exists():
        print("[!] Frontend node_modules not found. Installing npm dependencies...")
        subprocess.run(["npm", "install"], cwd=str(FRONTEND_DIR), shell=True, check=True)
    print("[OK] Frontend dependencies ready.")


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
    pref_api_port, pref_frontend_port = load_env_ports()

    backend_port = find_available_port(pref_api_port)
    frontend_port = find_available_port(pref_frontend_port)

    if backend_port != pref_api_port:
        print(f"[!] Preferred API port {pref_api_port} is busy. Auto-allocated port {backend_port}.")
    if frontend_port != pref_frontend_port:
        print(f"[!] Preferred frontend port {pref_frontend_port} is busy. Auto-allocated port {frontend_port}.")

    banner(backend_port, frontend_port)
    check_prerequisites()

    processes = []
    is_shutting_down = False

    def shutdown(sig=None, frame=None):
        nonlocal is_shutting_down
        if is_shutting_down:
            return
        is_shutting_down = True
        print("\n" + "=" * 68)
        print("[*] Gracefully stopping backend and frontend services...")
        print("=" * 68)
        for p in processes:
            kill_process_tree(p)
        print("[OK] All services stopped. Goodbye!\n")
        os._exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # 1. Launch FastAPI Backend
    print(f"\n[2/4] Starting FastAPI Backend on http://127.0.0.1:{backend_port} ...")
    backend_env = os.environ.copy()
    backend_env["API_PORT"] = str(backend_port)
    backend_env["FRONTEND_ORIGIN"] = f"http://localhost:{frontend_port}"

    backend_cmd = [
        PYTHON_EXE,
        "-m", "uvicorn",
        "backend.main:app",
        "--host", "127.0.0.1",
        "--port", str(backend_port)
    ]
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=str(PROJECT_ROOT),
        env=backend_env
    )
    processes.append(backend_proc)

    # Wait for backend port to be active
    if not wait_for_port(backend_port, timeout=10.0):
        print(f"[!] Warning: Backend port {backend_port} did not respond within timeout.")

    # 2. Launch Vite React Frontend
    print(f"[3/4] Starting Vite React Frontend on http://localhost:{frontend_port} ...")
    frontend_env = os.environ.copy()
    frontend_env["FRONTEND_PORT"] = str(frontend_port)
    frontend_env["API_PORT"] = str(backend_port)

    frontend_cmd = f"npm run dev -- --port {frontend_port}"
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=str(FRONTEND_DIR),
        shell=True,
        env=frontend_env
    )
    processes.append(frontend_proc)

    # Wait for frontend port to be active
    if not wait_for_port(frontend_port, timeout=10.0):
        print(f"[!] Warning: Frontend port {frontend_port} did not respond within timeout.")

    # 3. Launch browser
    dashboard_url = f"http://localhost:{frontend_port}"
    print(f"[4/4] Opening dashboard in browser: {dashboard_url}")
    try:
        webbrowser.open(dashboard_url)
    except Exception:
        pass

    print("\n" + "=" * 68)
    print("[+] System is ACTIVE and LIVE!")
    print(f"   * Dashboard:   {dashboard_url}")
    print(f"   * Swagger API: http://127.0.0.1:{backend_port}/docs")
    print("   * Press Ctrl+C at any time to cleanly stop all services.")
    print("=" * 68 + "\n")

    # Monitor loop
    try:
        while not is_shutting_down:
            if backend_proc.poll() is not None:
                print(f"[!] Backend process exited with code {backend_proc.returncode}")
                break
            if frontend_proc.poll() is not None:
                print(f"[!] Frontend process exited with code {frontend_proc.returncode}")
                break
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        shutdown()


if __name__ == "__main__":
    main()

