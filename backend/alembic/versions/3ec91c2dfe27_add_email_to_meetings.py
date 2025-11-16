"""add_email_to_meetings

Revision ID: 3ec91c2dfe27
Revises: 4150d47ed9d7
Create Date: 2025-11-15 19:01:20.779507

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ec91c2dfe27'
down_revision: Union[str, None] = '4150d47ed9d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add email and email_generated_at columns to meetings table
    op.add_column('meetings', sa.Column('email', sa.Text(), nullable=True))
    op.add_column('meetings', sa.Column('email_generated_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove email columns from meetings table
    op.drop_column('meetings', 'email_generated_at')
    op.drop_column('meetings', 'email')

