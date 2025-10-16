from lica.sqlalchemy.noasync.dbase import create_engine_sessionclass

engine, Session = create_engine_sessionclass(env_var="DATABASE_URL", tag="tessdb")

__all__ = ["engine", "Session"]
