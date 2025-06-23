from app.db.database import async_session
from app.db.models import Session as SessionModel

async def save_session(user_id: str, session_id: str, prompt: str, reply: str):
    new_session = SessionModel(
        user_id=user_id,
        session_id=session_id,
        prompt=prompt,
        reply=reply
    )
    async with async_session() as session:
        session.add(new_session)
        await session.commit()
