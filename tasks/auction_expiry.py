import asyncio
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils.database import SessionLocal
from models.tables import Submission
from config import LOG_GROUP_ID, GROUP_ID
from utils.tg_links import build_user_link


async def check_expired_auctions(bot):
    session = SessionLocal()
    now = datetime.utcnow()

    expired_items = (
        session.query(Submission)
        .filter(
            Submission.status == "approved",
            Submission.is_expired == False,
            Submission.expires_at <= now
        )
        .all()
    )

    if not expired_items:
        print("✅ No expired auctions found.")
        session.close()
        return

    for submission in expired_items:
        try:
            item_id = submission.id
            print(f"🔍 Processing expired auction ID: {item_id}")

            type_name = getattr(submission, "type", "Waifu").capitalize()
            rarity_text = f"💎 Rarity: {getattr(submission, 'rarity_name', '')} ({getattr(submission, 'rarity', '')})"

            # --- Build clickable user links ---
            owner_link = (
                build_user_link(submission.user_id, submission.username)
                if submission.user_id else "Unknown Seller"
            )
            winner_link = (
                build_user_link(submission.last_bidder_id, submission.last_bidder_username)
                if submission.last_bidder_id else "No Winner"
            )

            # --- Build announcement caption ---
            announcement = (
                f"🎉 <b>Auction Ended!</b>\n\n"
                f"💞 <b>{type_name}</b>: <code>{getattr(submission, 'waifu_name', '')}</code>\n"
                f"🎬 <b>Anime:</b> <code>{getattr(submission, 'anime_name', '')}</code>\n"
                f"{rarity_text}\n\n"
                f"💰 <b>Winning Bid:</b> <code>{submission.current_bid or 'N/A'}</code>\n"
                f"👤 <b>Seller:</b> {owner_link}\n"
                f"🏆 <b>Winner:</b> {winner_link}\n\n"
                f"🆔 <b>Item ID:</b> <code>{item_id}</code>"
            )

            if getattr(submission, "optional_tag", None) and getattr(submission, "optional_tag") != "—":
                announcement += f"\n{getattr(submission, 'optional_tag')}"

            # --- Inline buttons (Contact Seller/Winner) ---
            buttons = []
            if submission.user_id:
                buttons.append(InlineKeyboardButton("👤 Contact Seller", url=f"tg://user?id={submission.user_id}"))
            if submission.last_bidder_id:
                buttons.append(InlineKeyboardButton("🏆 Contact Winner", url=f"tg://user?id={submission.last_bidder_id}"))
            reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None

            # === 1️⃣ Send announcement in main group ===
            try:
                await bot.send_photo(
                    chat_id=GROUP_ID,
                    photo=submission.file_id,
                    caption=announcement,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            except Exception as e:
                print(f"⚠️ Failed to send group announcement for item {item_id}: {e}")

            # === 2️⃣ Edit channel post (mark ended) ===
            if getattr(submission, "channel_message_id", None):
                try:
                    await bot.edit_message_caption(
                        chat_id=submission.channel_id,
                        message_id=submission.channel_message_id,
                        caption=f"{announcement}\n\n⏰ <b>Auction Ended</b>",
                        parse_mode="HTML",
                        reply_markup=None
                    )
                except Exception as e:
                    print(f"⚠️ Failed to edit channel caption for item {item_id}: {e}")

            # === 3️⃣ Notify winner (if any) ===
            if submission.last_bidder_id:
                try:
                    winner_msg = (
                        f"🎉 Congratulations {winner_link}!\n\n"
                        f"You’ve <b>won</b> the auction for:\n"
                        f"💞 <b>{type_name}</b>: {getattr(submission, 'waifu_name', '')}\n"
                        f"🎬 <b>Anime:</b> {getattr(submission, 'anime_name', '')}\n\n"
                        f"💰 <b>Final Bid:</b> <code>{submission.current_bid}</code>\n"
                        f"🆔 <b>Item ID:</b> <code>{item_id}</code>\n\n"
                        f"Please contact the seller for delivery 💎"
                    )
                    await bot.send_message(
                        chat_id=submission.last_bidder_id,
                        text=winner_msg,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"⚠️ Failed to notify winner {submission.last_bidder_id}: {e}")

            # === 4️⃣ Notify seller ===
            if submission.user_id:
                try:
                    owner_msg = (
                        f"🕊️ Hello {owner_link},\n\n"
                        f"Your auction for <b>{getattr(submission, 'waifu_name', '')}</b> has ended!\n"
                        f"🏆 <b>Winner:</b> {winner_link}\n"
                        f"💰 <b>Final Bid:</b> <code>{submission.current_bid}</code>\n\n"
                        f"🆔 <b>Item ID:</b> <code>{item_id}</code>\n"
                        f"You can contact the winner directly."
                    )
                    await bot.send_message(
                        chat_id=submission.user_id,
                        text=owner_msg,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"⚠️ Failed to notify seller {submission.user_id}: {e}")

            # === 5️⃣ Log to admin/log group ===
            if LOG_GROUP_ID:
                try:
                    await bot.send_photo(
                        chat_id=LOG_GROUP_ID,
                        photo=submission.file_id,
                        caption=f"✅ <b>Auction Ended Log</b>\n\n{announcement}",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"⚠️ Failed to send log for item {item_id}: {e}")

            # === 6️⃣ Update database ===
            submission.is_expired = True
            submission.status = "ended"
            session.commit()

            print(f"🕒 Auction ended: {submission.waifu_name or submission.anime_name} (ID: {item_id})")

            await asyncio.sleep(1)  # Avoid Telegram rate limits

        except Exception as e:
            print(f"⚠️ Error while processing expired auction ID {getattr(submission, 'id', 'unknown')}: {e}")
            session.rollback()

    session.close()


async def start_expiry_task(bot, interval: int = 5):
    """Runs expiry checker every `interval` hours."""
    while True:
        try:
            print(f"⏱️ Checking expired auctions... ({datetime.utcnow().strftime('%H:%M:%S')})")
            await check_expired_auctions(bot)
        except Exception as e:
            print(f"⚠️ Expiry task crashed: {e}")
        await asyncio.sleep(interval * 60)  # Wait given hours before next check
