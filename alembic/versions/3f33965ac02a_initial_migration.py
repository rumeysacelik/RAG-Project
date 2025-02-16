"""initial migration

Revision ID: 3f33965ac02a
Revises: 
Create Date: 2024-12-22 13:22:40.256666

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3f33965ac02a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('request_logs', 'created_date',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=True)
    op.drop_column('request_logs', 'timestamp')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('request_logs', sa.Column('timestamp', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.alter_column('request_logs', 'created_date',
               existing_type=sa.DateTime(),
               type_=postgresql.TIMESTAMP(timezone=True),
               existing_nullable=True)
    # ### end Alembic commands ###
