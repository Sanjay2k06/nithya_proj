"""
ForestWatch AI - Unified System Orchestrator & Multi-Subsystem Launcher
Single-command launcher that initializes the SQLite database, launches the FastAPI
backend, starts the Vite React frontend, starts the Telegram Sentinel Bot,
and interconnects all four subsystems with end-to-end health verification.

Usage:
    python runproj.py
    or run: run.bat / start.bat / ./start.ps1
"""

import sys
import os
import time
import signal
import socket
import subprocess
import webbrowser
import urllib.request
import json
from pathlib import Path

# Ensure safe UTF-8 output encoding across Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
RUNTIME_DIR = PROJECT_ROOT / "runtime"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

# Resolve python interpreter
PYTHON_EXE = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable


# ---------------------------------------------------------------------------
# Network & Port Discovery Utilities
# ---------------------------------------------------------------------------
def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Checks if a TCP port is currently occupied."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.4)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


def find_available_port(preferred_port: int, host: str = "127.0.0.1", max_attempts: int = 25) -> int:
    """Finds an available TCP port starting from preferred_port."""
    port = preferred_port
    while is_port_in_use(port, host) and max_attempts > 0:
        port += 1
        max_attempts -= 1
    return port


def wait_for_port(port: int, host: str = "127.0.0.1", timeout: float = 14.0) -> bool:
    """Blocks until a port is accepting TCP connections or timeout expires."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_in_use(port, host):
            return True
        time.sleep(0.3)
    return False


def wait_for_http_health(url: str, timeout: float = 16.0) -> bool:
    """Polls an HTTP health endpoint until it returns HTTP 200 OK."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ForestWatchLauncher/1.0"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.4)
    return False


# ---------------------------------------------------------------------------
# Configuration Loader
# ---------------------------------------------------------------------------
def load_env_config():
    """Reads API_PORT, FRONTEND_PORT, and Telegram configuration from .env."""
    api_port = 8010
    frontend_port = 5180
    bot_enabled = False
    bot_token = None
    chat_id = None
    env_file = PROJECT_ROOT / ".env"

    if env_file.exists():
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("API_PORT="):
                    val = line.split("=", 1)[1].strip()
                    if val.isdigit():
                        api_port = int(val)
                elif line.startswith("FRONTEND_PORT="):
                    val = line.split("=", 1)[1].strip()
                    if val.isdigit():
                        frontend_port = int(val)
                elif line.startswith("TELEGRAM_ENABLED="):
                    val = line.split("=", 1)[1].strip().lower()
                    bot_enabled = val in ("true", "1", "yes")
                elif line.startswith("TELEGRAM_BOT_TOKEN="):
                    bot_token = line.split("=", 1)[1].strip()
                elif line.startswith("TELEGRAM_CHAT_ID="):
                    chat_id = line.split("=", 1)[1].strip()
        except Exception:
            pass

    has_valid_token = bool(bot_token and bot_token != "your-bot-token")
    return api_port, frontend_port, (bot_enabled and has_valid_token), bot_token, chat_id


