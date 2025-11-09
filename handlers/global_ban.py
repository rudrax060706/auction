import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.database import SessionLocal
from models.global_ban import GlobalBan
from config import LOG_GROUP_ID, OWNER_ID, ADMINS

# ===== CHECK IF USER IS ADMIN OR OWNER =====
def is_admin_or_owner(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in ADMINS

# ===== ADD GLOBAL BAN =====
async def aban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin_or_owner(user.id):
        return await update.message.reply_text("🚫 You don’t have permission to use this command.")

    if len(context.args) < 1 and not update.message.reply_to_message:
        return await update.message.reply_text("Usage: /aban <user_id or reply> <reason>")

    # Extract target user
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    else:
        try:
            target_id = int(context.args[0])
            target = await context.bot.get_chat(target_id)
        except Exception:
            return await update.message.reply_text("❌ Invalid user ID.")

    # Prevent self-ban or owner ban
    if target.id == user.id:
        return await update.message.reply_text("❌ You cannot ban yourself.")
    if is_admin_or_owner(target.id):
        return await update.message.reply_text("❌ You cannot ban another admin/owner.")

    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided."

    session = SessionLocal()
    try:
        # Check if already banned
        existing = session.query(GlobalBan).filter_by(user_id=target.id).first()
        if existing:
            return await update.message.reply_text(f"⚠️ {target.mention_html()} is already globally banned.", parse_mode="HTML")

        # Add new ban
        new_ban = GlobalBan(user_id=target.id, reason=reason, banned_by=user.id)
        session.add(new_ban)
        session.commit()

        # Log message
        log_text = (
            f"🚨 <b>Global Ban Executed</b>\n\n"
            f"<b>Banned User:</b> {target.mention_html()} (`{target.id}`)\n"
            f"<b>By:</b> {user.mention_html()} (`{user.id}`)\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        await context.bot.send_message(LOG_GROUP_ID, log_text, parse_mode="HTML")

        await update.message.reply_text(f"✅ {target.mention_html()} has been globally banned.\nReason: {reason}", parse_mode="HTML")
    finally:
        session.close()

# ===== REMOVE GLOBAL BAN =====
async def unaban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin_or_owner(user.id):
        return await update.message.reply_text("🚫 You don’t have permission to use this command.")

    if len(context.args) < 1 and not update.message.reply_to_message:
        return await update.message.reply_text("Usage: /unaban <user_id or reply>")

    # Extract target
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    else:
        try:
            target_id = int(context.args[0])
            target = await context.bot.get_chat(target_id)
        except Exception:
            return await update.message.reply_text("❌ Invalid user ID.")

    session = SessionLocal()
    try:
        existing = session.query(GlobalBan).filter_by(user_id=target.id).first()
        if not existing:
            return await update.message.reply_text(f"⚠️ {target.mention_html()} is not globally banned.", parse_mode="HTML")

        session.delete(existing)
        session.commit()

        log_text = (
            f"✅ <b>Global Unban Executed</b>\n\n"
            f"<b>User:</b> {target.mention_html()} (`{target.id}`)\n"
            f"<b>By:</b> {user.mention_html()} (`{user.id}`)"
        )
        await context.bot.send_message(LOG_GROUP_ID, log_text, parse_mode="HTML")

        await update.message.reply_text(f"✅ {target.mention_html()} has been unbanned globally.", parse_mode="HTML")
    finally:
        session.close()