"""Update run status enum

Revision ID: 1ec1eabe45bf
Revises: 2e57fc6dd873
Create Date: 2024-04-16 10:55:22.821262

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ec1eabe45bf'
down_revision: Union[str, None] = '2e57fc6dd873'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    dialect = op.get_context().dialect.name
    match dialect:
        case 'postgresql':
            op.execute("ALTER TYPE runstatus RENAME VALUE 'SUCCEEDED' TO 'SUCCESS'")
        case _:
            op.execute("UPDATE runs SET status = 'SUCCESS' WHERE status = 'SUCCEEDED'")


def downgrade() -> None:
    dialect = op.get_context().dialect.name
    match dialect:
        case 'postgresql':
            op.execute("ALTER TYPE runstatus RENAME VALUE 'SUCCESS' TO 'SUCCEEDED'")
        case _:
            op.execute("UPDATE runs SET status = 'SUCCEEDED' WHERE status = 'SUCCESS'")
