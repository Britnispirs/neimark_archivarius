import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from database import init_db, save_query
from rag_engine import process_and_save_document, ask_mistral
from aiogram.client.session.aiohttp import AiohttpSession
import io
import pypdf
import docx


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def extract_text_from_pdf(file_stream) -> str:
    pdf_reader = pypdf.PdfReader(file_stream)
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def extract_text_from_docx(file_stream) -> str:
    doc = docx.Document(file_stream)
    text = ""
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text += paragraph.text + "\n"
    return text


@dp.message(Command("start"))
async def cmd_start(message: Message):
    text = (
        "Привет! Я твой AI-Архивариус.\n\n"
        "Скинь мне любой конспект или статью в формате <b>.txt</b>, "
        "а затем задавай вопросы. Я найду нужную информацию и отвечу строго по тексту."
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(F.document)
@dp.message(F.document)
async def handle_document(message: Message, bot: Bot):
    file_name = message.document.file_name.lower()
    
    if not (file_name.endswith('.txt') or file_name.endswith('.pdf') or file_name.endswith('.docx')):
        await message.answer("⚠️ Пожалуйста, отправь файл в формате .txt, .pdf или .docx")
        return

    msg = await message.answer("🔄 Скачиваю и изучаю документ...")
    
    try:
        file_in_memory = await bot.download(message.document)
        if file_name.endswith('.txt'):
            text_content = file_in_memory.read().decode('utf-8')
        elif file_name.endswith('.pdf'):
            text_content = extract_text_from_pdf(file_in_memory)
        elif file_name.endswith('.docx'):
            text_content = extract_text_from_docx(file_in_memory)
            
        if not text_content.strip():
            await msg.edit_text("❌ Не удалось извлечь текст из файла.")
            return
        
        result = process_and_save_document(text_content, doc_id=str(message.document.file_id))
        await msg.edit_text(f"✅ {result}")
        
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка при обработке файла: {e}")

@dp.message(F.text)
async def handle_text(message: Message):
    question = message.text
    msg = await message.answer("Ищу ответ в архивах...")
    answer = ask_mistral(question)
    
    clean_answer = answer.replace('**', '').replace('*', '')
    
    save_query(
        user_id=message.from_user.id, 
        question=question, 
        answer=clean_answer
    )
    
    await msg.edit_text(clean_answer)

async def main():
    init_db() 
    print("Бот успешно запущен! Нажми Ctrl+C для остановки.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())