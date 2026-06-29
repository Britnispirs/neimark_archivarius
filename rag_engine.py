import os
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer
from mistralai.client import Mistral

load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

print("Поднимаем модель")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="student_notes")

mistral_client = Mistral(api_key=MISTRAL_API_KEY)


def process_and_save_document(text, doc_id, user_id):
    paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 50]
    if not paragraphs:
        return "Текст слишком короткий."

    embeddings = embedding_model.encode(paragraphs).tolist()
    ids = [f"{doc_id}_chunk_{i}" for i in range(len(paragraphs))]
    
    metadatas = [{"user_id": user_id} for _ in range(len(paragraphs))]

    collection.add(
        embeddings=embeddings,
        documents=paragraphs,
        ids=ids,
        metadatas=metadatas
    )
    return f"Текст разбит на {len(paragraphs)} смысловых блоков и сохранен в твой личный архив."

def ask_mistral(question, user_id):
    question_embedding = embedding_model.encode([question]).tolist()
    
    results = collection.query(
        query_embeddings=question_embedding, 
        n_results=3,
        where={"user_id": user_id}
    )

    found_chunks = results['documents'][0]
    if not found_chunks:
        return "В твоем документе нет ответа на этот вопрос. Сначала загрузи нужный документ."

    context = "\n\n".join(found_chunks)
    
    prompt = f"""Ответь на вопрос, опираясь ТОЛЬКО на контекст. Если ответа нет, скажи об этом.
    Отвечай простым текстом без форматирования Markdown. не используй звездочки и решетки.
    Контекст: {context}
    Вопрос: {question}"""

    try:
        chat_response = mistral_client.chat.complete(
            model="mistral-tiny",
            messages=[{"role": "user", "content": prompt}]
        )
        return chat_response.choices[0].message.content
    except Exception as e:
        return f"Ошибка API: {e}"


def clear_user_data(user_id):
    try:
        collection.delete(where={"user_id": user_id})
        return "Твой личный архив успешно очищен! Можно загружать новые файлы."
    except Exception as e:
        return f"Ошибка при очистке: {e}"