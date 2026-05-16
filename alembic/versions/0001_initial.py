"""initial

Revision ID: 0001
Revises: 
Create Date: 2026-05-16

"""

from alembic import op
import sqlalchemy as sa


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "payment_packages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "CONFIRMED", "FAILED", "CANCELED", name="paymentstatus"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column(
            "method",
            sa.Enum("CREDIT_CARD", "PIX", "BOLETO", "PAYPAL", name="paymentmethod"),
            nullable=False,
        ),
        sa.Column("transaction_id", sa.String(length=100), nullable=True),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_payments_user_id", "payments", ["user_id"], unique=False)
    op.create_index("ix_payments_status", "payments", ["status"], unique=False)
    op.create_index("uq_payments_transaction_id", "payments", ["transaction_id"], unique=True)
    op.create_index("uq_payments_idempotency_key", "payments", ["idempotency_key"], unique=True)

    op.create_table(
        "user_packages",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("package_id", sa.Integer(), sa.ForeignKey("payment_packages.id"), nullable=False),
        sa.Column("payment_id", sa.BigInteger(), sa.ForeignKey("payments.id"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "EXPIRED", "CANCELED", name="userpackagestatus"),
            nullable=False,
            server_default="ACTIVE",
        ),
    )
    op.create_index("ix_user_packages_user_id", "user_packages", ["user_id"], unique=False)
    op.create_index("ix_user_packages_package_id", "user_packages", ["package_id"], unique=False)
    op.create_index("ix_user_packages_payment_id", "user_packages", ["payment_id"], unique=False)
    op.create_index(
        "ix_user_packages_user_payment",
        "user_packages",
        ["user_id", "payment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_packages_user_payment", table_name="user_packages")
    op.drop_index("ix_user_packages_payment_id", table_name="user_packages")
    op.drop_index("ix_user_packages_package_id", table_name="user_packages")
    op.drop_index("ix_user_packages_user_id", table_name="user_packages")
    op.drop_table("user_packages")

    op.drop_index("uq_payments_idempotency_key", table_name="payments")
    op.drop_index("uq_payments_transaction_id", table_name="payments")
    op.drop_index("ix_payments_status", table_name="payments")
    op.drop_index("ix_payments_user_id", table_name="payments")
    op.drop_table("payments")

    op.drop_table("payment_packages")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS paymentstatus")
    op.execute("DROP TYPE IF EXISTS paymentmethod")
    op.execute("DROP TYPE IF EXISTS userpackagestatus")
