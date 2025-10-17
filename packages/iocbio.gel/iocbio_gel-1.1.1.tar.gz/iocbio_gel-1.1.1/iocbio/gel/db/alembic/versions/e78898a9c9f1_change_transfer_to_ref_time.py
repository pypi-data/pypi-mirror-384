"""Change transfer to ref_time

Revision ID: e78898a9c9f1
Revises: 8b8ae59755af
Create Date: 2023-03-27 14:19:25.430780

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "e78898a9c9f1"
down_revision = "8b8ae59755af"
branch_labels = None
depends_on = None


def upgrade():
    is_batch = op.get_context().opts.get("render_as_batch", False)
    if not is_batch:
        op.alter_column("gel", column_name="transfer", new_column_name="ref_time")
    else:
        # sqlite is using batch mode and we have to disable foreign_keys check
        op.execute("PRAGMA foreign_keys=OFF")
        with op.batch_alter_table("gel") as bop:
            bop.alter_column(column_name="transfer", new_column_name="ref_time")
        op.execute("PRAGMA foreign_keys=ON")


def downgrade():
    pass
