"""add session_token (server-side session stamp)

Revision ID: b3f1a9c20d47
Revises: 0299762c402d
Create Date: 2026-09-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3f1a9c20d47'
down_revision = '0299762c402d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('session_token', sa.String(length=64), nullable=True))


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('session_token')
