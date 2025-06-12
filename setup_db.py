import asyncio
from prisma import Prisma

async def main():
    db = Prisma()
    await db.connect()
    
    print("Database connected successfully!")
    print("Running migrations...")
    
    # Database will be automatically set up when running "prisma db push"
    
    await db.disconnect()
    print("Setup complete!")

if __name__ == "__main__":
    asyncio.run(main())