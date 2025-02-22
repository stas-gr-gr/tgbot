import logging
import requests
import pandas as pd
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext
)

# === Читаем переменные окружения ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_DRIVE_FILE_URL = os.getenv("GOOGLE_DRIVE_FILE_URL")

# === Логирование (чтобы видеть ошибки) ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# === Функция старта ===
async def start(update: Update, context: CallbackContext) -> None:
    """Отправляет приветственное сообщение"""
    await update.message.reply_text(
        "Привет! Я бот для учета финансов. Доступные команды:\n"
        "/обновить - загрузить актуальные данные\n"
        "/финансы - посмотреть отчет по финансам\n"
        "/период <дата_начала> <дата_конца> - данные за период\n"
        "/проект <название> - отчет по проекту"
    )

# === Функция обновления данных ===
async def update_data(update: Update, context: CallbackContext) -> None:
    """Скачивает и обновляет файл данных из Google Drive"""
    await update.message.reply_text("Обновляю данные...")
    response = requests.get(GOOGLE_DRIVE_FILE_URL)
    
    if response.status_code == 200:
        with open("data.xlsx", "wb") as file:
            file.write(response.content)
        await update.message.reply_text("✅ Данные обновлены!")
    else:
        await update.message.reply_text("❌ Ошибка обновления. Проверьте ссылку.")

# === Функция чтения Excel-файла ===
def read_data():
    """Считывает Excel-файл и возвращает DataFrame"""
    try:
        df = pd.read_excel("data.xlsx")
        return df
    except Exception as e:
        logging.error(f"Ошибка чтения файла: {e}")
        return None

# === Функция отчета по финансам ===
async def finances(update: Update, context: CallbackContext) -> None:
    """Отображает общую информацию по финансам"""
    df = read_data()
    if df is None:
        await update.message.reply_text("❌ Ошибка загрузки данных.")
        return
    
    try:
        total_profit = df["Чистая прибыль"].sum()
        total_sales = df["Сумма к перечислению"].sum()
        total_expenses = df["Расходы"].sum()
        
        await update.message.reply_text(
            f"📊 Финансовый отчет:\n"
            f"💰 Чистая прибыль: {total_profit:.2f} ₽\n"
            f"📈 Продажи: {total_sales:.2f} ₽\n"
            f"📉 Расходы: {total_expenses:.2f} ₽"
        )
    except Exception as e:
        logging.error(f"Ошибка обработки данных: {e}")
        await update.message.reply_text("❌ Ошибка обработки данных.")

# === Фильтрация по периоду ===
async def filter_by_period(update: Update, context: CallbackContext) -> None:
    """Выводит отчет по заданному периоду"""
    try:
        start_date, end_date = context.args
        df = read_data()
        if df is None:
            await update.message.reply_text("❌ Ошибка загрузки данных.")
            return
        
        df["Дата"] = pd.to_datetime(df["Дата"])
        mask = (df["Дата"] >= start_date) & (df["Дата"] <= end_date)
        df_filtered = df.loc[mask]

        total_profit = df_filtered["Чистая прибыль"].sum()
        await update.message.reply_text(
            f"📅 Данные за период {start_date} - {end_date}:\n"
            f"💰 Чистая прибыль: {total_profit:.2f} ₽"
        )
    except Exception as e:
        logging.error(f"Ошибка обработки периода: {e}")
        await update.message.reply_text("❌ Неправильный формат. Введите: /период ДД.ММ.ГГГГ ДД.ММ.ГГГГ")

# === Фильтрация по проекту ===
async def filter_by_project(update: Update, context: CallbackContext) -> None:
    """Выводит отчет по заданному проекту"""
    try:
        project_name = " ".join(context.args)
        df = read_data()
        if df is None:
            await update.message.reply_text("❌ Ошибка загрузки данных.")
            return
        
        df_filtered = df[df["Проект"] == project_name]

        if df_filtered.empty:
            await update.message.reply_text(f"❌ Данных по проекту {project_name} нет.")
            return
        
        total_profit = df_filtered["Чистая прибыль"].sum()
        await update.message.reply_text(
            f"📊 Данные по проекту {project_name}:\n"
            f"💰 Чистая прибыль: {total_profit:.2f} ₽"
        )
    except Exception as e:
        logging.error(f"Ошибка обработки проекта: {e}")
        await update.message.reply_text("❌ Неправильный формат. Введите: /проект <название проекта>")

# === Основная функция ===
def main():
    """Запуск бота"""
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Добавляем команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("обновить", update_data))
    app.add_handler(CommandHandler("финансы", finances))
    app.add_handler(CommandHandler("период", filter_by_period))
    app.add_handler(CommandHandler("проект", filter_by_project))

    # Запуск бота
    logging.info("Бот запущен...")
    app.run_polling()

if __name__ == "_main_":
    main()
