from app import create_app
from app.extensions import db
from app.models import User, Product, Customer
from app.security import hash_password

app = create_app()

with app.app_context():
    db.create_all()

    demo_users = [
        ("admin@securestock.example.com", "System Admin", "admin"),
        ("manager@securestock.example.com", "Store Manager", "manager"),
        ("employee@securestock.example.com", "Sales Employee", "employee"),
    ]

    for email, name, role in demo_users:
        if not User.query.filter_by(email=email).first():
            user = User(
                email=email,
                name=name,
                role=role,
                password_hash=hash_password("ChangeMe123!"),
            )
            db.session.add(user)

    if Product.query.count() == 0:
        db.session.add_all([
            Product(name="Laptop", description="Business laptop", price=850.00, quantity=10, low_stock_threshold=2),
            Product(name="Wireless Mouse", description="USB wireless mouse", price=25.00, quantity=30, low_stock_threshold=5),
            Product(name="Keyboard", description="Mechanical keyboard", price=60.00, quantity=15, low_stock_threshold=3),
        ])

    if Customer.query.count() == 0:
        db.session.add(Customer(
            name="Demo Customer",
            email="customer@example.com",
            phone_encrypted=None,
        ))

    db.session.commit()
    print("Database initialized.")
    print("Demo password for all three users: ChangeMe123!")
