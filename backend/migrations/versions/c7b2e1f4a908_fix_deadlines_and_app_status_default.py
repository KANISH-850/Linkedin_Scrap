"""fix_deadlines_and_app_status_default

Revision ID: c7b2e1f4a908
Revises: ed7eabf5ed40
Create Date: 2026-11-13 08:52:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7b2e1f4a908'
down_revision: Union[str, None] = 'ed7eabf5ed40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update application_status column default to 'UNVERIFIED'
    with op.batch_alter_table('opportunities', schema=None) as batch_op:
        batch_op.alter_column('application_status', server_default='UNVERIFIED')

    # 2. Mark past deadlines as EXPIRED and closed
    op.execute(
        "UPDATE opportunities "
        "SET application_status = 'EXPIRED', active_status = 'closed', verification_status = 'EXPIRED' "
        "WHERE deadline IS NOT NULL AND deadline < CURRENT_DATE"
    )

    # 3. Mark research papers as NOT_APPLICABLE
    op.execute(
        "UPDATE opportunities "
        "SET opportunity_type = 'RESEARCH_PAPER', application_status = 'NOT_APPLICABLE' "
        "WHERE category = 'research' OR title LIKE '%arXiv%' OR source_url LIKE '%arxiv.org%'"
    )

    # 4. Mark closed verifications
    op.execute(
        "UPDATE opportunities "
        "SET application_status = 'CLOSED', active_status = 'closed' "
        "WHERE verification_status = 'CLOSED'"
    )


def downgrade() -> None:
    with op.batch_alter_table('opportunities', schema=None) as batch_op:
        batch_op.alter_column('application_status', server_default='OPEN')

