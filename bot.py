import os
import io
from datetime import datetime, time, timedelta
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- Constants ---
HOURLY_RATE = 9.375          # EUR per hour (1500 / 160)
MINI_EARNED = 300.0          # EUR from mini-job
FULL_DAYS_WORKED = 4         # full-time days already completed
FULL_DAY_HOURS = 8           # hours per workday
GOAL_TOTAL = 3500.0          # EUR total goal

# Work schedule
WORK_START = time(7, 0)
WORK_END = time(15, 30)
WORK_HOURS_PER_DAY = (
    (datetime.combine(datetime.min, WORK_END) - datetime.combine(datetime.min, WORK_START)).seconds / 3600.0
)
WORK_DAYS = range(0, 5)      # Monday=0 .. Friday=4

# Reference point: the date+time when FULL_DAYS_WORKED days were completed.
# Earnings from live tracking start AFTER this point.
# Adjust this to the Monday after the 4th completed day.
TRACKING_START = datetime(2025, 3, 3, 7, 0)  # adjust as needed

FULL_TIME_BASE = FULL_DAYS_WORKED * FULL_DAY_HOURS * HOURLY_RATE


def _work_seconds_on_day(day_date, clamp_start=None, clamp_end=None) -> float:
    if day_date.weekday() not in WORK_DAYS:
        return 0.0
    ds = datetime.combine(day_date, WORK_START)
    de = datetime.combine(day_date, WORK_END)
    if clamp_start:
        ds = max(ds, clamp_start)
    if clamp_end:
        de = min(de, clamp_end)
    return max((de - ds).total_seconds(), 0.0)


def work_hours_since_tracking_start(now: datetime) -> float:
    if now <= TRACKING_START:
        return 0.0

    start_date = TRACKING_START.date()
    end_date = now.date()

    if start_date == end_date:
        return _work_seconds_on_day(start_date, TRACKING_START, now) / 3600.0

    total = _work_seconds_on_day(start_date, clamp_start=TRACKING_START)
    total += _work_seconds_on_day(end_date, clamp_end=now)

    first_full = start_date + timedelta(days=1)
    last_full = end_date - timedelta(days=1)
    if first_full <= last_full:
        span = (last_full - first_full).days + 1
        full_weeks, leftover = divmod(span, 7)
        workdays = full_weeks * 5
        for i in range(leftover):
            if (first_full + timedelta(days=full_weeks * 7 + i)).weekday() in WORK_DAYS:
                workdays += 1
        total += workdays * WORK_HOURS_PER_DAY * 3600

    return total / 3600.0


def generate_chart(earned: float) -> io.BytesIO:
    remaining = max(GOAL_TOTAL - earned, 0)

    sizes = [earned, remaining]
    colors = ["#2196F3", "#FFFFFF"]
    labels = [f"Earned\n{earned:,.2f} EUR", f"Remaining\n{remaining:,.2f} EUR"]

    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops={"edgecolor": "#333333", "linewidth": 1.5},
    )
    for t in autotexts:
        t.set_fontsize(12)
        t.set_fontweight("bold")
    for t in texts:
        t.set_fontsize(11)

    ax.set_title("BlueSliceBot Progress", fontsize=16, fontweight="bold", pad=20)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now()
    live_hours = work_hours_since_tracking_start(now)
    earned = MINI_EARNED + FULL_TIME_BASE + live_hours * HOURLY_RATE
    remaining = max(GOAL_TOTAL - earned, 0)

    buf = generate_chart(earned)
    caption = (
        f"Earned: {earned:,.2f} EUR / {GOAL_TOTAL:,.2f} EUR\n"
        f"Remaining: {remaining:,.2f} EUR\n"
        f"Progress: {earned / GOAL_TOTAL * 100:.1f}%"
    )
    await update.message.reply_photo(photo=buf, caption=caption)


async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now()
    live_hours = work_hours_since_tracking_start(now)
    earned = MINI_EARNED + FULL_TIME_BASE + live_hours * HOURLY_RATE
    remaining = max(GOAL_TOTAL - earned, 0)

    text = (
        f"--- BlueSliceBot Summary ---\n"
        f"Mini-job earned:    {MINI_EARNED:,.2f} EUR\n"
        f"Full-time base:     {FULL_TIME_BASE:,.2f} EUR\n"
        f"Live work hours:    {live_hours:.2f} h\n"
        f"Live earnings:      {live_hours * HOURLY_RATE:,.2f} EUR\n"
        f"-----------------------------\n"
        f"Total earned:       {earned:,.2f} EUR\n"
        f"Goal:               {GOAL_TOTAL:,.2f} EUR\n"
        f"Remaining:          {remaining:,.2f} EUR\n"
        f"Progress:           {earned / GOAL_TOTAL * 100:.1f}%"
    )
    await update.message.reply_text(text)


def main() -> None:
    token = os.environ["TOKEN"]
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("progress", progress))
    app.add_handler(CommandHandler("summary", summary))
    print("Polling started...")
    app.run_polling()


if __name__ == "__main__":
    main()
