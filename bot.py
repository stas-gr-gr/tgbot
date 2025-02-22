import logging
import requests
import pandas as pd
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackContext
)

# === Читаем переменные окружения ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_DRIVE_FILE_URL = os.getenv("GOOGLE_DRIVE_FILE_URL")

# === Логирование ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# === Функция старта ===
async def start(update: Update, context: CallbackContext) -> None:
    """Отправляет приветственное сообщение"""
    await update.message.reply_text(
        "Привет! Я бот для учета финансов. Доступные команды:\n"
        "/update - загрузить актуальные данные\n"
        "/finance - посмотреть отчет по финансам\n"
        "/period <дд.мм.гггг> <дд.мм.гггг> - данные за период\n"
        "/project <название> - отчет по проекту"
    )

# === Функция обновления данных ===
async def update_data(update: Update, context: CallbackContext) -> None:
    """Скачивает и обновляет файл данных из Google Drive"""
    await update.message.reply_text("🔄 Обновляю данные...")
    try:
        response = requests.get(GOOGLE_DRIVE_FILE_URL)
        if response.status_code == 200:
            with open("data.xlsx", "wb") as file:
                file.write(response.content)
            await update.message.reply_text("✅ Данные обновлены!")
        else:
            await update.message.reply_text("❌ Ошибка обновления. Проверьте ссылку.")
    except Exception as e:
        logging.error(f"Ошибка обновления данных: {e}")
        await update.message.reply_text("❌ Ошибка загрузки данных.")

# === Функция чтения Excel-файла ===
def read_data():
    """Считывает Excel-файл и возвращает DataFrame"""
    try:
        df = pd.read_excel("data.xlsx", engine="openpyxl")
        return df
    except Exception as e:
        logging.error(f"Ошибка чтения файла: {e}")
        return None

# === Функция отчета по финансам ===
async def finance(update: Update, context: CallbackContext) -> None:
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
async def period(update: Update, context: CallbackContext) -> None:
    """Выводит отчет по заданному периоду"""
    if len(context.args) != 2:
        await update.message.reply_text("❌ Неправильный формат. Введите: /period ДД.ММ.ГГГГ ДД.ММ.ГГГГ")
        return

    try:
        start_date = pd.to_datetime(context.args[0], dayfirst=True)
        end_date = pd.to_datetime(context.args[1], dayfirst=True)

        df = read_data()
        if df is None:
            await update.message.reply_text("❌ Ошибка загрузки данных.")
            return

        if "Дата" not in df.columns:
            await update.message.reply_text("❌ В файле отсутствует колонка 'Дата'.")
            return

        df["Дата"] = pd.to_datetime(df["Дата"], dayfirst=True, errors="coerce")
        mask = (df["Дата"] >= start_date) & (df["Дата"] <= end_date)
        df_filtered = df.loc[mask]

        if df_filtered.empty:
            await update.message.reply_text(f"❌ Нет данных за период {context.args[0]} - {context.args[1]}.")
            return

        total_profit = df_filtered["Чистая прибыль"].sum()
        await update.message.reply_text(
            f"📅 Данные за период {context.args[0]} - {context.args[1]}:\n"
            f"💰 Чистая прибыль: {total_profit:.2f} ₽"
        )
    except Exception as e:
        logging.error(f"Ошибка обработки периода: {e}")
        await update.message.reply_text("❌ Ошибка обработки периода.")

# === Фильтрация по проекту ===
async def project(update: Update, context: CallbackContext) -> None:
    """Выводит отчет по заданному проекту"""
    if len(context.args) == 0:
        await update.message.reply_text("❌ Введите название проекта. Пример: /project Powerrise")
        return

    try:
        project_name = " ".join(context.args)
        df = read_data()
        if df is None:
            await update.message.reply_text("❌ Ошибка загрузки данных.")
            return
        
        if "Проект" not in df.columns:
            await update.message.reply_text("❌ В файле отсутствует колонка 'Проект'.")
            return

        df_filtered = df[df["Проект"].str.lower() == project_name.lower()]

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
        await update.message.reply_text("❌ Ошибка обработки проекта.")

# === Основная функция ===
def main():
    """Запуск бота"""
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Добавляем команды (только латинские!)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("update", update_data))
    app.add_handler(CommandHandler("finance", finance))
    app.add_handler(CommandHandler("period", period))
    app.add_handler(CommandHandler("project", project))

    # Запуск бота
    logging.info("✅ Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
