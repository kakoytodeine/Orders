from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import ForeignKey
from datetime import datetime
from app.db.db_session import Base


class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    tg_id: Mapped[int] = mapped_column(unique=True, nullable=False)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(nullable=True)
    role: Mapped[str] = mapped_column(nullable=True, default='user')

    orders = relationship('Order', back_populates='user')
    
class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(nullable=False)

    products = relationship('Product', back_populates='category')
    orders = relationship('Order', back_populates='category')


class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    target_quantity: Mapped[int] = mapped_column(nullable=False)
    photo_url: Mapped[str] = mapped_column(nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id', ondelete="CASCADE"), nullable=False)

    category = relationship('Category', back_populates='products')
    orders = relationship('OrderItem', back_populates='product', cascade="all, delete-orphan")



class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    user = relationship('User', back_populates='orders')
    category = relationship('Category', back_populates='orders')
    items = relationship('OrderItem', back_populates='order')

class OrderItem(Base):
    __tablename__ = 'order_items'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), nullable=False)
    actual_quantity: Mapped[int] = mapped_column(nullable=False)
    to_order: Mapped[int] = mapped_column(nullable=False)

    order = relationship('Order', back_populates='items')
    product = relationship('Product', back_populates='orders')


