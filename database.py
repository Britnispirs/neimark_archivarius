from sqlalchemy import create_engine, Column, Integer, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

engine = create_engine('sqlite:///archivarius.db', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class UserQuery(Base):
    __tablename__ = 'user_queries'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True) 
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(engine)
    print('бд создана')

def save_query(user_id, question, answer):
    session = Session()
    try:
        new_query = UserQuery(user_id=user_id, question=question, answer=answer)
        session.add(new_query)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Ошибка БД: {e}")
    finally:
        session.close()