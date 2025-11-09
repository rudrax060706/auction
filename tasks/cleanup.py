import asyncio
from datetime import datetime
from telegram import InlineKeyboardMarkup
from telegram.error import BadRequest
from utils.database import SessionLocal
from models.tables import Submission
from config import CHANNEL_ID


async def remove_expired_bids(bot):
    """Periodically remove '💸 Bid Now' buttons from expired posts."""
    while True:
        db = SessionLocal()
        now = datetime.utcnow()

        expired_items = (
            db.query(Submission)
            .filter(Submission.expires_at <= now, Submission.is_expired == False)
            .all()
        )

        for item in expired_items:
            try:
                await bot.edit_message_reply_markup(
                    chat_id=CHANNEL_ID,
                    message_id=item.channel_message_id,
                    reply_markup=InlineKeyboardMarkup([]),
                )
                item.is_expired = True  # type: ignore[attr-defined]
                db.commit()
            except BadRequest:
                # Message may already be deleted or uneditable
                item.is_expired = True  # type: ignore[attr-defined]
                db.commit()

        db.close()
        await asyncio.sleep(3600)  # check every hour