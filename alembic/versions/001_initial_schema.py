"""initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-07-20 00:00:00
"""

import app.models  # noqa: F401
from alembic import op
from app.database import Base

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
