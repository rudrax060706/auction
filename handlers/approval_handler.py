from datetime import datetime, timedelta
from telegram.ext import JobQueue
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
)
from utils.database import SessionLocal
from models.tables import Submission
from .add_command import safe_split, RARITY_MAP, GROUP_ID, CHANNEL_ID, GROUP_URL # Assuming relative import for shared components
from config import OWNER_ID,ADMINS



# ====== AUTO UNPIN AFTER DELAY ======
async def unpin_after_delay(context: ContextTypes.DEFAULT_TYPE):
    """Automatically unpins the auction post after 3 days."""
    data = context.job.data
    chat_id = int(data.get("chat_id"))
    message_id = int(data.get("message_id"))

    try:
        await context.bot.unpin_chat_message(chat_id=chat_id, message_id=message_id)
        print(f"✅ Unpinned message {message_id} in chat {chat_id}")
    except Exception as e:
        err = str(e).lower()
        if "message to unpin not found" in err or "message can't be unpinned" in err:
            print(f"⚠️ Already unpinned or deleted ({message_id})")
        elif "chat not found" in err:
            print(f"⚠️ Chat {chat_id} no longer exists or bot removed.")
        else:
            print(f"[Error unpinning message {message_id}] {e}")


# ====== APPROVAL HANDLER ======
async def approval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()

    split_data = safe_split(query.data)
    if not isinstance(split_data, list) or len(split_data) < 2:
        return

    action = split_data[0]
    raw_item_id = split_data[1]

    # Validate item ID
    try:
        item_id = int(raw_item_id)
    except Exception:
        try:
            await query.edit_message_caption(caption="⚠️ Invalid item ID.")
        except Exception:
            pass
        return

    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == item_id).first()
    except Exception:
        submission = None

    if not submission:
        try:
            await query.edit_message_caption(caption="⚠️ Submission not found.")
        except Exception:
            pass
        db.close()
        return

    # Admin permission check
    if query.from_user.id != OWNER_ID and query.from_user.id not in ADMINS:
        await query.answer("🚫 Only the owner or an admin can approve/reject.", show_alert=True)
        db.close()
        return

    # Prevent double approval/rejection
    if submission.status in ("approved", "rejected"):
        await query.answer(f"⚠️ This item is already {submission.status}!", show_alert=True)
        db.close()
        return

    type_name = getattr(submission, "type", "item").capitalize()
    status_text = "✅ <b>Approved</b>" if action == "approve" else "❌ <b>Rejected</b>"

    final_caption = (
        f"📩 <b>{type_name} Submission</b>\n\n"
        f"🆔 <b>Item ID:</b> <code>{getattr(submission, 'id', 'N/A')}</code>\n"
        f"👤 <b>Name:</b> {getattr(submission, 'user_name', 'N/A')}\n"
        f"🔗 <b>Username:</b> {getattr(submission, 'username', 'N/A')}\n"
        f"🎬 <b>Anime:</b> {getattr(submission, 'anime_name', 'N/A')}\n"
        f"💞 <b>{type_name}:</b> {getattr(submission, 'waifu_name', 'N/A')}\n"
        f"💎 <b>Rarity:</b> {getattr(submission, 'rarity_name', 'N/A')} {getattr(submission, 'rarity', '')}\n"
        f"💰 Base Bid: {getattr(submission, 'base_bid', 0)}\n\n"
        f"🏷️ <b>Tag:</b> {getattr(submission, 'optional_tag', 'N/A')}\n"
        f"⏰ <b>Submitted:</b> {getattr(submission, 'submitted_time', datetime.now()).strftime('%d %B %Y • %I:%M %p')}"
    )

    post_link = None

    # ===== APPROVE FLOW =====
    if action == "approve":
        submission.status = "approved"
        db.commit() # Save the status update

        rarity_text = f"{getattr(submission, 'rarity', '')}𝗥𝗔𝗥𝗜𝗧𝗬: {getattr(submission, 'rarity_name', '')}"
        new_caption = (
            f"🆔 Item ID: {item_id}\n"
            f"🎬 Anime name: {getattr(submission, 'anime_name', '')}\n"
            f"💞 {type_name} name: {getattr(submission, 'waifu_name', '')}\n"
            f"{rarity_text}\n\n"
            f"💰 Base Bid: {getattr(submission, 'base_bid', 0)}\n\n"
        )
        if getattr(submission, "optional_tag", None) and getattr(submission, "optional_tag") != "—":
            new_caption += str(getattr(submission, "optional_tag"))

        sent_msg = None
        group_msg = None
        group_post_link = None

        # === Step 1: Send to group (no button) and pin ===
        # === Step 1: Send to group (no button) and pin ===
        try:
            group_msg = await context.bot.send_photo(
                chat_id=int(GROUP_ID),
                photo=str(getattr(submission, "file_id")),
                caption=str(new_caption),
                parse_mode="HTML",
            )
        
            # ✅ Save group message details in DB
            submission.group_message_id= group_msg.message_id
            db.commit()  # save immediately so it's not lost on errors later
        
            # Pin message
            await context.bot.pin_chat_message(chat_id=int(GROUP_ID), message_id=group_msg.message_id)
            # Try to build public group message link
            try:
                group_chat = await context.bot.get_chat(GROUP_ID)
                if getattr(group_chat, "username", None):
                    group_post_link = f"https://t.me/{group_chat.username}/{group_msg.message_id}"
                else:
                    group_post_link = None
            except Exception as e:
                print(f"[Error building group link] {e}")
                group_post_link = None

            # Schedule unpin after 3 days
            if isinstance(context.job_queue, JobQueue):
                context.job_queue.run_once(
                    unpin_after_delay,
                    when=timedelta(days=3),
                    data={"chat_id": GROUP_ID, "message_id": group_msg.message_id},
                    name=f"unpin_{group_msg.message_id}",
                )

        except Exception as e:
            print(f"[Error sending/pinning in group] {e}")

        # === Step 2: Send to channel with bid button ===
        try:
            # Button redirects to pinned group post (if public), or fallback deep link
            bid_url = group_post_link if group_post_link else f"{GROUP_URL}?start=bid_{item_id}"

            bid_keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("💸 Bid Now", url=bid_url)]]
            )

            sent_msg = await context.bot.send_photo(
                chat_id=int(CHANNEL_ID),
                photo=str(getattr(submission, "file_id")),
                caption=str(new_caption),
                parse_mode="HTML",
                reply_markup=bid_keyboard,
            )
        except Exception as e:
            print(f"[Error sending to channel] {e}")

        # === Step 3: Save info in DB ===
        if sent_msg:
            submission.channel_id = CHANNEL_ID
            submission.channel_message_id = sent_msg.message_id
            submission.expires_at = datetime.utcnow() + timedelta(days=3)
            submission.is_expired = False
            submission.status = "approved"
            db.commit()

        # === Step 4: Build channel post link ===
        try:
            channel_chat = await context.bot.get_chat(CHANNEL_ID)
            if getattr(channel_chat, "username", None) and sent_msg:
                post_link = f"https://t.me/{channel_chat.username}/{sent_msg.message_id}"
            else:
                post_link = None
        except Exception as e:
            print(f"[Error building channel post link] {e}")
            post_link = None

        # === Step 5: Notify user ===
        try:
            user_chat_id = int(getattr(submission, "user_id"))
            user_caption = (
                f"🎉 <b>Your {type_name} has been approved!</b>\n\n"
                f"💎 <b>Rarity:</b> {getattr(submission, 'rarity_name')} {getattr(submission, 'rarity')}\n"
                f"💞 <b>Name:</b> {getattr(submission, 'waifu_name')}\n"
                f"🎬 <b>Anime:</b> {getattr(submission, 'anime_name')}"
            )

            await context.bot.send_photo(
                chat_id=user_chat_id,
                photo=str(getattr(submission, "file_id")),
                caption=user_caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("👉 View Post", url=post_link)]]
                ) if post_link else None,
            )

        except Exception as e:
            print(f"[Error notifying user] {e}")
    # ===== REJECT FLOW =====
    else:
        submission.status = "rejected"
        db.commit()
        try:
            caption = (
                f"❌ <b>Your {type_name} submission was rejected.</b>\n\n"
                f"🎬 <b>Anime:</b> {getattr(submission, 'anime_name', 'N/A')}\n"
                f"💞 <b>{type_name}:</b> {getattr(submission, 'waifu_name', 'N/A')}\n"
                f"💎 <b>Rarity:</b> {getattr(submission, 'rarity_name', 'N/A')} {getattr(submission, 'rarity', '')}\n"
            )
            if getattr(submission, "optional_tag", None) and getattr(submission, "optional_tag") != "—":
                caption += f"🏷️ <b>Tag:</b> {getattr(submission, 'optional_tag')}\n"
            caption += "\nPlease review and try again!"

            await context.bot.send_photo(
                chat_id=int(getattr(submission, "user_id")),
                photo=str(getattr(submission, "file_id")),
                caption=caption,
                parse_mode="HTML",
            )
        except Exception as e:
            print(f"[Error sending rejection notice] {e}")

    db.close()

    # Update admin caption
    final_caption += f"\n\n{status_text}"
    try:
        await query.edit_message_caption(caption=final_caption, parse_mode="HTML")
    except Exception:
        pass


# ====== HANDLERS LIST FOR approval_handler.py ======
approval_handlers = [
    CallbackQueryHandler(approval_handler, pattern="^(approve|reject)_"),
]