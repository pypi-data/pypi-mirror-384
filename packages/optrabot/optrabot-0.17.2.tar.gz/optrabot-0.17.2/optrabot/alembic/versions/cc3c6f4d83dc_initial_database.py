"""Initial Database

Revision ID: cc3c6f4d83dc
Revises: 
Create Date: 2024-01-23 20:53:10.548050

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc3c6f4d83dc'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'accounts',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('broker', sa.String(5), nullable=False),
        sa.Column('pdt', sa.Boolean, nullable=False)
	)
    op.create_table(
        'trades',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('account', sa.String, sa.ForeignKey('accounts.id'), nullable=False),
        sa.Column('symbol', sa.String, nullable=False),
        sa.Column('strategy',sa.String, nullable=False),
        sa.Column('status', sa.String, nullable=False),
        sa.Column('realizedPNL', sa.Float, nullable=False)
	)
    op.create_table(
        'transactions',
		sa.Column('tradeid', sa.String, sa.ForeignKey('trades.id'), primary_key=True),
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('type', sa.String, nullable=False),
        sa.Column('sectype', sa.String, nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP, nullable=False),
        sa.Column('expiration', sa.Date),
        sa.Column('strike', sa.Float, nullable=False),
        sa.Column('contracts', sa.Integer, nullable=False),
        sa.Column('price', sa.Float, nullable=False),
        sa.Column('fee', sa.Float, nullable=False),
        sa.Column('commission', sa.Float, nullable=False),
        sa.Column('notes', sa.String, nullable=False)
	)


def downgrade() -> None:
    op.drop_table('trades')
    op.drop_table('accounts')
    op.drop_table('transactions')
