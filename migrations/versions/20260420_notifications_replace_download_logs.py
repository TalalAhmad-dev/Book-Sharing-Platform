"""replace download logs with notifications

Revision ID: 20260420_notifications
Revises:
Create Date: 2026-04-20
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260420_notifications'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'notifications' not in tables:
        op.create_table(
            'notifications',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('recipient_id', sa.Integer(), nullable=False),
            sa.Column('actor_id', sa.Integer(), nullable=True),
            sa.Column('category', sa.String(length=50), nullable=False, server_default='general'),
            sa.Column('title', sa.String(length=150), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('entity_type', sa.String(length=50), nullable=True),
            sa.Column('entity_id', sa.Integer(), nullable=True),
            sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('read_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['actor_id'], ['users.id']),
            sa.ForeignKeyConstraint(['recipient_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )

    if 'download_logs' in tables:
        op.drop_table('download_logs')


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'download_logs' not in tables:
        op.create_table(
            'download_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('book_id', sa.Integer(), nullable=False),
            sa.Column('downloaded_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['book_id'], ['books.id']),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )

    if 'notifications' in tables:
        op.drop_table('notifications')
