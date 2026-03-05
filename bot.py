import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, time, timedelta
import os

# Bot token (set in Render as environment variable)
TOKEN = os.environ.get("TOKEN")  

# Goal and earnings
GOAL = 3500
START_AMOUNT = 618.75  # Updated: mini job + 4 full-time days
HOURLY_RATE = 9.375

# Work shift
SHIFT_START = time(7, 0)
SHIFT_END = time(15, 30)

# Start date for full-time job counting
START_DATE = datetime(2026, 3, 2)

def calculate_earned():
    now = datetime.now()
    earned = START_AMOUNT

    # Count all weekdays since START_DATE
    total_days = (now.date() - START_DATE.date()).days + 1
    for i in range(total_days):
        day = START_DATE + timedelta(days=i)
        if day.weekday() < 5:  # Monday=0 … Friday=4
            # Past days: full day
            if day.date() < now.date():
                earned += HOURLY_RATE * 8.5
            # Today: partial based on current time
            elif day.date() == now.date():
                if now.time() >= SHIFT_END:
                    earned += HOURLY_RATE * 8.5
                elif now.time() > SHIFT_START:
                    hours_today = (datetime.combine(now.date(), now.time()) - datetime.combine(now.date(), SHIFT_START)).total_seconds() / 3600
                    earned += hours_today * HOURLY_RATE

    return min(earned, GOAL)

def generate_pie_chart(earned):
    remaining = GOAL - earned
    plt.figure()
    plt.pie(
        [earned, remaining],
        labels=["Earned", "Remaining"],
        colors=["blue", "white"],
        autopct='%1.1f%%',
        startangle=90
    )
    plt.title(f"€{earned:.2f} / €{GOAL}")
    plt.savefig("progress.png")
    plt.close()

async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    earned = calculate_earned()
    generate_pie_chart(earned)
    await update.message.reply_photo(
        photo=open("progress.png", "rb"),
        caption=f"€{earned:.2f} of €{GOAL}"
    )

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("progress", progress))

app.run_polling()