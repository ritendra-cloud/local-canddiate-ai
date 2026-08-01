from datetime import datetime, timezone
from sqlalchemy import ForeignKey, String, Text, event, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
class Base(DeclarativeBase): pass
class Session(Base):
    __tablename__='sessions'; id: Mapped[int]=mapped_column(primary_key=True); public_id: Mapped[str]=mapped_column(String(36), unique=True, index=True); title: Mapped[str]=mapped_column(String(255)); created_at: Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc)); updated_at: Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc)); messages: Mapped[list['Message']]=relationship(back_populates='session', cascade='all, delete-orphan')
class Message(Base):
    __tablename__='messages'; id: Mapped[int]=mapped_column(primary_key=True); session_id: Mapped[int]=mapped_column(ForeignKey('sessions.id', ondelete='CASCADE'), index=True); role: Mapped[str]=mapped_column(String(30)); content: Mapped[str]=mapped_column(Text); status: Mapped[str]=mapped_column(String(30), default='complete'); created_at: Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc)); session: Mapped[Session]=relationship(back_populates='messages')
class JobAnalysis(Base):
    __tablename__='job_analyses'; id: Mapped[int]=mapped_column(primary_key=True); public_id: Mapped[str|None]=mapped_column(String(36), unique=True, index=True, nullable=True); session_id: Mapped[int|None]=mapped_column(ForeignKey('sessions.id', ondelete='SET NULL'), nullable=True, index=True); job_title: Mapped[str|None]=mapped_column(String(255), nullable=True); job_description: Mapped[str]=mapped_column(Text); result_json: Mapped[str]=mapped_column(Text); alignment_score: Mapped[int|None]=mapped_column(nullable=True); recommendation: Mapped[str|None]=mapped_column(String(32),nullable=True); created_at: Mapped[datetime]=mapped_column(default=lambda:datetime.now(timezone.utc),index=True)
def init_database(path):
    path.parent.mkdir(parents=True, exist_ok=True); engine=create_engine(f'sqlite:///{path}')
    @event.listens_for(engine, 'connect')
    def foreign_keys(conn, _): conn.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    if 'public_id' not in {column['name'] for column in inspect(engine).get_columns('sessions')}:
        with engine.begin() as connection:
            connection.execute(text('ALTER TABLE sessions ADD COLUMN public_id VARCHAR(36)'))
    existing={column['name'] for column in inspect(engine).get_columns('job_analyses')}
    additions={'public_id':'VARCHAR(36)','job_title':'VARCHAR(255)','alignment_score':'INTEGER','recommendation':'VARCHAR(32)'}
    with engine.begin() as connection:
        for name,kind in additions.items():
            if name not in existing: connection.execute(text(f'ALTER TABLE job_analyses ADD COLUMN {name} {kind}'))
    return engine
