import asyncio
from app.core.database import engine, async_session_maker, Base, User
from app.core.security import get_password_hash

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session_maker() as db:
        result = await db.execute(User.__table__.select().where(User.username == 'admin'))
        if result.first() is None:
            admin = User(
                username='admin',
                password_hash=get_password_hash('admin123'),
                role='admin',
                is_active=True
            )
            db.add(admin)
            await db.commit()
            print('Admin user created: admin / admin123')
        else:
            print('Admin user already exists')

if __name__ == '__main__':
    asyncio.run(init_db())
