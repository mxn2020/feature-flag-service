"""SQLAlchemy ORM models."""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class Flag(Base):
    __tablename__ = "flags"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    default_variant: Mapped[str] = mapped_column(String(100), nullable=False, default="off")
    rollout_percentage: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    targeted_allow: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    targeted_deny: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    rules: Mapped[list[Rule]] = relationship("Rule", back_populates="flag", cascade="all, delete-orphan")
    flag_environments: Mapped[list[FlagEnvironment]] = relationship(
        "FlagEnvironment", back_populates="flag", cascade="all, delete-orphan"
    )


class Environment(Base):
    __tablename__ = "environments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.utcnow
    )

    flag_environments: Mapped[list[FlagEnvironment]] = relationship(
        "FlagEnvironment", back_populates="environment", cascade="all, delete-orphan"
    )


class FlagEnvironment(Base):
    """Per-environment overrides for a flag (enabled state, rollout, targeting)."""
    __tablename__ = "flag_environments"
    __table_args__ = (UniqueConstraint("flag_id", "environment_id", name="uq_flag_env"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    flag_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("flags.id", ondelete="CASCADE"), nullable=False
    )
    environment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("environments.id", ondelete="CASCADE"), nullable=False
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rollout_percentage: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    targeted_allow: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    targeted_deny: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    default_variant: Mapped[str] = mapped_column(String(100), nullable=False, default="off")

    flag: Mapped[Flag] = relationship("Flag", back_populates="flag_environments")
    environment: Mapped[Environment] = relationship("Environment", back_populates="flag_environments")


class Rule(Base):
    __tablename__ = "rules"
    __table_args__ = (UniqueConstraint("flag_id", "environment_id", "priority", name="uq_rule_priority"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    flag_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("flags.id", ondelete="CASCADE"), nullable=False
    )
    environment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("environments.id", ondelete="CASCADE"), nullable=False
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conditions: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    variant: Mapped[str] = mapped_column(String(100), nullable=False, default="on")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.datetime.utcnow
    )

    flag: Mapped[Flag] = relationship("Flag", back_populates="rules")
