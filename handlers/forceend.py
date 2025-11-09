import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from utils.database import SessionLocal
from models.tables import Submission
from config import LOG_GROUP_ID, GROUP_ID, ADMINS , OWNER_ID
from utils.tg_links import build_user_link


async def forceend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allows bot owner/admins to force-end an auction manually."""
    user = update.effective_user
    chat_id = update.effective_chat.id
                                              
    # ✅ Check if the user is bot owner or admin
    if user.id not in ADMINS and user.id != OWNER_ID:
        return


    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Usage: /forceend <item_id>")
        return

    item_id = context.args[0]
    session = SessionLocal()

    submission = session.query(Submission).filter(Submission.id == item_id).first()
    if not submission:
        await update.message.reply_text("❌ No item found with that ID.")
        session.close()
        return

    if submission.status not in ["approved"]:
        await update.message.reply_text("⚠️ This auction is not active or already ended.")
        session.close()
        return

    try:
        # --- Stop auction immediately ---
        submission.is_expired = True
        submission.status = "ended"
        submission.expires_at = datetime.utcnow()
        session.commit()

        type_name = getattr(submission, "type", "Waifu").capitalize()
        rarity_text = f"💎 Rarity: {getattr(submission, 'rarity_name', '')} ({getattr(submission, 'rarity', '')})"

        owner_link = (
            build_user_link(submission.user_id, submission.username)
            if submission.user_id else "Unknown Seller"
        )
        winner_link = (
            build_user_link(submission.last_bidder_id, submission.last_bidder_username)
            if submission.last_bidder_id else "No Winner"
        )

        announcement = (
            f"🚨 <b>Auction Force-Ended by Admin!</b>\n\n"
            f"💞 <b>{type_name}</b>: <code>{getattr(submission, 'waifu_name', '')}</code>\n"
            f"🎬 <b>Anime:</b> <code>{getattr(submission, 'anime_name', '')}</code>\n"
            f"{rarity_text}\n\n"
            f"💰 <b>Winning Bid:</b> <code>{submission.current_bid or 'N/A'}</code>\n"
            f"👤 <b>Seller:</b> {owner_link}\n"
            f"🏆 <b>Winner:</b> {winner_link}\n\n"
            f"🆔 <b>Item ID:</b> <code>{item_id}</code>\n"
            f"🛑 <i>Ended manually by admin {build_user_link(user.id, user.username)}</i>"
        )

        # --- Buttons ---
        buttons = []
        if submission.user_id:
            buttons.append(InlineKeyboardButton("👤 Contact Seller", url=f"tg://user?id={submission.user_id}"))
        if submission.last_bidder_id:
            buttons.append(InlineKeyboardButton("🏆 Contact Winner", url=f"tg://user?id={submission.last_bidder_id}"))
        reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None

        # === 1️⃣ Send announcement to group ===
        await context.bot.send_photo(
            chat_id=GROUP_ID,
            photo=submission.file_id,
            caption=announcement,
            parse_mode="HTML",
            reply_markup=reply_markup
        )

        # === 2️⃣ Edit channel post ===
        if getattr(submission, "channel_message_id", None):
            try:
                await context.bot.edit_message_caption(
                    chat_id=submission.channel_id,
                    message_id=submission.channel_message_id,
                    caption=f"{announcement}\n\n⏰ <b>Auction Force-Ended by Admin</b>",
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"⚠️ Failed to edit channel caption: {e}")

        # === 3️⃣ Notify winner ===
        if submission.last_bidder_id:
            try:
                msg = (
                    f"⚠️ <b>Admin Notice</b>\n\n"
                    f"Your auction win for <b>{getattr(submission, 'waifu_name', '')}</b> "
                    f"was force-ended by admin.\n"
                    f"💰 Final Bid: <code>{submission.current_bid or 'N/A'}</code>\n"
                    f"🆔 Item ID: <code>{item_id}</code>"
                )
                await context.bot.send_message(
                    chat_id=submission.last_bidder_id,
                    text=msg,
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"⚠️ Failed to notify winner: {e}")

        # === 4️⃣ Notify seller ===
        if submission.user_id:
            try:
                msg = (
                    f"🕊️ <b>Your auction has been force-ended by admin.</b>\n\n"
                    f"💞 <b>{getattr(submission, 'waifu_name', '')}</b>\n"
                    f"🏆 Winner: {winner_link}\n"
                    f"💰 Final Bid: <code>{submission.current_bid or 'N/A'}</code>"
                )
                await context.bot.send_message(
                    chat_id=submission.user_id,
                    text=msg,
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"⚠️ Failed to notify seller: {e}")

        # === 5️⃣ Log in admin group ===
        if LOG_GROUP_ID:
            try:
                await context.bot.send_photo(
                    chat_id=LOG_GROUP_ID,
                    photo=submission.file_id,
                    caption=f"🛑 <b>Force-End Log</b>\n\n{announcement}",
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"⚠️ Failed to send log: {e}")

        await update.message.reply_text(f"✅ Auction ID <code>{item_id}</code> force-ended successfully!", parse_mode="HTML")

    except Exception as e:
        print(f"❌ Force end failed: {e}")
        session.rollback()
        await update.message.reply_text("❌ Something went wrong while ending this auction.")
    finally:
        session.close()


def forceend_handler():
    return CommandHandler("forceend", forceend_command)