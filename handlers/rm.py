from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.database import SessionLocal
from models.tables import Submission
from config import OWNER_ID, ADMINS, CHANNEL_ID, GROUP_ID


# ========== REMOVE ITEMS COMMAND ==========
async def rm_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Only allow owner or admins — silently ignore others
    if user_id != OWNER_ID and user_id not in ADMINS:
        return

    # Validate command arguments
    if not context.args:
        await update.message.reply_text("Usage: /rm <item_id1> <item_id2> ...")
        return

    # Parse item IDs from command
    item_ids = []
    for arg in context.args:
        if arg.isdigit():
            item_ids.append(int(arg))
        else:
            await update.message.reply_text(f"⚠️ Invalid item ID: {arg}")
            return

    db = SessionLocal()
    deleted_count = 0

    for item_id in item_ids:
        item = db.query(Submission).filter_by(id=item_id).first()
        if item:
            # Try deleting messages from channel and group
            try:
                if getattr(item, "channel_message_id", None):
                    await context.bot.delete_message(chat_id=CHANNEL_ID, message_id=item.channel_message_id)
                if getattr(item, "group_message_id", None):
                    await context.bot.delete_message(chat_id=GROUP_ID, message_id=item.group_message_id)
            except Exception as e:
                # Ignore Telegram errors (message may already be deleted)
                pass

            # Remove from DB
            db.delete(item)
            deleted_count += 1

    db.commit()
    db.close()

    if deleted_count > 0:
        await update.message.reply_text(f"✅ Successfully deleted {deleted_count} item(s).")
    else:
        await update.message.reply_text("⚠️ No matching items found.")


# ========== REGISTER HANDLER ==========
def register_remove_handlers(app):
    app.add_handler(CommandHandler("rm", rm_items))