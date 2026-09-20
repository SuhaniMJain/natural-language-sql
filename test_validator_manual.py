"""Temporary manual checks for the SQL validator."""

from app.sql_validator import validate_sql


cases = [
    ("SELECT * FROM customers", True),
    ("SELECT name FROM customers;", True),
    ("SELECT c.name, SUM(o.total_amount) FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.name", True),
    ("DELETE FROM customers", False),
    ("DROP TABLE customers", False),
    ("UPDATE customers SET name = 'Test'", False),
    ("SELECT * FROM customers; DROP TABLE customers;", False),
    ("INSERT INTO customers (name) VALUES ('Test')", False),
    ("", False),
]


for sql, should_be_valid in cases:
    print(f"SQL: {sql!r}")
    try:
        validate_sql(sql)
        actual_is_valid = True
    except ValueError as error:
        actual_is_valid = False
        print(f"Validation error: {error}")

    if actual_is_valid == should_be_valid:
        print("PASS")
    else:
        print("FAIL")
    print()
