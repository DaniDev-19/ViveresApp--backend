"""add_product_provider_id

Revision ID: e8f9a7b1c3d4
Revises: cde7714510c1
Create Date: 2026-06-11 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e8f9a7b1c3d4"
down_revision: Union[str, Sequence[str], None] = "cde7714510c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("provider_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "products_provider_id_fkey",
        "products",
        "providers",
        ["provider_id"],
        ["id"],
    )
    op.create_index(op.f("ix_products_provider_id"), "products", ["provider_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_products_provider_id"), table_name="products")
    op.drop_constraint("products_provider_id_fkey", "products", type_="foreignkey")
    op.drop_column("products", "provider_id")
