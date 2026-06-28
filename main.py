import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from database import init_db, save_query
from rag_engine import process_and_save_document, ask_mistral



load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    text = (
        "Привет! Я твой AI-Архивариус.\n\n"
        "Скинь мне любой конспект или статью в формате <b>.txt</b>, "
        "а затем задавай вопросы. Я найду нужную информацию и отвечу строго по тексту."
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(F.document)
async def handle_document(message: Message, bot: Bot):
    if not message.document.file_name.endswith('.txt'):
        await message.answer("Пожалуйста, отправь файл в формате .txt")
        return

    msg = await message.answer("Скачиваю и изучаю документ. Это займет пару секунд.")
    
    try:
        file_in_memory = await bot.download(message.document)
        text_content = file_in_memory.read().decode('utf-8')
        result = process_and_save_document(text_content, doc_id=str(message.document.file_id))
        await msg.edit_text(f"{result}")
        
    except Exception as e:
        await msg.edit_text(f"Ошибка при обработке файла: {e}")

@dp.message(F.text)
async def handle_text(message: Message):
    question = message.text
    msg = await message.answer("Ищу ответ в архивах...")
    answer = ask_mistral(question)
    save_query(
        user_id=message.from_user.id, 
        question=question, 
        answer=answer
    )
    
    await msg.edit_text(answer)

async def main():
    init_db() 
    print("Бот успешно запущен! Нажми Ctrl+C для остановки.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())