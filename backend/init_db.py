from app.database import Base, SessionLocal, engine
from app.services.knowledge_service import ensure_knowledge_schema

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
db = SessionLocal()
try:
    ensure_knowledge_schema(db)
finally:
    db.close()
print("Database tables created successfully!")