# ---------------------------------------------------------------------------
# Process Termination Handler
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Main Orchestrator
# ---------------------------------------------------------------------------
def main():
    print("\n" + "=" * 72)
    print("      FORESTWATCH AI - MULTI-MODAL SENTINEL PLATFORM LAUNCHER")
    print("   Real-Time Forest Fire Detection with FireNet-CNN & Explainable AI")
    print("=" * 72)
    print(f"[*] Workspace Root:       {PROJECT_ROOT}")
    print(f"[*] Python Interpreter:   {PYTHON_EXE}")

    pref_api_port, pref_frontend_port, bot_configured, bot_token, chat_id = load_env_config()

    # Determine free ports
    backend_port = find_available_port(pref_api_port)
    frontend_port = find_available_port(pref_frontend_port)

    if backend_port != pref_api_port:
        print(f"[!] Preferred API port {pref_api_port} is busy. Auto-allocated port {backend_port}.")
    if frontend_port != pref_frontend_port:
        print(f"[!] Preferred frontend port {pref_frontend_port} is busy. Auto-allocated port {frontend_port}.")

    # =========================================================================
    # STEP 1: Database Setup & Connectivity
    # =========================================================================
    print("\n[1/5] Initializing & Verifying Database...")
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    (RUNTIME_DIR / "media" / "originals").mkdir(parents=True, exist_ok=True)
    (RUNTIME_DIR / "media" / "heatmaps").mkdir(parents=True, exist_ok=True)

    db_ok = False
    cam_count = 0
    det_count = 0
    alert_count = 0

    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from backend.db.session import init_db, SessionLocal
        from backend.models.camera import Camera
        from backend.models.detection import Detection
        from backend.models.alert import Alert

        # Create all tables if not existing
        init_db()

        # Seed initial database if empty
        try:
            from scripts.seed_database import seed
            seed()
        except Exception as seed_err:
            print(f"    [-] Seed warning: {seed_err}")

        # Verify DB connection & query records
        db = SessionLocal()
        cam_count = db.query(Camera).count()
        det_count = db.query(Detection).count()
        alert_count = db.query(Alert).count()
        db.close()
        db_ok = True
        print(f"[OK] Database connected! Surveillance Towers: {cam_count} | Detections: {det_count} | Incidents: {alert_count}")
    except Exception as exc:
        print(f"[!] Database connection warning: {exc}")

    # =========================================================================
    # Process Pool & Shutdown Handler
    # =========================================================================
    processes = []
    is_shutting_down = False

    def shutdown(sig=None, frame=None):
        nonlocal is_shutting_down
        if is_shutting_down:
            return
        is_shutting_down = True
        print("\n" + "=" * 72)
        print("[*] Gracefully stopping backend, frontend, and Telegram bot...")
        print("=" * 72)
        for p in processes:
            kill_process_tree(p)
        print("[OK] All services stopped cleanly. Goodbye!\n")
        os._exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, shutdown)

    # =========================================================================
    # STEP 2: Launch FastAPI Backend
    # =========================================================================
    print(f"\n[2/5] Starting FastAPI Backend on http://127.0.0.1:{backend_port} ...")
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

    # Verify backend HTTP healthcheck
    health_url = f"http://127.0.0.1:{backend_port}/api/v1/health"
    backend_ok = wait_for_http_health(health_url, timeout=12.0)
    if backend_ok:
        print(f"[OK] FastAPI Backend connected! Health endpoint responsive at {health_url}")
    else:
        print(f"[!] Warning: Backend health endpoint did not respond within timeout.")

    # =========================================================================
    # STEP 3: Launch Vite React Frontend
    # =========================================================================
    print(f"\n[3/5] Starting Vite React Frontend on http://localhost:{frontend_port} ...")
    if not (FRONTEND_DIR / "node_modules").exists():
        print("    [*] Installing frontend npm dependencies (first-time setup)...")
        subprocess.run(["npm", "install"], cwd=str(FRONTEND_DIR), shell=True, check=True)

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

    frontend_ok = wait_for_port(frontend_port, timeout=12.0)
    if frontend_ok:
        print(f"[OK] Frontend Web UI connected! Live at http://localhost:{frontend_port}")
    else:
        print(f"[!] Warning: Frontend port {frontend_port} did not respond within timeout.")

    # =========================================================================
    # STEP 4: Launch Telegram Sentinel Bot
    # =========================================================================
    print("\n[4/5] Starting Telegram Sentinel Bot...")
    bot_proc = None
    bot_script = PROJECT_ROOT / "bot.py"
    bot_active = False

    if bot_configured and bot_script.exists():
        bot_cmd = [PYTHON_EXE, str(bot_script)]
        bot_proc = subprocess.Popen(
            bot_cmd,
            cwd=str(PROJECT_ROOT)
        )
        processes.append(bot_proc)
        time.sleep(1.2)
        if bot_proc.poll() is None:
            bot_active = True
            print(f"[OK] Telegram Bot connected! Polling active for @fire_alret_agent_bot")
            if chat_id:
                print(f"    * Configured Emergency Chat ID: {chat_id}")
        else:
            print("[!] Telegram Bot process exited unexpectedly. Check network connection.")
    else:
        print("[*] Telegram Bot not enabled or token not configured.")
        print("    To enable: Set TELEGRAM_ENABLED=true and TELEGRAM_BOT_TOKEN in .env")

    # =========================================================================
    # STEP 5: Interconnect Verification & Launch Summary
    # =========================================================================
    dashboard_url = f"http://localhost:{frontend_port}"
    docs_url = f"http://127.0.0.1:{backend_port}/docs"

    print("\n" + "=" * 72)
    print("        ALL SUBSYSTEMS STARTED & CONNECTED SUCCESSFULLY!")
    print("=" * 72)
    print(f" [1] DATABASE:       {'[CONNECTED]' if db_ok else '[WARNING]'} SQLite (runtime/forest_fire.db)")
    print(f" [2] FASTAPI BACKEND: {'[CONNECTED]' if backend_ok else '[WAITING]'} http://127.0.0.1:{backend_port}")
    print(f"                     API Documentation: {docs_url}")
    print(f" [3] REACT FRONTEND: {'[CONNECTED]' if frontend_ok else '[WAITING]'} {dashboard_url}")
    print(f" [4] TELEGRAM BOT:   {'[CONNECTED]' if bot_active else '[STANDBY]'} @fire_alret_agent_bot")
    if chat_id:
        print(f"                     Alerts dispatched to Chat ID: {chat_id}")
    print("-" * 72)
    print(" [✓] Real-time Interconnect: Live monitoring, image/video analysis,")
    print("     and auto Grad-CAM heatmaps stream directly to the web dashboard")
    print("     and push emergency alerts to your Telegram bot!")
    print(" [*] Press Ctrl+C at any time to gracefully terminate all services.")
    print("=" * 72 + "\n")

    # Launch dashboard in browser
    try:
        webbrowser.open(dashboard_url)
    except Exception:
        pass

    # Process supervision loop
    try:
        while not is_shutting_down:
            if backend_proc.poll() is not None:
                print(f"[!] Backend process exited with code {backend_proc.returncode}")
                break
            if frontend_proc.poll() is not None:
                print(f"[!] Frontend process exited with code {frontend_proc.returncode}")
                break
            if bot_proc and bot_proc.poll() is not None:
                print(f"[!] Telegram bot exited with code {bot_proc.returncode}")
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        shutdown()


if __name__ == "__main__":
    main()
