"""fix_calendar_event_unique_constraint

Revision ID: f185998ab882
Revises: 3ec91c2dfe27
Create Date: 2025-11-16 15:31:33.217473

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f185998ab882'
down_revision: Union[str, None] = '3ec91c2dfe27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the old unique index on google_event_id alone
    op.drop_index('ix_calendar_events_google_event_id', table_name='calendar_events')
    
    # Add index on google_account_id if it doesn't exist
    # (needed for the composite unique constraint)
    op.create_index(
        'ix_calendar_events_google_account_id',
        'calendar_events',
        ['google_account_id'],
        unique=False
    )
    
    # Create composite unique constraint: google_event_id should be unique per google_account_id
    # This allows the same event ID to exist in different Google accounts
    op.create_unique_constraint(
        'uq_calendar_event_account_event',
        'calendar_events',
        ['google_account_id', 'google_event_id']
    )
    
    # Recreate the index on google_event_id (non-unique now)
    op.create_index(
        'ix_calendar_events_google_event_id',
        'calendar_events',
        ['google_event_id'],
        unique=False
    )


def downgrade() -> None:
    # Drop the composite unique constraint
    op.drop_constraint('uq_calendar_event_account_event', 'calendar_events', type_='unique')
    
    # Drop indexes
    op.drop_index('ix_calendar_events_google_event_id', table_name='calendar_events')
    op.drop_index('ix_calendar_events_google_account_id', table_name='calendar_events')
    
    # Restore the old unique index on google_event_id alone
    op.create_index(
        'ix_calendar_events_google_event_id',
        'calendar_events',
        ['google_event_id'],
        unique=True
    )
