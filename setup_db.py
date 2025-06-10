import asyncio
from prisma import Prisma

async def main():
    db = Prisma()
    await db.connect()
    
    print("Database connected successfully!")
    print("Running migrations...")
    
    # automatic na mag set up ng database if mag "prisma db push" ka
     
    await db.disconnect()
    print("Setup complete!")

if __name__ == "__main__":
    asyncio.run(main())