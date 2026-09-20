"""Create and seed a small synthetic SQLite database for local development."""

from datetime import date
from pathlib import Path

from sqlalchemy import (
	Column,
	Date,
	Float,
	ForeignKey,
	Integer,
	MetaData,
	String,
	Table,
	create_engine,
	func,
	select,
)
from sqlalchemy.engine import Engine


DATABASE_PATH = Path(__file__).resolve().parent / "database.db"
metadata = MetaData()

customers = Table(
	"customers",
	metadata,
	Column("customer_id", Integer, primary_key=True),
	Column("name", String, nullable=False),
	Column("city", String, nullable=False),
	Column("email", String, nullable=False),
	Column("signup_date", Date, nullable=False),
)

products = Table(
	"products",
	metadata,
	Column("product_id", Integer, primary_key=True),
	Column("product_name", String, nullable=False),
	Column("category", String, nullable=False),
	Column("price", Float, nullable=False),
)

orders = Table(
	"orders",
	metadata,
	Column("order_id", Integer, primary_key=True),
	Column("customer_id", Integer, ForeignKey("customers.customer_id"), nullable=False),
	Column("order_date", Date, nullable=False),
	Column("total_amount", Float, nullable=False),
)

order_items = Table(
	"order_items",
	metadata,
	Column("order_item_id", Integer, primary_key=True),
	Column("order_id", Integer, ForeignKey("orders.order_id"), nullable=False),
	Column("product_id", Integer, ForeignKey("products.product_id"), nullable=False),
	Column("quantity", Integer, nullable=False),
	Column("unit_price", Float, nullable=False),
)


def create_tables(engine: Engine) -> None:
	"""Create the demo tables if they do not already exist."""
	metadata.create_all(engine)


