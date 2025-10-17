"""Allow to sync measurement rois

Revision ID: d8d292a431fe
Revises: e78898a9c9f1
Create Date: 2023-03-28 11:29:14.826784

"""
from sqlalchemy import Column, Boolean

from alembic import op


# revision identifiers, used by Alembic.
revision = "d8d292a431fe"
down_revision = "e78898a9c9f1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "measurement",
        Column("sync_lane_rois", Boolean(), nullable=False, default=False, server_default="0"),
    )


def downgrade():
    pass
