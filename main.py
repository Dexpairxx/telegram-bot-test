"""
DeFiLlama Stablecoin Yield Telegram Bot

Features:
- Daily notifications at 9 AM (Vietnam timezone) with top stablecoin pools
- /TopTVL command for on-demand queries
"""
import os
import logging
from datetime import datetime, time
import pytz
import asyncio

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from defillama import get_top_pools_message


# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token - can be overridden by environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN", "8305431317:AAFr-wfK8d2dKvXqXmSGvPJG4Q6vabD6bM8")

# Chat ID for scheduled notifications (set this after getting your chat ID)
# You can get your chat ID by messaging @userinfobot on Telegram
CHAT_ID = os.getenv("CHAT_ID", "5369646620")

# Vietnam timezone
VIETNAM_TZ = pytz.timezone("Asia/Ho_Chi_Minh")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    welcome_message = (
        "👋 Chào mừng bạn đến với DeFiLlama Stablecoin Yield Bot!\n\n"
        "🔔 Bot này sẽ gửi thông báo hàng ngày lúc 9h sáng về top stablecoin pools.\n\n"
        "📝 Các lệnh:\n"
        "• /TopTVL <số lượng> <TVL triệu $> <APR %>\n"
        "  Ví dụ: /TopTVL 25 2 15 → Top 25 pools, TVL > $2M, APR > 15%\n\n"
        "• /help - Xem hướng dẫn\n\n"
        f"💬 Chat ID của bạn: {update.effective_chat.id}\n"
        "(Cần thiết cho scheduled notifications)"
    )
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_message = (
        "📖 HƯỚNG DẪN SỬ DỤNG\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔸 /TopTVL <số lượng> <TVL> <APR>\n"
        "   Tra cứu top stablecoin pools theo điều kiện\n\n"
        "   Tham số:\n"
        "   • Số lượng: Số pools muốn xem (mặc định: 20)\n"
        "   • TVL: TVL tối thiểu (triệu USD, mặc định: 5)\n"
        "   • APR: APR tối thiểu (%, mặc định: 12)\n\n"
        "   Ví dụ:\n"
        "   /TopTVL 25 2 15 → Top 25, TVL > $2M, APR > 15%\n"
        "   /TopTVL 10 → Top 10, TVL > $5M, APR > 12%\n"
        "   /TopTVL → Top 20, TVL > $5M, APR > 12%\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📡 Dữ liệu từ DeFiLlama"
    )
    await update.message.reply_text(help_message)


async def top_tvl_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /TopTVL command with optional parameters."""
    # Default values
    top_n = 20
    min_tvl = 5.0
    min_apr = 12.0
    
    args = context.args
    
    try:
        if len(args) >= 1:
            top_n = int(args[0])
        if len(args) >= 2:
            min_tvl = float(args[1])
        if len(args) >= 3:
            min_apr = float(args[2])
    except ValueError:
        await update.message.reply_text(
            "❌ Tham số không hợp lệ!\n\n"
            "Cú pháp: /TopTVL <số lượng> <TVL triệu $> <APR %>\n"
            "Ví dụ: /TopTVL 25 2 15"
        )
        return
    
    # Validate parameters
    if top_n < 1 or top_n > 100:
        await update.message.reply_text("❌ Số lượng phải từ 1 đến 100")
        return
    if min_tvl < 0:
        await update.message.reply_text("❌ TVL phải là số dương")
        return
    if min_apr < 0:
        await update.message.reply_text("❌ APR phải là số dương")
        return
    
    # Send "typing" action
    await update.message.chat.send_action("typing")
    
    # Get and send the message
    message = get_top_pools_message(
        min_tvl_millions=min_tvl,
        min_apr=min_apr,
        top_n=top_n
    )
    
    # Split message if too long (Telegram limit is 4096 characters)
    if len(message) > 4096:
        for i in range(0, len(message), 4096):
            await update.message.reply_text(message[i:i+4096])
    else:
        await update.message.reply_text(message)


async def send_daily_notification(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send daily notification at 9 AM."""
    chat_id = context.job.chat_id if context.job else CHAT_ID
    
    if not chat_id:
        logger.warning("CHAT_ID not set, skipping daily notification")
        return
    
    logger.info("Sending daily notification...")
    
    message = get_top_pools_message(
        min_tvl_millions=5.0,
        min_apr=12.0,
        top_n=20
    )
    
    try:
        # Split message if too long
        if len(message) > 4096:
            for i in range(0, len(message), 4096):
                await context.bot.send_message(chat_id=chat_id, text=message[i:i+4096])
        else:
            await context.bot.send_message(chat_id=chat_id, text=message)
        logger.info("Daily notification sent successfully")
    except Exception as e:
        logger.error(f"Failed to send daily notification: {e}")


async def post_init(application: Application) -> None:
    """Schedule the daily notification job after bot starts."""
    if not CHAT_ID:
        logger.warning("CHAT_ID not set. Daily notifications disabled.")
        logger.info("Send /start to the bot to get your Chat ID, then set CHAT_ID environment variable.")
        return
    
    # Schedule daily job at 9:00 AM Vietnam time
    job_queue = application.job_queue
    target_time = time(hour=9, minute=0, second=0, tzinfo=VIETNAM_TZ)
    
    job_queue.run_daily(
        send_daily_notification,
        time=target_time,
        chat_id=int(CHAT_ID),
        name="daily_9am_notification"
    )
    logger.info(f"Scheduled daily notification at 9:00 AM Vietnam time for chat_id: {CHAT_ID}")


def main() -> None:
    """Start the bot."""
    logger.info("Starting DeFiLlama Stablecoin Yield Bot...")
    
    # Create the Application
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("TopTVL", top_tvl_command))
    application.add_handler(CommandHandler("toptvl", top_tvl_command))  # Case-insensitive
    
    # Run the bot
    logger.info("Bot is running. Press Ctrl+C to stop.")
    application.run_polling()


if __name__ == "__main__":
    main()



