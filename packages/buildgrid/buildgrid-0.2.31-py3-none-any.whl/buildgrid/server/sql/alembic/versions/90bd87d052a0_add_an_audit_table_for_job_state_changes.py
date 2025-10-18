# Copyright (C) 2025 Bloomberg LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  <http://www.apache.org/licenses/LICENSE-2.0>
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Add an audit table for job state changes

Revision ID: 90bd87d052a0
Revises: 22cc661efef9
Create Date: 2025-04-04 17:07:55.092386

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "90bd87d052a0"
down_revision = "22cc661efef9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_type", sa.Integer(), nullable=False),
        sa.Column("job_name", sa.String(), nullable=False, index=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column(
            "payload", sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"), nullable=True
        ),
        sa.ForeignKeyConstraint(["job_name"], ["jobs.name"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("job_history")
