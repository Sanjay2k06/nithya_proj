"""
ForestWatch AI - Interactive Telegram Sentinel Bot
Bot Handle: @fire_alret_agent_bot

Provides interactive commands (/start, /status, /alerts, /detections, /test, /ping, /help)
for monitoring real-time forest fire and smoke surveillance events.
"""

import sys
import os
import asyncio
import logging
from typing import Any
from pathlib import Path
from datetime import datetime, timezone

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.config import settings
from backend.db.session import SessionLocal
from backend.repositories.alerts import AlertRepository
from backend.repositories.cameras import CameraRepository
from backend.repositories.detections import DetectionRepository

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("ForestWatchBot")


def format_timestamp(dt: datetime) -> str:
    if not dt:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def _register_chat_id(chat_id: Any):
    try:
        cid_str = str(chat_id).strip()
        active_file = PROJECT_ROOT / "runtime" / "active_telegram_chat.txt"
        active_file.parent.mkdir(parents=True, exist_ok=True)
        existing = set()
        if active_file.is_file():
            existing = set(active_file.read_text(encoding="utf-8").splitlines())
        if cid_str not in existing:
            with active_file.open("a", encoding="utf-8") as f:
                f.write(f"{cid_str}\n")
            logger.info("Registered active Telegram chat ID: %s for automatic fire alerts", cid_str)
    except Exception as exc:
        logger.warning("Failed to register chat ID: %s", exc)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    chat_id = update.effective_chat.id
    _register_chat_id(chat_id)
    user_name = update.effective_user.first_name if update.effective_user else "Operator"

    text = (
        f"🌲 *ForestWatch AI Surveillance Sentinel*\n"
        f"Hello, *{user_name}*!\n\n"
        f"I am the real-time notification and telemetry bot for the "
        f"*FireNet-CNN Explainable Forest Fire Surveillance Platform*.\n\n"
        f"🆔 *Your Chat ID:* `{chat_id}` (Active & Registered!)\n"
        f"✅ *Emergency Alert Delivery:* Enabled! All live monitoring, image, and video fire alerts will be dispatched directly to this chat.\n\n"
        f"📋 *Available Commands:*\n"
        f"• /status — Surveillance system & backend health\n"
        f"• /alerts — Recent active fire and smoke alerts\n"
        f"• /detections — Latest camera inference detections\n"
        f"• /test — Test alert dispatch pipeline\n"
        f"• /ping — Check bot response latency\n"
        f"• /help — Show command reference\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /help command."""
    text = (
        f"🚨 *ForestWatch AI Sentinel Bot Guide*\n\n"
        f"Commands you can use:\n"
        f"• `/start` — Register chat and display your Chat ID\n"
        f"• `/status` — View surveillance towers, active alerts, and system health\n"
        f"• `/alerts` — View the 5 most recent incidents/alerts\n"
        f"• `/detections` — View recent inference classifications\n"
        f"• `/test` — Send a test notification to verify alert delivery\n"
        f"• `/ping` — Verify bot connectivity\n\n"
        f"⚠️ *Emergency Notifications:*\n"
        f"When a high-confidence fire or smoke event is temporally verified across "
        f"consecutive frames, the backend dispatcher automatically transmits an "
        f"emergency alert and Grad-CAM visual evidence heatmap to configured chats."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /ping command."""
    await update.message.reply_text("🟢 *Pong!* ForestWatch AI Sentinel Bot is online and active.", parse_mode="Markdown")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /status command."""
    try:
        db = SessionLocal()
        try:
            cameras = CameraRepository.get_all(db)
            active_alerts_count = AlertRepository.get_active_count(db)
            recent_detections = DetectionRepository.get_recent(db, limit=1)

            camera_names = [f"• {c.name} ({'Online' if c.enabled else 'Offline'})" for c in cameras]
            cam_list_str = "\n".join(camera_names) if camera_names else "• None configured"

            last_det_time = "N/A"
            if recent_detections:
                last_det_time = format_timestamp(recent_detections[0].created_at)

            checkpoint_file = Path(settings.MODEL_PATH)
            model_status = "Available" if checkpoint_file.is_file() else "Checkpoint missing (Demo Mode active)"

            text = (
                f"🛰️ *ForestWatch AI System Telemetry*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚡ *System Health:* `Operational`\n"
                f"🔥 *Active Incidents:* `{active_alerts_count}`\n"
                f"🧠 *AI Model Engine:* `{model_status}`\n"
                f"🕒 *Latest Detection:* `{last_det_time}`\n\n"
                f"📹 *Surveillance Towers ({len(cameras)}):*\n"
                f"{cam_list_str}\n\n"
                f"🔔 *Telegram Dispatcher:* `Enabled`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━"
            )
            await update.message.reply_text(text, parse_mode="Markdown")
        finally:
            db.close()
    except Exception as exc:
        logger.error("Failed to query status: %s", exc)
        await update.message.reply_text(f"⚠️ Error querying system telemetry: {exc}")


async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /alerts command."""
    try:
        db = SessionLocal()
        try:
            alerts, total = AlertRepository.list_paginated(db, page=1, page_size=5)
            if not alerts:
                await update.message.reply_text("✅ *No active or recent alerts found.* All sectors clear.", parse_mode="Markdown")
                return

            lines = [f"🚨 *Recent Incidents & Alerts ({len(alerts)} of {total}):*\n"]
            for a in alerts:
                emoji = "🔥" if a.alert_type.lower() == "fire" else "💨"
                status_emoji = "🔴" if a.status == "ACTIVE" else "🟡" if a.status == "ACKNOWLEDGED" else "🟢"
                ts = format_timestamp(a.created_at)
                src = a.source_name or a.source_id or "Unknown Tower"
                lines.append(
                    f"{emoji} *{a.alert_type.upper()}* [{a.severity}]\n"
                    f"   ├ Status: {status_emoji} `{a.status}`\n"
                    f"   ├ Source: `{src}`\n"
                    f"   └ Time: `{ts}`\n"
                )

            await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        finally:
            db.close()
    except Exception as exc:
        logger.error("Failed to query alerts: %s", exc)
        await update.message.reply_text(f"⚠️ Error retrieving alerts: {exc}")


async def detections_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /detections command."""
    try:
        db = SessionLocal()
        try:
            detections = DetectionRepository.get_recent(db, limit=5)
            if not detections:
                await update.message.reply_text("ℹ️ *No detection records found.*", parse_mode="Markdown")
                return

            lines = ["📷 *Recent Model Classifications:*\n"]
            for d in detections:
                emoji = "🔥" if d.predicted_class == "fire" else "💨" if d.predicted_class == "smoke" else "🌲"
                ts = format_timestamp(d.created_at)
                verified = "Verified ✅" if d.temporally_verified else "Raw frame"
                lines.append(
                    f"{emoji} *{d.predicted_class.upper()}* ({d.confidence:.1%})\n"
                    f"   ├ Verification: `{verified}`\n"
                    f"   ├ Latency: `{d.inference_time_ms:.1f} ms`\n"
                    f"   └ Time: `{ts}`\n"
                )

            await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        finally:
            db.close()
    except Exception as exc:
        logger.error("Failed to query detections: %s", exc)
        await update.message.reply_text(f"⚠️ Error retrieving detections: {exc}")


async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /test command."""
    chat_id = update.effective_chat.id
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    text = (
        f"✅ *ForestWatch AI Test Notification*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Time: `{now_str}`\n"
        f"Recipient Chat ID: `{chat_id}`\n"
        f"Status: `Connected & Ready`\n"
        f"Emergency alerts and Grad-CAM heatmaps will be delivered here automatically when fire is detected."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


def create_bot_app():
    token = settings.TELEGRAM_BOT_TOKEN
    if not token or token == "your-bot-token":
        return None

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("alerts", alerts_command))
    app.add_handler(CommandHandler("detections", detections_command))
    app.add_handler(CommandHandler("test", test_command))
    return app


async def start_bot_async():
    """Starts polling asynchronously inside FastAPI lifespan (for single-service cloud hosting on Render)."""
    app = create_bot_app()
    if not app:
        logger.warning("Telegram bot not configured. Skipping embedded start.")
        return None

    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        logger.info("ForestWatch Telegram Sentinel Bot started successfully in background.")
        return app
    except Exception as exc:
        logger.warning("Failed to start embedded Telegram bot: %s", exc)
        return None


def main():
    token = settings.TELEGRAM_BOT_TOKEN
    if not token or token == "your-bot-token":
        print("[!] ERROR: TELEGRAM_BOT_TOKEN is not configured in .env")
        print("    Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env before running.")
        sys.exit(1)

    print("=" * 64)
    print("   ForestWatch AI - Telegram Sentinel Bot (@fire_alret_agent_bot)")
    print("=" * 64)
    print(f"[*] Bot Token configured: {token[:10]}...{token[-4:]}")
    print(f"[*] Target Chat ID:       {settings.TELEGRAM_CHAT_ID}")
    print("[*] Initializing polling bot...")

    app = create_bot_app()
    if not app:
        sys.exit(1)

    print("[+] Bot is now POLLING for incoming commands.")
    print("    Open Telegram, find @fire_alret_agent_bot, and send /start")
    print("    Press Ctrl+C to terminate the bot.")
    print("=" * 64)

    try:
        app.run_polling(drop_pending_updates=True)
    except Exception as exc:
        print(f"\n[!] Bot polling error: {exc}")
        print("    Note: Telegram polling requires an active internet connection.")


if __name__ == "__main__":
    main()

