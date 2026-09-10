# SecureStock ERD (text representation)

```text
USER
-----
id PK
email UNIQUE
name
password_hash
role
failed_attempts
locked_until

CUSTOMER
--------
id PK
name
email
phone_encrypted

PRODUCT
-------
id PK
name
description
price
quantity
low_stock_threshold

SALE
----
id PK
customer_id FK -> CUSTOMER.id
user_id FK -> USER.id
total
created_at

SALE_ITEM
---------
id PK
sale_id FK -> SALE.id
product_id FK -> PRODUCT.id
quantity
unit_price

AUDIT_LOG
---------
id PK
user_id FK -> USER.id
action
entity
entity_id
ip_address
created_at

Relationships:
USER 1 ---- N SALE
CUSTOMER 1 ---- N SALE
SALE 1 ---- N SALE_ITEM
PRODUCT 1 ---- N SALE_ITEM
USER 1 ---- N AUDIT_LOG
```
