from datetime import datetime

from sqlalchemy import select

from app.db.models import User, Category, Product, Order, OrderItem
from sqlalchemy.orm import Session
from app.logger import logger


class UserRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def create_user(self, tg_id: int, username: str, first_name: str) -> User | None:
        """Создание нового юзера"""
        try:
            new_user = User(
                tg_id=tg_id,
                username=username,
                first_name=first_name
            )
            self.session.add(new_user)
            self.session.commit()
            return new_user
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            self.session.rollback()
            return None
    
    def get_user_by_tg_id(self, tg_id: int) -> User | None:
        """Получить юзера по tg id"""
        try:
            return self.session.query(User).filter(User.tg_id == tg_id).first()
        except Exception as e:
            logger.error(f"Error getting user by tg_id: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> User | None:
        """Получить юзера по id """
        try:
            return self.session.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting user by id: {e}")
            return None
        
    def get_all_users(self):
        try:
            return self.session.query(User).all()
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return None


class CategoryRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def create_category(self, name: str) -> Category | None:
        """Создание ногой категории"""
        try:
            new_category = Category(
                name=name
            )
            self.session.add(new_category)
            self.session.commit()
            return new_category
        except Exception as e:
            logger.error(f"Error creating category: {e}")
            return None
    
    def get_category_by_id(self, category_id: int) -> Category | None:
        """Получить категорию по id """
        try:
            return self.session.query(Category).filter(Category.id == category_id).first()
        except Exception as e:
            logger.error(f"Error getting category by id: {e}")
            return None
        
    def get_category_by_name(self, name_category: str) -> Category | None:
        """Получить категорию по нэйму"""
        try:
            return self.session.query(Category).filter(Category.name == name_category).first()
        except Exception as e:
            logger.error(f'Error getting category by name: {e}')
            return None
        
    def get_all_categories(self) -> list[Category] | list:
        """Получить все категории"""
        try:
            return self.session.query(Category).all()
        except Exception as e:
            logger.error(f"Error getting all categories: {e}")
            return []
    
    def update_category(self, category_id: int, name: str) -> Category | None:
        """Обновление name категории"""
        category = self.get_category_by_id(category_id)
        if not category:
            logger.error(f"Category with id {category_id} not found for update.")
            return None
        category.name = name
        try:
            self.session.commit()
            return category
        except Exception as e:
            logger.error(f"Error updating category: {e}")
            self.session.rollback()
            return None
    
    def delete_category(self, category_id: int) -> bool:
        """Удаление категории"""
        category = self.get_category_by_id(category_id)
        if not category:
            logger.error(f"Category with id {category_id} not found for deletion.")
            return False
        try:
            self.session.delete(category)
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting category: {e}")
            self.session.rollback()
            return False


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self.session = session
    
    def get_all_by_category(self, category_id: int) ->list[Category]:
        """Получить вс продукты по категории"""
        try:
            return self.session.query(Product).filter(Product.category_id == category_id).all()
        except Exception as e:
            logger.error(f'Error getting products by category {e}')
            return []
        
    def get_all_products(self):
        try:
            return self.session.scalars(select(Product)).all()
        except Exception as e:
            logger.error(f"Error getting all products {e}")
            return []
    
    def get_by_id(self, product_id: int) -> Product | None:
        """Получить категорию по id продукта"""
        try:
            return self.session.query(Product).filter(Product.id == product_id).first()
        except Exception as e:
            logger.error(f'Error getting product by id {e}')
            return None
    
    def create(self, name: str, target_quantity: int, category_id: int, photo_url: str = None, ) -> Product | None:
        """Создание нового продукта"""
        try:
            new_product = Product(
                name=name,
                target_quantity=target_quantity,
                category_id=category_id,
                photo_url=photo_url
            )
            self.session.add(new_product)
            self.session.commit()
            return new_product
        except Exception as e:
            logger.error(f'Error add new product {e}')
            self.session.rollback()
            return None
    
    def update_target_quantity(self, product_id: int, new_quantity: int) -> bool:
        """Обновление количества по умолчанию"""
        try:
            product = self.get_by_id(product_id=product_id)
            if not product:
                logger.error(f'Product with id {product_id} not fount for update')
                return False
            product.target_quantity = new_quantity
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f'Error update quantity target {e}')
            return False
    
    def delete(self, product_id: int) -> bool:
        """Удаление продукта"""
        try:
            product = self.get_by_id(product_id=product_id)
            if not product:
                logger.error(f'Product not delete becouse not found with id {product_id}')
                return False
            self.session.delete(product)
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f'failed delete product {e}')
            return False
    
    def get_product_by_name(self, product_name: str, category_id: int) -> Product | None:
        try:
            return self.session.query(Product).filter(Product.name == product_name, Product.category_id==category_id).first()
        except Exception as e:
            logger.error(f"Error getting product by name in category {e}")
            return None
            
            

class OrderRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, user_id: int, category_id: int, created_at: None = None) -> Order | None:
        if created_at is None:
            created_at = datetime.now()
        try:
            order = Order(
                user_id=user_id,
                category_id=category_id,
                created_at=created_at
            )
            self.session.add(order)
            self.session.commit()
            return order
        except Exception as e:
            logger.error(f'Not field created new order {e}')
            self.session.rollback()
            return None
    
    def get_by_id(self, order_id: int) -> Order | None:
        try:
            return self.session.query(Order).filter(Order.id == order_id).first()
        except Exception as e:
            logger.error(f'Not found {order_id} {e}')
            return None
    
    def get_all_by_user(self, user_id: int) -> list[Order]:
        return self.session.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
        
    def get_last_by_user(self, user_id: int) -> Order | None:
        try:
            return self.session.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).first()
        except Exception as e:
            logger.error(e)
            return None


class OrderItemRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_items(self, order_id: int, items: list[dict]) -> None:
        try:
            order_items = [
                OrderItem(
                    order_id=order_id,
                    product_id=item['product_id'],
                    actual_quantity=item['actual_quantity'],
                    to_order=item['to_order']
                ) for item in items
            ]
            self.session.add_all(order_items)
            self.session.commit()
        except Exception as e:
            logger.error(f"Failed to add order items: {e}")
            self.session.rollback()

    def get_by_id(self, order_item_id: int) -> OrderItem | None:
        try:
            return self.session.query(OrderItem).filter(OrderItem.id == order_item_id).first()
        except Exception as e:
            logger.error(f"Failed to get order item by id {order_item_id}: {e}")
            return None

    def get_all_by_order(self, order_id: int) -> list[OrderItem] | list:
        try:
            return self.session.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        except Exception as e:
            logger.error(f"Failed to get order items for order {order_id}: {e}")
            return []

    def update(self, order_item_id: int, data: dict) -> bool:
        try:
            order_item = self.get_by_id(order_item_id)
            if not order_item:
                logger.error(f"Order item not found with id {order_item_id}")
                return False
            for key, value in data.items():
                if hasattr(order_item, key):
                    setattr(order_item, key, value)
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update order item {order_item_id}: {e}")
            self.session.rollback()
            return False

    def delete(self, order_item_id: int) -> bool:
        try:
            order_item = self.get_by_id(order_item_id)
            if not order_item:
                logger.error(f"Order item not found with id {order_item_id}")
                return False
            self.session.delete(order_item)
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to delete order item {order_item_id}: {e}")
            self.session.rollback()
            return False
