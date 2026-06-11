"""initial evaluation schema

Revision ID: a3b4c5d6e7f8
Revises:
Create Date: 2026-06-11 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'a3b4c5d6e7f8'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'evaluation_results',
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('retrieval_log_id', sa.UUID(), nullable=True),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('contexts', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('faithfulness', sa.Float(), nullable=True),
        sa.Column('answer_relevancy', sa.Float(), nullable=True),
        sa.Column('context_precision', sa.Float(), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_evaluation_results_tenant_id'), 'evaluation_results', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_evaluation_results_tenant_id'), table_name='evaluation_results')
    op.drop_table('evaluation_results')
