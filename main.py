import json
import random
import os  # Added for environment variables
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# Configuration - NOW SECURE
BOT_TOKEN = os.environ['BOT_TOKEN']  # Set in hosting secrets
ADMIN_ID = int(os.environ['ADMIN_ID'])  # Set in hosting secrets
TELEGRAM_CHANNEL = "https://t.me/sastilootdealss"

# Load data
try:
    with open("data.json", "r") as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    data = {
        "current_round": 1,
        "winners": {},
        "used_vouchers": {},
        "vouchers": {
            "₹10": ["TEST10A", "TEST10B"],
            "₹15": ["TEST15A", "TEST15B"],
            "₹20": ["TEST20A"],
            "₹50": ["TEST50A"]
        }
    }

def save_data():
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        
        try:
            member = await context.bot.get_chat_member(chat_id="@sastilootdealss", user_id=int(user_id))
            if member.status not in ["member", "administrator", "creator"]:
                raise Exception("Not a member")
        except Exception as e:
            keyboard = [[InlineKeyboardButton("📢 CLICK HERE TO JOIN", url=TELEGRAM_CHANNEL)]]
            await update.message.reply_text(
                "🔒 You Must Join Our Channel First To Participate!\n\n"
                "👉 Join @sastilootdealss then try /start again",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        if user_id in data["winners"]:
            await update.message.reply_text("⚠️ You have already played this round!")
            return

        all_prizes_claimed = all(not codes for codes in data["vouchers"].values())
        if all_prizes_claimed:
            prize = "Better Luck Next Time"
        else:
            prize = random.choices(
                ["Better Luck Next Time"] + [p for p in data["vouchers"] if data["vouchers"][p]],
                weights=[80, 5, 5, 5, 5],
                k=1
            )[0]

        data["winners"][user_id] = prize
        save_data()

        if prize == "Better Luck Next Time":
            keyboard = [[InlineKeyboardButton("📢 Support Us | Share Channel", url=TELEGRAM_CHANNEL)]]
            await update.message.reply_text(
                "😢 Better luck next time!\n\n"
                "Stay tuned for the next round!\n\n"
                "🙌 Stay & Share with friends!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            keyboard = [
                [InlineKeyboardButton("📢 Share Channel", url=TELEGRAM_CHANNEL)],
                [InlineKeyboardButton("🎁 CLAIM PRIZE", callback_data=f"claim:{user_id}")]
            ]
            await update.message.reply_text(
                f"🎉 You won {prize} Amazon Pay Voucher!\n\n"
                "🙌 Support our channel to keep contests running!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    except Exception as e:
        print(f"Error in start: {e}")
        await update.message.reply_text("⚠️ An error occurred. Please try again.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user_id = str(query.from_user.id)
        action, callback_user_id = query.data.split(":")

        if user_id != callback_user_id:
            await query.edit_message_text("⚠️ This button isn't for you!")
            return

        prize = data["winners"].get(user_id)
        if not prize or prize == "Better Luck Next Time":
            await query.edit_message_text("⚠️ No voucher to claim!")
            return

        if not data["vouchers"].get(prize):
            await query.edit_message_text("⚠️ Sorry, all vouchers for this prize are claimed!")
            return

        code = data["vouchers"][prize].pop(0)
        amazon_url = f"https://www.amazon.in/gp/css/gc/payment?claimCode={code}&actionType=add"
        data["used_vouchers"][user_id] = code
        save_data()

        await query.edit_message_text(
            f"🎉 Here's your {prize} Amazon Pay Code:\n\n"
            f"💳 `{code}`\n\n"
            "Click below to redeem instantly:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔥 REDEEM NOW", url=amazon_url)]
            ])
        )

    except Exception as e:
        print(f"Error in callback: {e}")
        await query.edit_message_text("⚠️ An error occurred. Please try /start again.")

async def admin_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("⛔ Admin only!")
            return

        data["current_round"] += 1
        data["winners"] = {}
        data["used_vouchers"] = {}
        data["vouchers"] = {
            "₹10": ["TEST10A", "TEST10B"],
            "₹15": ["TEST15A", "TEST15B"],
            "₹20": ["TEST20A"],
            "₹50": ["TEST50A"]
        }
        save_data()
        await update.message.reply_text(f"✅ Round {data['current_round']} started!")
    except Exception as e:
        print(f"Error in reset: {e}")
        await update.message.reply_text("⚠️ Error resetting contest.")

async def end_contest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Admin only!")
        return
    
    for prize in data["vouchers"]:
        data["vouchers"][prize] = []
    save_data()
    await update.message.reply_text("✅ Contest manually ended! Spins will now return 'Better Luck Next Time'.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback, pattern=r"^claim:\d+"))
    app.add_handler(CommandHandler("reset", admin_reset))
    app.add_handler(CommandHandler("end", end_contest))
    
    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()