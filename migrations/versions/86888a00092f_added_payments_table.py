"""Added payments  table

Revision ID: 86888a00092f
Revises: 5ab25b7f3046
Create Date: 2024-12-16 14:38:34.284626

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '86888a00092f'
down_revision = '5ab25b7f3046'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_column('card_number')
        batch_op.drop_column('card_holder_name')
        batch_op.drop_column('gsm_number')
        batch_op.drop_column('identity_number')
        batch_op.drop_column('shipping_status')
        batch_op.drop_column('name')
        batch_op.drop_column('contact_name')
        batch_op.drop_column('registration_address')
        batch_op.drop_column('zip_code')
        batch_op.drop_column('email')
        batch_op.drop_column('delivery_date')
        batch_op.drop_column('shipping_date')
        batch_op.drop_column('expire_month')
        batch_op.drop_column('expire_year')
        batch_op.drop_column('cvc')
        batch_op.drop_column('city')
        batch_op.drop_column('address')
        batch_op.drop_column('tracking_number')
        batch_op.drop_column('surname')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('surname', sa.VARCHAR(length=150), nullable=False))
        batch_op.add_column(sa.Column('tracking_number', sa.VARCHAR(length=100), nullable=True))
        batch_op.add_column(sa.Column('address', sa.VARCHAR(length=250), nullable=False))
        batch_op.add_column(sa.Column('city', sa.VARCHAR(length=100), nullable=False))
        batch_op.add_column(sa.Column('cvc', sa.VARCHAR(length=4), nullable=False))
        batch_op.add_column(sa.Column('expire_year', sa.VARCHAR(length=4), nullable=False))
        batch_op.add_column(sa.Column('expire_month', sa.VARCHAR(length=2), nullable=False))
        batch_op.add_column(sa.Column('shipping_date', sa.DATETIME(), nullable=True))
        batch_op.add_column(sa.Column('delivery_date', sa.DATETIME(), nullable=True))
        batch_op.add_column(sa.Column('email', sa.VARCHAR(length=150), nullable=False))
        batch_op.add_column(sa.Column('zip_code', sa.VARCHAR(length=10), nullable=False))
        batch_op.add_column(sa.Column('registration_address', sa.VARCHAR(length=250), nullable=False))
        batch_op.add_column(sa.Column('contact_name', sa.VARCHAR(length=150), nullable=False))
        batch_op.add_column(sa.Column('name', sa.VARCHAR(length=150), nullable=False))
        batch_op.add_column(sa.Column('shipping_status', sa.VARCHAR(length=50), nullable=True))
        batch_op.add_column(sa.Column('identity_number', sa.VARCHAR(length=11), nullable=False))
        batch_op.add_column(sa.Column('gsm_number', sa.VARCHAR(length=15), nullable=False))
        batch_op.add_column(sa.Column('card_holder_name', sa.VARCHAR(length=150), nullable=False))
        batch_op.add_column(sa.Column('card_number', sa.VARCHAR(length=20), nullable=False))

    # ### end Alembic commands ###
