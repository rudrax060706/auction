from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
)
from utils.database import SessionLocal
from models.tables import Submission
from .add_command import is_private_chat, RARITY_MAP # Assuming relative import for shared components
from config import LOG_GROUP_ID
# ====== CONFIG (Placeholder for logs group) ======
 # Placeholder for your actual LOG_GROUP_ID


# ====== BASE BID HANDLER ======
async def handle_base_bid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private_chat(update):
        return
    if not context.user_data.get("awaiting_bid"):
        return  # Ignore if we’re not expecting a bid

    user = update.message.from_user
    text = update.message.text.strip()

    # Validate numeric input
    if not text.isdigit():
        await update.message.reply_text("⚠️ Please enter a valid number for base bid.")
        return

    base_bid = int(text)
    context.user_data["base_bid"] = base_bid
    context.user_data.pop("awaiting_bid", None)  # Clear state

    # Save submission to DB
    db = SessionLocal()
    item_id = None
    try:
        new_submission = Submission(
            user_id=int(user.id),
            user_name=user.first_name or "N/A",
            username=f"@{user.username}" if user.username else "N/A",
            type=context.user_data["type"],
            rarity=context.user_data["rarity"],
            rarity_name=RARITY_MAP.get(context.user_data["rarity"], "Unknown"),
            anime_name=context.user_data["anime_name"],
            waifu_name=context.user_data["waifu_name"],
            optional_tag=context.user_data["optional_tag"],
            caption=context.user_data["caption"],
            file_id=context.user_data["file_id"],
            submitted_time=datetime.now(),
            base_bid=base_bid,
            status="pending",
        )
        db.add(new_submission)
        db.commit()
        db.refresh(new_submission)
        item_id = new_submission.id
    finally:
        db.close()

    # Send to logs group
    log_caption = (
        f"📩 <b>New {context.user_data['type'].capitalize()} Submission</b>\n\n"
        f"🆔 <b>Item ID:</b> <code>{item_id}</code>\n"
        f"👤 <b>Name:</b> {user.first_name}\n"
        f"🔗 <b>Username:</b> @{user.username if user.username else 'N/A'}\n"
        f"🎬 <b>Anime:</b> {context.user_data['anime_name']}\n"
        f"💞 <b>{context.user_data['type'].capitalize()}:</b> {context.user_data['waifu_name']}\n"
        f"💎 <b>Rarity:</b> {RARITY_MAP.get(context.user_data['rarity'])} {context.user_data['rarity']}\n"
        f"💰 <b>Base Bid:</b> {base_bid}\n"
        f"🏷️ <b>Tag:</b> {context.user_data['optional_tag']}\n"
        f"⏰ <b>Submitted:</b> {datetime.now().strftime('%d %B %Y • %I:%M %p')}"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{item_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{item_id}"),
        ]
    ]

    try:
        await context.bot.send_photo(
            chat_id=int(LOG_GROUP_ID),
            photo=context.user_data["file_id"],
            caption=log_caption,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except Exception:
        pass

    await update.message.reply_text("✅ Sent to the owner for approval!")

    # Clear temp data
    context.user_data.clear()
    

# ====== HANDLERS LIST FOR bid_handler.py ======
bid_handlers = [
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_base_bid),
]