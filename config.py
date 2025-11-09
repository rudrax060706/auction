from telegram.helpers import escape_markdown
# config.py
BOT_TOKEN = "8596519637:AAGw6uUdJtpInopkq7W2oHiI3Zzm0JjTa_4" 
BOT_USERNAME="HxH_AuctionBot"
# Your log group ID (use a negative ID for supergroups)
LOG_GROUP_ID = -1002641745655     
OWNER_ID=7562158122
GROUP_ID=-1002677839849
CHANNEL_ID = -1002875695805
ADMINS = [6143218334, 7745310823]  # other admins (exclude owner if you want)
# ====== DATABASE CONFIG ======
# Option 1: Local SQLite (no MySQL server required)
# DATABASE_URL = "sqlite:///auction_bot.db"

# Option 2: MySQL (for VPS, Render, or other deployment)
DATABASE_URL = "mysql+mysqlconnector://root:PASSWORD@localhost:3306/auction_bot"
# Replace PASSWORD with your actual MySQL root password
# Public links
GROUP_URL = "https://t.me/ThePhantom_Troupe"  # Link opened by 🧿 Group button
CHANNEL_URL ="https://t.me/ThePhantom_Troupe_Auction"   # Link opened by 💫 Channel button
SUPPORT_GROUP_URL="https://t.me/ThePhantom_Troupe"
# Use Telegram's file_id (not file path)
WELCOME_VIDEO_ID = "BAACAgUAAxkBAAMHaQOJgeQ6Cj5349F03nC9Gvt4o4IAAmAYAAIWVBlUhSpI7yXDkvUeBA"  

WELCOME_MESSAGE_RAW = (
    "💎 Gʀᴇᴇᴛɪɴɢs, I'ᴍ ˹Tʜᴇ Pʜᴀɴᴛᴏᴍ Tʀᴏᴜᴘᴇ Aᴜᴄᴛɪᴏɴ Bᴏᴛ˼ 🕊️ ɴɪᴄᴇ ᴛᴏ ᴍᴇᴇᴛ ʏᴏᴜ!\n"
    "━━━━━━━▧▣▧━━━━━━━\n"
    "⦾ Tᴏ ᴜsᴇ ᴍᴇ: Jᴏɪɴ ᴛʜᴇ ɢʀᴏᴜᴘ ᴀɴᴅ ᴄʜᴀɴɴᴇʟ\n"
    "⦾ Wʜᴀᴛ I ᴅᴏ: I ʜᴏsᴛ ʟɪᴠᴇ ᴀᴜᴄᴛɪᴏɴs ᴡʜᴇʀᴇ ᴜsᴇʀs ʙɪᴅ ᴛᴏ ᴡɪɴ Hᴜsʙᴀɴᴅᴏ ᴀɴᴅ Wᴀɪғᴜs\n"
    "⦾ Tʜɪɴᴋ ғᴀsᴛ, ʙɪᴅ ғᴀsᴛᴇʀ — ᴛʀᴇᴀsᴜʀᴇs ᴅᴏɴ’ᴛ ᴡᴀɪᴛ!\n"
    "━━━━━━━▧▣▧━━━━━━━"
)

# Escape entire caption for MarkdownV2
WELCOME_MESSAGE = escape_markdown(WELCOME_MESSAGE_RAW, version=2)
# config.py

RARITY_MAP = {
    "🔵": "Common",
    "🔴": "Medium",
    "🟠": "Rare",
    "🟡": "Legendary",
    "💮": "Exclusive",
    "🔮": "Limited",
    "🎐": "Celestial",
}   