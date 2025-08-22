"""new relationship delete cascade in product

Revision ID: 9d1bd606e180
Revises: 8597745976cd
Create Date: 2025-08-21 19:11:33.260694
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d1bd606e180'
down_revision: Union[str, Sequence[str], None] = '8597745976cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with cascade delete for products -> categories"""
    # Используем batch mode для SQLite
    with op.batch_alter_table("products") as batch_op:
        # Переопределяем внешний ключ с ondelete="CASCADE"
        batch_op.create_foreign_key(
            "fk_products_category_id",
            "categories",
            ["category_id"],
            ["id"],
            ondelete="CASCADE"
        )


def downgrade() -> None:
    """Downgrade schema to previous state"""
    with op.batch_alter_table("products") as batch_op:
        # Возвращаем FK без каскада
        batch_op.drop_constraint("fk_products_category_id", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_products_category_id",
            "categories",
            ["category_id"],
            ["id"]
        )
