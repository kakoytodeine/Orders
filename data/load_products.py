from itertools import product

from pandas import read_excel

from app.db.db_session import SessionLocal
from app.services import ProductService

df = read_excel("data_product.xlsx", usecols=[0, 1])

for name, quantity in zip(df.iloc[:, 0], df.iloc[:, 1]):
    with SessionLocal() as session:
        product_service = ProductService(session=session)
        q = quantity if isinstance(quantity, int) else 0
        product_service.create_product_for_admin(name, q, 1)