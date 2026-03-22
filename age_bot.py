import os
import logging
from datetime import datetime
from calendar import monthrange
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, filters, ContextTypes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 1221035175  # VKV Nalbari Admin

# Conversation state
WAITING_FOR_DOB = 1

# ── Helpers ──────────────────────────────────────────────────────────────────

def parse_date(text):
    try:
        return datetime.strptime(text.strip(), "%d-%m-%Y")
    except ValueError:
        return None

def calculate_age(dob: datetime, as_of: datetime):
    years  = as_of.year  - dob.year
    months = as_of.month - dob.month
    days   = as_of.day   - dob.day

    if days < 0:
        months -= 1
        prev_month = as_of.month - 1 if as_of.month > 1 else 12
        prev_year  = as_of.year      if as_of.month > 1 else as_of.year - 1
        days += monthrange(prev_year, prev_month)[1]

    if months < 0:
        years  -= 1
        months += 12

    return years, months, days

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Calculate Student's Age", callback_data="ask_dob")]
    ])

# ── Handlers ─────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🙏 *Namaskar!*\n\n"
        "Welcome to the *VKV Nalbari Age Calculator Bot* 🎓\n"
        "_Vivekananda Kendra Vidyalaya, Nalbari_\n\n"
        "This bot calculates age as on *31 March 2026* — useful for *new admissions*.\n\n"
        "Tap the button below to get started 👇"
    )
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_keyboard())

async def button_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "📅 Please enter the *date of birth of the student* in `dd-mm-yyyy` format:\n\n"
        "_Example: 15-08-2010_",
        parse_mode="Markdown"
    )
    return WAITING_FOR_DOB

async def receive_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    dob  = parse_date(text)

    if not dob:
        await update.message.reply_text(
            "❌ Invalid date format. Please enter in `dd-mm-yyyy` format.\n"
            "_Example: 15-08-2010_",
            parse_mode="Markdown"
        )
        return WAITING_FOR_DOB  # ask again

    as_of = datetime(2026, 3, 31)

    if dob > as_of:
        await update.message.reply_text(
            "❌ Date of birth cannot be *after* 31 March 2026. Please check and try again.",
            parse_mode="Markdown"
        )
        return WAITING_FOR_DOB

    years, months, days = calculate_age(dob, as_of)
    total_days = (as_of - dob).days

    response = (
        f"✅ *Age Calculation Result*\n\n"
        f"📅 Date of Birth: *{dob.strftime('%d %B %Y')}*\n"
        f"📆 As on: *31 March 2026*\n\n"
        f"🎂 *Age: {years} years, {months} months, {days} days*\n\n"
        f"📊 That's *{total_days:,} days* of life!"
    )

    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=main_keyboard())

    # Notify admin
    user = update.message.from_user
    username = f"@{user.username}" if user.username else f"{user.first_name} (ID: {user.id})"
    notify = (
        f"📊 *New Age Query*\n\n"
        f"👤 User: {username}\n"
        f"📅 DOB entered: *{dob.strftime('%d %B %Y')}*\n"
        f"🎂 Result: *{years}y {months}m {days}d*"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=notify, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Could not notify admin: {e}")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❎ Cancelled. Tap the button anytime to calculate age again.",
        reply_markup=main_keyboard()
    )
    return ConversationHandler.END

# ── /age command still works too ─────────────────────────────────────────────

async def age_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "❗ Usage: `/age dd-mm-yyyy`\n_Example: `/age 15-08-2010`_",
            parse_mode="Markdown"
        )
        return

    dob = parse_date(args[0])
    if not dob:
        await update.message.reply_text(
            f"❌ Invalid date: `{args[0]}`\nUse `dd-mm-yyyy` format.",
            parse_mode="Markdown"
        )
        return

    as_of = datetime(2026, 3, 31)
    if dob > as_of:
        await update.message.reply_text("❌ Date of birth is after 31 March 2026.", parse_mode="Markdown")
        return

    years, months, days = calculate_age(dob, as_of)
    total_days = (as_of - dob).days

    await update.message.reply_text(
        f"✅ *Age Calculation Result*\n\n"
        f"📅 Date of Birth: *{dob.strftime('%d %B %Y')}*\n"
        f"📆 As on: *31 March 2026*\n\n"
        f"🎂 *Age: {years} years, {months} months, {days} days*\n\n"
        f"📊 That's *{total_days:,} days* of life!",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

    # Notify admin
    user = update.message.from_user
    username = f"@{user.username}" if user.username else f"{user.first_name} (ID: {user.id})"
    notify = (
        f"📊 *New Age Query*\n\n"
        f"👤 User: {username}\n"
        f"📅 DOB entered: *{dob.strftime('%d %B %Y')}*\n"
        f"🎂 Result: *{years}y {months}m {days}d*"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=notify, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Could not notify admin: {e}")

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable not set!")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_pressed, pattern="^ask_dob$")],
        states={
            WAITING_FOR_DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_dob)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("age", age_command))
    app.add_handler(conv_handler)

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
