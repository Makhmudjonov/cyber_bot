import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes,
    ConversationHandler, filters
)
from apps.models import Team, Player
import nest_asyncio
from asgiref.sync import sync_to_async


TEAM_NAME, LEADER_NAME, LEADER_PHONE, RESERVE_PHONE, PLAYER_NAME, PLAYER_FACULTY, PLAYER_COURSE, CONFIRM = range(8)

FACULTY_CHOICES = {
    "IT": "Informatika texnologiyalari",
    "ENG": "Muhandislik",
    "MED": "Tibbiyot"
}
COURSE_CHOICES = {
    "1-kurs": "1-kurs",
    "2-kurs": "2-kurs",
    "3-kurs": "3-kurs",
    "4-kurs": "4-kurs",
    "5-kurs": "5-kurs",
    "6-kurs": "6-kurs",
}

team_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Jamoa nomini kiriting:")
    return TEAM_NAME

async def get_team_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    team_data[update.effective_chat.id] = {
        "name": update.message.text,
        "players": [],
        "player_index": 1,
    }
    await update.message.reply_text("Sardorning to‘liq ismini kiriting:")
    return LEADER_NAME

async def get_leader_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    team_data[update.effective_chat.id]["leader_full_name"] = update.message.text
    await update.message.reply_text("Sardorning telefon raqamini kiriting:")
    return LEADER_PHONE

async def get_leader_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    team_data[update.effective_chat.id]["leader_phone"] = update.message.text
    await update.message.reply_text("Zahira raqam kiriting (ixtiyoriy, bo‘sh qoldirsangiz ham bo‘ladi):")
    return RESERVE_PHONE

async def get_reserve_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    team_data[update.effective_chat.id]["reserve_phone"] = update.message.text
    await update.message.reply_text("1-o‘yinchining to‘liq ismini kiriting:")
    return PLAYER_NAME

async def get_player_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    player = {"full_name": update.message.text}
    team_data[chat_id]["current_player"] = player

    markup = ReplyKeyboardMarkup([[v] for v in FACULTY_CHOICES.values()], one_time_keyboard=True)
    await update.message.reply_text("Fakultetni tanlang:", reply_markup=markup)
    return PLAYER_FACULTY

async def get_player_faculty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    faculty_name = update.message.text
    faculty_code = next((k for k, v in FACULTY_CHOICES.items() if v == faculty_name), None)
    if not faculty_code:
        await update.message.reply_text("Noto‘g‘ri fakultet. Qaytadan tanlang.")
        return PLAYER_FACULTY

    team_data[chat_id]["current_player"]["faculty"] = faculty_code
    markup = ReplyKeyboardMarkup([[k] for k in COURSE_CHOICES.keys()], one_time_keyboard=True)
    await update.message.reply_text("Kursni tanlang:", reply_markup=markup)
    return PLAYER_COURSE

async def get_player_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    player = team_data[chat_id]["current_player"]
    player["course"] = update.message.text
    player["is_reserve"] = (team_data[chat_id]["player_index"] == 6)
    team_data[chat_id]["players"].append(player)

    if team_data[chat_id]["player_index"] < 6:
        team_data[chat_id]["player_index"] += 1
        await update.message.reply_text(
            f"{team_data[chat_id]['player_index']}-o‘yinchining to‘liq ismini kiriting:",
            reply_markup=ReplyKeyboardRemove()
        )
        return PLAYER_NAME
    else:
        summary = f"✅ Jamoa: {team_data[chat_id]['name']}\n"
        summary += f"👤 Sardor: {team_data[chat_id]['leader_full_name']} ({team_data[chat_id]['leader_phone']})\n"
        summary += f"📞 Zahira raqam: {team_data[chat_id]['reserve_phone']}\n"
        summary += f"\n🧍‍♂️ O‘yinchilar:\n"
        for idx, p in enumerate(team_data[chat_id]["players"], start=1):
            summary += f"{idx}. {p['full_name']} | {FACULTY_CHOICES[p['faculty']]} | {p['course']}-kurs"
            if p['is_reserve']:
                summary += " (Zahira)"
            summary += "\n"
        await update.message.reply_text(summary + "\nTasdiqlaysizmi? (ha/yo‘q)")
        return CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if update.message.text.lower() == "ha":
        data = team_data[chat_id]

        # Teamni yaratish (leader hozircha None)
        team = await sync_to_async(Team.objects.create)(
            name=data["name"],
            leader_phone=data["leader_phone"],
            reserve_phone=data["reserve_phone"]
        )

        leader_player = None
        for p in data["players"]:
            player = await sync_to_async(Player.objects.create)(
                team=team,
                full_name=p["full_name"],
                faculty=p["faculty"],
                course_number = int(p["course"].split("-")[0]),
                is_reserve=p["is_reserve"]
            )

            if not p["is_reserve"] and p["full_name"] == data["leader_full_name"]:
                leader_player = player

        if leader_player:
            team.leader = leader_player
            await sync_to_async(team.save)()

        await update.message.reply_text("✅ Jamoa muvaffaqiyatli ro‘yxatdan o‘tkazildi!", reply_markup=ReplyKeyboardRemove())
        team_data.pop(chat_id, None)
        return ConversationHandler.END
    elif update.message.text.lower() == "yo‘q":
        await update.message.reply_text("❌ Ro‘yxatdan o‘tkazish bekor qilindi.", reply_markup=ReplyKeyboardRemove())
        team_data.pop(chat_id, None)
        return ConversationHandler.END
    else:
        await update.message.reply_text("ha yoki yo‘q dan birini yuboring", reply_markup=ReplyKeyboardRemove())
        return CONFIRM

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    team_data.pop(update.effective_chat.id, None)
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def run_bot():
    import nest_asyncio
    nest_asyncio.apply()

    async def main():
        app = ApplicationBuilder().token("8208998249:AAEuEwB-2Q3xAtAEl3YG1DE53QB-EHbZzxA").build()

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                TEAM_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_team_name)],
                LEADER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_leader_name)],
                LEADER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_leader_phone)],
                RESERVE_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_reserve_phone)],
                PLAYER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_player_name)],
                PLAYER_FACULTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_player_faculty)],
                PLAYER_COURSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_player_course)],
                CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )

        app.add_handler(conv_handler)

        print("🏁 Bot ishga tushdi...")
        await app.run_polling()

    asyncio.run(main())

