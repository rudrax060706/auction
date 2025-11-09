from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from sqlalchemy import text
from utils.database import SessionLocal, engine
from models.tables import Submission, User
from config import OWNER_ID, ADMINS
from datetime import datetime


# ================= /STATUS COMMAND =================
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # Allow only Owner or Admins
    if user_id != OWNER_ID and user_id not in ADMINS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    session = SessionLocal()
    text_msg = "📊 <b>System Status Overview</b>\n\n"

    # ================= MYSQL CONNECTION =================
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            mysql_status = "✅ Connected"
    except Exception:
        mysql_status = "❌ Disconnected"

    # ================= BOT STATUS =================
    bot_status = "✅ Running"

    # ================= USER STATS =================
    try:
        active_users = session.query(User).filter(User.is_banned == False).count()
        inactive_users = session.query(User).filter(User.is_banned == True).count()
    except Exception:
        active_users = "⚠️ Error"
        inactive_users = "⚠️ Error"

    # ================= AUCTION STATS =================
    try:
        active_auctions = session.query(Submission).filter(Submission.status == "active").count()
        inactive_auctions = session.query(Submission).filter(Submission.status == "ended").count()
    except Exception:
        active_auctions = "⚠️ Error"
        inactive_auctions = "⚠️ Error"

    # ================= ITEM STATS =================
    try:
        active_items = session.query(Submission).filter(Submission.status == "active").count()
        pending_items = session.query(Submission).filter(Submission.status == "pending").count()
    except Exception:
        active_items = "⚠️ Error"
        pending_items = "⚠️ Error"

    # ================= TIMESTAMP =================
    last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ================= BUILD MESSAGE =================
    text_msg += (
        f"🧑‍💻 <b>Active Users:</b> {active_users}\n"
        f"😴 <b>Inactive/Banned Users:</b> {inactive_users}\n\n"
        f"🏷️ <b>Active Auctions:</b> {active_auctions}\n"
        f"💤 <b>Inactive Auctions:</b> {inactive_auctions}\n\n"
        f"📦 <b>Active Items:</b> {active_items}\n"
        f"⏳ <b>Pending Items:</b> {pending_items}\n\n"
        f"🧩 <b>MySQL Status:</b> {mysql_status}\n"
        f"🤖 <b>Bot Status:</b> {bot_status}\n"
        f"🕒 <b>Last Update:</b> {last_update}\n"
    )

    await update.message.reply_text(text_msg, parse_mode="HTML")
    session.close()


# ================= HANDLER REGISTRATION =================
status_handler = CommandHandler("status", status_command)