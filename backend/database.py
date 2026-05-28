from config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
    """Get database session and ensure proper cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()