def seed_data(engine: Engine) -> bool:
	"""Insert synthetic demo business data once.

	Returns:
		``True`` when records were inserted, or ``False`` when the database
		already contained customer records and was left unchanged.
	"""
	customer_rows = [
		{"customer_id": 1, "name": "Ava Morgan", "city": "Austin", "email": "ava.morgan@example.com", "signup_date": date(2023, 1, 15)},
		{"customer_id": 2, "name": "Liam Chen", "city": "Seattle", "email": "liam.chen@example.com", "signup_date": date(2023, 2, 28)},
		{"customer_id": 3, "name": "Sofia Patel", "city": "Chicago", "email": "sofia.patel@example.com", "signup_date": date(2023, 4, 10)},
		{"customer_id": 4, "name": "Noah Williams", "city": "Denver", "email": "noah.williams@example.com", "signup_date": date(2023, 6, 5)},
		{"customer_id": 5, "name": "Mia Thompson", "city": "Boston", "email": "mia.thompson@example.com", "signup_date": date(2023, 8, 19)},
		{"customer_id": 6, "name": "Ethan Garcia", "city": "Austin", "email": "ethan.garcia@example.com", "signup_date": date(2023, 10, 2)},
	]
	product_rows = [
		{"product_id": 1, "product_name": "Wireless Keyboard", "category": "Electronics", "price": 49.99},
		{"product_id": 2, "product_name": "USB-C Hub", "category": "Electronics", "price": 34.50},
		{"product_id": 3, "product_name": "Insulated Water Bottle", "category": "Home", "price": 24.00},
		{"product_id": 4, "product_name": "Desk Lamp", "category": "Home", "price": 39.95},
		{"product_id": 5, "product_name": "Notebook Set", "category": "Office", "price": 12.75},
		{"product_id": 6, "product_name": "Ballpoint Pen Pack", "category": "Office", "price": 8.25},
		{"product_id": 7, "product_name": "Laptop Stand", "category": "Accessories", "price": 59.00},
		{"product_id": 8, "product_name": "Webcam Cover", "category": "Accessories", "price": 6.50},
	]
	order_rows = [
		{"order_id": 1, "customer_id": 1, "order_date": date(2024, 1, 8), "total_amount": 84.49},
		{"order_id": 2, "customer_id": 2, "order_date": date(2024, 1, 22), "total_amount": 59.00},
		{"order_id": 3, "customer_id": 3, "order_date": date(2024, 2, 14), "total_amount": 64.50},
		{"order_id": 4, "customer_id": 1, "order_date": date(2024, 2, 27), "total_amount": 51.00},
		{"order_id": 5, "customer_id": 4, "order_date": date(2024, 3, 3), "total_amount": 99.90},
		{"order_id": 6, "customer_id": 5, "order_date": date(2024, 3, 18), "total_amount": 47.25},
		{"order_id": 7, "customer_id": 6, "order_date": date(2024, 4, 9), "total_amount": 65.50},
		{"order_id": 8, "customer_id": 2, "order_date": date(2024, 4, 21), "total_amount": 88.75},
		{"order_id": 9, "customer_id": 3, "order_date": date(2024, 5, 6), "total_amount": 118.00},
		{"order_id": 10, "customer_id": 4, "order_date": date(2024, 5, 24), "total_amount": 73.50},
		{"order_id": 11, "customer_id": 5, "order_date": date(2024, 6, 11), "total_amount": 36.75},
		{"order_id": 12, "customer_id": 6, "order_date": date(2024, 6, 29), "total_amount": 118.00},
	]
	order_item_rows = [
		{"order_item_id": 1, "order_id": 1, "product_id": 1, "quantity": 1, "unit_price": 49.99},
		{"order_item_id": 2, "order_id": 1, "product_id": 5, "quantity": 2, "unit_price": 12.75},
		{"order_item_id": 3, "order_id": 1, "product_id": 6, "quantity": 1, "unit_price": 8.25},
		{"order_item_id": 4, "order_id": 2, "product_id": 7, "quantity": 1, "unit_price": 59.00},
		{"order_item_id": 5, "order_id": 3, "product_id": 2, "quantity": 1, "unit_price": 34.50},
		{"order_item_id": 6, "order_id": 3, "product_id": 3, "quantity": 1, "unit_price": 24.00},
		{"order_item_id": 7, "order_id": 3, "product_id": 8, "quantity": 1, "unit_price": 6.50},
		{"order_item_id": 8, "order_id": 4, "product_id": 3, "quantity": 2, "unit_price": 24.00},
		{"order_item_id": 9, "order_id": 4, "product_id": 6, "quantity": 1, "unit_price": 3.00},
		{"order_item_id": 10, "order_id": 5, "product_id": 1, "quantity": 2, "unit_price": 49.95},
		{"order_item_id": 11, "order_id": 6, "product_id": 5, "quantity": 3, "unit_price": 12.75},
		{"order_item_id": 12, "order_id": 6, "product_id": 6, "quantity": 1, "unit_price": 9.00},
		{"order_item_id": 13, "order_id": 7, "product_id": 2, "quantity": 1, "unit_price": 34.50},
		{"order_item_id": 14, "order_id": 7, "product_id": 4, "quantity": 1, "unit_price": 31.00},
		{"order_item_id": 15, "order_id": 8, "product_id": 7, "quantity": 1, "unit_price": 59.00},
		{"order_item_id": 16, "order_id": 8, "product_id": 8, "quantity": 1, "unit_price": 6.50},
		{"order_item_id": 17, "order_id": 8, "product_id": 5, "quantity": 2, "unit_price": 11.625},
		{"order_item_id": 18, "order_id": 9, "product_id": 7, "quantity": 2, "unit_price": 59.00},
		{"order_item_id": 19, "order_id": 10, "product_id": 4, "quantity": 1, "unit_price": 39.95},
		{"order_item_id": 20, "order_id": 10, "product_id": 3, "quantity": 1, "unit_price": 24.00},
		{"order_item_id": 21, "order_id": 10, "product_id": 8, "quantity": 1, "unit_price": 9.55},
		{"order_item_id": 22, "order_id": 11, "product_id": 5, "quantity": 1, "unit_price": 12.75},
		{"order_item_id": 23, "order_id": 11, "product_id": 6, "quantity": 2, "unit_price": 12.00},
		{"order_item_id": 24, "order_id": 12, "product_id": 1, "quantity": 1, "unit_price": 49.99},
		{"order_item_id": 25, "order_id": 12, "product_id": 4, "quantity": 1, "unit_price": 39.95},
		{"order_item_id": 26, "order_id": 12, "product_id": 8, "quantity": 1, "unit_price": 28.06},
	]

	with engine.begin() as connection:
		existing_customer = connection.execute(select(func.count()).select_from(customers)).scalar_one()
		if existing_customer:
			return False

		connection.execute(customers.insert(), customer_rows)
		connection.execute(products.insert(), product_rows)
		connection.execute(orders.insert(), order_rows)
		connection.execute(order_items.insert(), order_item_rows)

	return True


def main() -> None:
	"""Create the database and seed it with synthetic demo data."""
	DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
	engine = create_engine(f"sqlite:///{DATABASE_PATH.as_posix()}")
	try:
		create_tables(engine)
		inserted = seed_data(engine)
		status = "seeded" if inserted else "already contained demo data"
		print(f"Demo database {status}: {DATABASE_PATH}")
	finally:
		engine.dispose()


if __name__ == "__main__":
	main()
