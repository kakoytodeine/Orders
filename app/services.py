from app.db.repositories import UserRepository, ProductRepository, OrderRepository, OrderItemRepository, \
    CategoryRepository
from sqlalchemy.orm import Session
from app.db.models import User, Product, Order, Category, OrderItem


class UserService:
    """Сервис для работы с пользователями"""
    
    def __init__(self, session: Session):
        self.session = session
        self.user_repo = UserRepository(session)
    
    def get_user_by_id(self, user_id: int) -> User | None:
        """Получить пользователя по ID"""
        return self.user_repo.get_user_by_id(user_id)
    
    def create_user(self, tg_id: int, username: str, first_name: str) -> User:
        """Создать нового пользователя или вернуть существующего"""
        user = self.user_repo.get_user_by_tg_id(tg_id=tg_id)
        if user:
            return user
        return self.user_repo.create_user(tg_id, username, first_name)
    
    def get_role_user(self, user_id: int) -> str:
        """Получить роль пользователя (например, admin или user)"""
        user = self.get_user_by_id(user_id)
        if user is None:
            return 'user'
        return user.role or 'user'
    
    def get_user_by_tg_id(self, tg_id: int) -> User | None:
        return self.user_repo.get_user_by_tg_id(tg_id=tg_id)


class ProductService:
    """Сервис для работы с продуктами"""
    
    def __init__(self, session: Session):
        self.session = session
        self.repo_product = ProductRepository(session)
        self.repo_user = UserRepository(session)
    
    def get_products_by_category(self, category_id: int) -> list[Product]:
        """Получить список продуктов по категории"""
        products = self.repo_product.get_all_by_category(category_id)
        if products:
            return products
        return []
    
    def get_product_by_id(self, product_id: int):
        return self.repo_product.get_by_id(product_id)
    
    def get_product_by_name_in_category(self, product_name: str, category_id: int) -> Product:
        return self.repo_product.get_product_by_name(product_name, category_id)
    
    def create_product_for_admin(
            self,
            name: str,
            target_quantity: int,
            category_id: int,
            photo_url: str = None):
        new_product = self.repo_product.create(name, target_quantity, category_id, photo_url)
        if new_product:
            return Product
        else:
            return None
    
    def delete_product_for_admin(self, product_id: int) -> bool:
        """Удалить продукт (только для администратора)"""
        return self.repo_product.delete(product_id=product_id)
    
    def update_product_quantity_for_admin(self, product_id: int, new_quantity: int, user_id: int) -> dict:
        """Обновить целевое количество продукта (только для администратора)"""
        user = self.repo_user.get_user_by_id(user_id)
        if user and user.role == 'admin':
            result = self.repo_product.update_target_quantity(product_id, new_quantity)
            if result:
                return {"success": True, "message": "Количество успешно обновлено"}
            return {"success": False, "message": "Ошибка при обновлении количества"}
        return {"success": False, "message": "Ошибка: недостаточно прав"}


class OrderService:
    """Сервис для работы с заказами"""
    
    def __init__(self, session: Session):
        self.session = session
        self.repo_order = OrderRepository(session)
        self.repo_order_item = OrderItemRepository(session)
        self.repo_product = ProductRepository(session)
    
    def create_order(self, user_id: int, category_id: int, items: list[dict]) -> dict:
        """
        Создать новый заказ с позициями.
        items — список словарей с ключами: product_id, actual_quantity
        """
        order = self.repo_order.create(user_id, category_id)
        if not order:
            return {"success": False, "message": "Ошибка при создании заказа"}
        order_items = []
        for item in items:
            product = self.repo_product.get_by_id(item['product_id'])
            if not product:
                continue
            actual_quantity = item.get('actual_quantity', 0)
            to_order = max(product.target_quantity - actual_quantity, 0)
            order_items.append({
                'product_id': item['product_id'],
                'actual_quantity': actual_quantity,
                'to_order': to_order
            })
        self.repo_order_item.add_items(order.id, order_items)
        return {"success": True, "message": "Заказ создан", "order_id": order.id}
    
    def add_items(self, order_id: int, items: list[dict]) -> dict:
        """Добавить позиции в существующий заказ"""
        order = self.repo_order.get_by_id(order_id)
        if not order:
            return {"success": False, "message": "Заказ не найден"}
        order_items = []
        for item in items:
            product = self.repo_product.get_by_id(item['product_id'])
            if not product:
                continue
            actual_quantity = item.get('actual_quantity', 0)
            to_order = max(product.target_quantity - actual_quantity, 0)
            order_items.append({
                'product_id': item['product_id'],
                'actual_quantity': actual_quantity,
                'to_order': to_order
            })
        self.repo_order_item.add_items(order_id, order_items)
        return {"success": True, "message": "Позиции добавлены"}
    
    def get_last_order(self, user_id: int) -> Order | None:
        """Получить последний заказ пользователя"""
        return self.repo_order.get_last_by_user(user_id)

    def get_order_report(self, order_id: int) -> dict:
        """Получить отчет по заказу с позициями и количеством"""
        order = self.repo_order.get_by_id(order_id)
        if not order:
            return {"success": False, "message": "Заказ не найден"}
        items = self.repo_order_item.get_all_by_order(order_id)
        report = []
        for item in items:
            product = self.repo_product.get_by_id(item.product_id)
            report.append({
                'product_id': item.product_id,
                'product_name': product.name if product else None,
                'actual_quantity': item.actual_quantity,
                'to_order': item.to_order,
                'target_quantity': product.target_quantity if product else None
            })
        return {"success": True, "order_id": order_id, "items": report}


class CategoryService:
    """Сервис для работы с категориями"""
    
    def __init__(self, session: Session):
        self.session = session
        self.repo_category = CategoryRepository(session)
    
    def get_all_categories(self) -> dict:
        """Получить все категории"""
        categories = self.repo_category.get_all_categories()
        return categories
    
    def get_category_by_id(self, category_id: int) -> Category | None:
        """Получить категорию по ID"""
        return self.repo_category.get_category_by_id(category_id)
    
    def get_category_by_name(self, category_name: str):
        return self.repo_category.get_category_by_name(category_name)
    
    def create_category(self, name: str) -> Category | None:
        """Создать новую категорию"""
        return self.repo_category.create_category(name)
    
    def delete_category(self, category_id: int) -> dict:
        """Удалить категорию по ID"""
        result = self.repo_category.delete_category(category_id)
        if not result:
            return {"success": False, "message": "Ошибка при удалении категории"}
        return {"success": True, "message": "Категория удалена"}
