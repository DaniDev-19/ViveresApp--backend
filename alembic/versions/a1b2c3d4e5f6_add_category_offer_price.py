"""add_category_offer_price

Revision ID: a1b2c3d4e5f6
Revises: 12935f1db94d
Create Date: 2026-06-08

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "12935f1db94d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if "categories" not in tables:
        op.create_table(
            "categories",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_categories_id"), "categories", ["id"], unique=False)
        op.create_index(op.f("ix_categories_name"), "categories", ["name"], unique=True)

    product_columns = {col["name"] for col in inspector.get_columns("products")}

    if "category_id" not in product_columns:
        op.add_column("products", sa.Column("category_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "products_category_id_fkey",
            "products",
            "categories",
            ["category_id"],
            ["id"],
        )

    if "offer_price_usd" not in product_columns:
        op.add_column("products", sa.Column("offer_price_usd", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("products", "offer_price_usd")
    op.drop_constraint("products_category_id_fkey", "products", type_="foreignkey")
    op.drop_column("products", "category_id")
    op.drop_index(op.f("ix_categories_name"), table_name="categories")
    op.drop_index(op.f("ix_categories_id"), table_name="categories")
    op.drop_table("categories")
