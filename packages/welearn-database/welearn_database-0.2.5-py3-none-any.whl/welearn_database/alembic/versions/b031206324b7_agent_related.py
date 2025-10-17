"""agent_related

Revision ID: b031206324b7
Revises: 4c7161819e5a
Create Date: 2025-10-10 16:33:43.217427

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b031206324b7'
down_revision: Union[str, None] = '4c7161819e5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('checkpoint_blobs',
                    sa.Column('thread_id', sa.TEXT(), autoincrement=False, nullable=False),
                    sa.Column('checkpoint_ns', sa.TEXT(), server_default=sa.text("''::text"), autoincrement=False,
                              nullable=False),
                    sa.Column('channel', sa.TEXT(), autoincrement=False, nullable=False),
                    sa.Column('version', sa.TEXT(), autoincrement=False, nullable=False),
                    sa.Column('type', sa.TEXT(), autoincrement=False, nullable=False),
                    sa.Column('blob', postgresql.BYTEA(), autoincrement=False, nullable=True),
                    sa.PrimaryKeyConstraint('thread_id', 'checkpoint_ns', 'channel', 'version',
                                            name=op.f('checkpoint_blobs_pkey')),
                    schema='agent_related'
                    )
    op.create_table('checkpoint_writes',
                    sa.Column('thread_id', sa.TEXT(), autoincrement=False, nullable=False),
                    sa.Column('checkpoint_ns', sa.TEXT(), server_default=sa.text("''::text"), autoincrement=False,
                              nullable=False),
                    sa.Column('checkpoint_id', sa.TEXT(), autoincrement=False, nullable=False),
                    sa.Column('task_id', sa.TEXT(), autoincrement=False, nullable=False),
                    sa.Column('idx', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.Column('channel', sa.TEXT(), autoincrement=False, nullable=False),
                    sa.Column('type', sa.TEXT(), autoincrement=False, nullable=True),
                    sa.Column('blob', postgresql.BYTEA(), autoincrement=False, nullable=False),
                    sa.Column('task_path', sa.TEXT(), server_default=sa.text("''::text"), autoincrement=False,
                              nullable=False),
                    sa.PrimaryKeyConstraint('thread_id', 'checkpoint_ns', 'checkpoint_id', 'task_id', 'idx',
                                            name=op.f('checkpoint_writes_pkey')),
                    schema='agent_related'
                    )

    op.create_table('checkpoint_migrations',
                    sa.Column('v', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.PrimaryKeyConstraint('v', name=op.f('checkpoint_migrations_pkey')),
                    schema='agent_related'
                    )

    op.create_table('checkpoints',
                    sa.Column('thread_id', sa.TEXT(), autoincrement=False, nullable=False),
                    sa.Column('checkpoint_ns', sa.TEXT(), server_default=sa.text("''::text"), autoincrement=False,
                              nullable=False),
                    sa.Column('checkpoint_id', sa.TEXT(), autoincrement=False, nullable=False),
                    sa.Column('parent_checkpoint_id', sa.TEXT(), autoincrement=False, nullable=True),
                    sa.Column('type', sa.TEXT(), autoincrement=False, nullable=True),
                    sa.Column('checkpoint', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False,
                              nullable=False),
                    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()),
                              server_default=sa.text("'{}'::jsonb"), autoincrement=False, nullable=False),
                    sa.PrimaryKeyConstraint('thread_id', 'checkpoint_ns', 'checkpoint_id',
                                            name=op.f('checkpoints_pkey')),
                    schema='agent_related'
                    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_table('checkpoints', schema='agent_related')
    op.drop_table('checkpoint_migrations', schema='agent_related')
    op.drop_table('checkpoint_writes', schema='agent_related')
    op.drop_table('checkpoint_blobs', schema='agent_related')
    # ### end Alembic commands ###
