"""Initial schema - SQLite compatible

Revision ID: 001
Revises: 
Create Date: 2026-10-14

"""
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table - SQLite compatible UUID as String
    op.create_table('users',
    sa.Column('id', sa.String(36), nullable=False, default=lambda: str(uuid.uuid4())),
    sa.Column('email', sa.String(255), nullable=False),
    sa.Column('hashed_password', sa.String(255), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create user_preferences table
    op.create_table('user_preferences',
    sa.Column('id', sa.String(36), nullable=False, default=lambda: str(uuid.uuid4())),
    sa.Column('user_id', sa.String(36), nullable=False),
    sa.Column('destination', sa.String(255), nullable=True),
    sa.Column('min_budget', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('max_budget', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('min_rating', sa.Numeric(precision=2, scale=1), nullable=False),
    sa.Column('cleanliness_weight', sa.Numeric(precision=3, scale=2), nullable=False),
    sa.Column('location_weight', sa.Numeric(precision=3, scale=2), nullable=False),
    sa.Column('rooms_weight', sa.Numeric(precision=3, scale=2), nullable=False),
    sa.Column('service_weight', sa.Numeric(precision=3, scale=2), nullable=False),
    sa.Column('value_weight', sa.Numeric(precision=3, scale=2), nullable=False),
    sa.Column('sleep_quality_weight', sa.Numeric(precision=3, scale=2), nullable=False),
    sa.Column('travel_style', sa.String(50), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_preferences_user_id'), 'user_preferences', ['user_id'], unique=False)

    # Create saved_hotels table
    op.create_table('saved_hotels',
    sa.Column('id', sa.String(36), nullable=False, default=lambda: str(uuid.uuid4())),
    sa.Column('user_id', sa.String(36), nullable=False),
    sa.Column('hotel_id', sa.String(255), nullable=False),
    sa.Column('saved_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'hotel_id', name='unique_user_hotel')
    )
    op.create_index(op.f('ix_saved_hotels_hotel_id'), 'saved_hotels', ['hotel_id'], unique=False)
    op.create_index(op.f('ix_saved_hotels_user_id'), 'saved_hotels', ['user_id'], unique=False)

    # Create model_experiments table
    op.create_table('model_experiments',
    sa.Column('id', sa.String(36), nullable=False, default=lambda: str(uuid.uuid4())),
    sa.Column('experiment_name', sa.String(255), nullable=False),
    sa.Column('model_type', sa.String(50), nullable=False),
    sa.Column('parameters', sa.JSON(), nullable=True),
    sa.Column('metrics', sa.JSON(), nullable=True),
    sa.Column('dataset_version', sa.String(50), nullable=True),
    sa.Column('training_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    sa.Column('status', sa.String(50), nullable=False),
    sa.Column('notes', sa.String(1000), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('model_experiments')
    op.drop_index(op.f('ix_saved_hotels_user_id'), table_name='saved_hotels')
    op.drop_index(op.f('ix_saved_hotels_hotel_id'), table_name='saved_hotels')
    op.drop_table('saved_hotels')
    op.drop_index(op.f('ix_user_preferences_user_id'), table_name='user_preferences')
    op.drop_table('user_preferences')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

