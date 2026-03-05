import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime, time

# Read Telegram bot token from environment
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise ValueError("No TOKEN found in environment variables.")

# ---- CONFIG ----
HOURLY_RATE = 1500 / 40  # full-time monthly net / weekly hours (adjust if needed)
MINI_EARNED = 300  # already earned from minijob
FULL_DAYS_WORKED = 4  # full-time days worked
GOAL_TOTAL = 500 + 1000 + 1000 + 1000  # mom + Barcelona + snowboarding + safety net

# Calculate current earned
FULL_DAY_HOURS = 8  # your workday hours
FULL_TIME_EARNED = HOURLY_RATE * FULL_DAY_HOURS * FULL_DAYS_WORKED
CURRENT_EARNED = MINI_EARNED + FULL_TIME_EARNED

# ---- BOT HANDLER ----
async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Generate pie chart
    earned = CURRENT_EARNED
    remaining = max(GOAL_TOTAL - earned, 0)
    fig, ax = plt.subplots()
    ax.pie([earned, remaining], labels=["Earned", "Remaining"], colors=["blue", "white"], startangle=90, autopct='%1.0f%%')
    ax.set_title("BlueSliceBot Progress")
    # Save to in-memory buffer
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)
    await update.message.reply_photo(photo=buf)

# ---- MAIN ----
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("progress", progress))

print("Polling started...")
app.run_polling()
