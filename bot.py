import os
import matplotlib
matplotlib.use('Agg')  # Important for headless servers like Render
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime, time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---- TOKEN ----
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise ValueError("No TOKEN found in environment variables.")

# ---- CONFIG ----
HOURLY_RATE = 1500 / 40  # full-time monthly net / 40h per week
MINI_EARNED = 300  # already earned from minijob
FULL_DAYS_WORKED = 4  # full-time days worked
GOAL_TOTAL = 500 + 1000 + 1000 + 1000  # mom + Barcelona + snowboarding + safety net
FULL_DAY_HOURS = 8  # your daily work hours

# ---- HELPER FUNCTION ----
def calculate_current_earned():
    full_time_earned = HOURLY_RATE * FULL_DAY_HOURS * FULL_DAYS_WORKED
    current_earned = MINI_EARNED + full_time_earned
    return current_earned

def generate_pie_chart(earned, remaining):
    fig, ax = plt.subplots()
    ax.pie([earned, remaining], labels=["Earned", "Remaining"], colors=["blue", "white"], startangle=90, autopct='%1.0f%%')
    ax.set_title("BlueSliceBot Progress")
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)
    return buf

# ---- BOT HANDLER ----
async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    earned = calculate_current_earned()
    remaining = max(GOAL_TOTAL - earned, 0)
    buf = generate_pie_chart(earned, remaining)
    await update.message.reply_photo(photo=buf)

# ---- MAIN ----
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("progress", progress))

print("Polling started...")
app.run_polling()
