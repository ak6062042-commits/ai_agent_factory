from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy import exc as core_exc
from sqlalchemy.orm import sessionmaker, DeclarativeMeta
from backend.app.config import DATABASE_URL # sqlite:///./backend/data/app.db
from backend.log.logger import Logger

DB_URL = DATABASE_URL
engine = create_engine(DB_URL, ...) #kwargs not decided yet
SessionLocal = sessionmaker(bind = engine, autoflush=False, autocommit=False)
logger = Logger()

def init_db(Base: DeclarativeMeta): # Base will be defined in the model.py, right now just a place holder here // TODO: Fill the kwargs after model.py
    Base.metadata.create_all(bind = engine)

@contextmanager
def get_session():
    session = SessionLocal()
    
    try:
        yield session
        session.commit()
        
    except core_exc.PendingRollbackError as e:
        logger.log(f"Pending rollback detected: {e}", "ERROR")
        session.rollback()
        raise
    
    except core_exc.SQLAlchemyError as e:
        logger.log(f"Exception in the SQL database deteceted {e}", "ERROR")
        session.rollback()
        raise
        
    except Exception as e:
        logger.log(f"unexpected Error occured {e}", "ERROR")
        session.rollback()
        raise
    
    finally:
        session.close()
         
