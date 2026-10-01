from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import Index
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db, login_manager


def _utcnow():
    """Timezone-aware UTC-время (замена устаревшему datetime.utcnow())."""
    return datetime.now(timezone.utc)


# =========================================================
#  ПОЛЬЗОВАТЕЛИ И РОЛИ
# =========================================================

class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False)

    users = db.relationship("User", back_populates="role", lazy="selectin")

    def __repr__(self):
        return f"<Role {self.code}>"


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active_flag = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=_utcnow, index=True)

    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"),
                        nullable=False, index=True)
    role = db.relationship("Role", back_populates="users", lazy="joined")

    def set_password(self, password):
        from config import Config
        self.password_hash = generate_password_hash(
            password, method=Config.PASSWORD_HASH_METHOD
        )

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.is_active_flag

    def has_role(self, *codes):
        return self.role and self.role.code in codes

    def __repr__(self):
        return f"<User {self.username}>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# =========================================================
#  СПРАВОЧНИКИ
# =========================================================

class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)

    products = db.relationship("Product", back_populates="category",
                               lazy="selectin")

    def __repr__(self):
        return f"<Category {self.name}>"


class Unit(db.Model):
    __tablename__ = "units"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16), unique=True, nullable=False)

    def __repr__(self):
        return f"<Unit {self.name}>"


class Warehouse(db.Model):
    __tablename__ = "warehouses"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    address = db.Column(db.String(255))

    def __repr__(self):
        return f"<Warehouse {self.name}>"


class StorageLocation(db.Model):
    __tablename__ = "storage_locations"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), nullable=False, index=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"),
                             nullable=False, index=True)

    warehouse = db.relationship("Warehouse", lazy="joined")

    __table_args__ = (db.UniqueConstraint("warehouse_id", "code"),)

    def __repr__(self):
        return f"<Location {self.warehouse_id}/{self.code}>"


class Supplier(db.Model):
    __tablename__ = "suppliers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False, index=True)
    inn = db.Column(db.String(20))
    phone = db.Column(db.String(32))

    def __repr__(self):
        return f"<Supplier {self.name}>"


class Customer(db.Model):
    __tablename__ = "customers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False, index=True)
    inn = db.Column(db.String(20))
    phone = db.Column(db.String(32))

    def __repr__(self):
        return f"<Customer {self.name}>"


# =========================================================
#  ТОВАРЫ
# =========================================================

class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(32), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey("units.id"))
    min_stock = db.Column(db.Numeric(12, 3), default=0)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=_utcnow, index=True)

    category = db.relationship("Category", back_populates="products",
                               lazy="joined")
    unit = db.relationship("Unit", lazy="joined")

    __table_args__ = (
        Index("ix_product_active_name", "is_active", "name"),
    )

    def __repr__(self):
        return f"<Product {self.sku}>"


# =========================================================
#  ПРИЁМКА
# =========================================================

class ReceiptDoc(db.Model):
    __tablename__ = "receipt_docs"
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(32), unique=True, nullable=False, index=True)
    doc_date = db.Column(db.Date, default=_utcnow, index=True)
    comment = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    created_at = db.Column(db.DateTime, default=_utcnow, index=True)

    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"),
                            nullable=False, index=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"),
                             nullable=False, index=True)
    is_cancelled = db.Column(db.Boolean, default=False, index=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancelled_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    supplier = db.relationship("Supplier", lazy="joined")
    warehouse = db.relationship("Warehouse", lazy="joined")
    items = db.relationship("ReceiptItem", back_populates="doc",
                            cascade="all, delete-orphan", lazy="selectin")
    canceller = db.relationship("User", foreign_keys=[cancelled_by], lazy="joined")
    def __repr__(self):
        return f"<ReceiptDoc {self.number}>"


class ReceiptItem(db.Model):
    __tablename__ = "receipt_items"
    id = db.Column(db.Integer, primary_key=True)
    doc_id = db.Column(db.Integer, db.ForeignKey("receipt_docs.id"),
                       nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"),
                           nullable=False, index=True)
    location_id = db.Column(db.Integer, db.ForeignKey("storage_locations.id"),
                            index=True)
    quantity = db.Column(db.Numeric(12, 3), nullable=False)
    price = db.Column(db.Numeric(12, 2), default=0)

    doc = db.relationship("ReceiptDoc", back_populates="items")
    product = db.relationship("Product", lazy="joined")
    location = db.relationship("StorageLocation", lazy="joined")


# =========================================================
#  ОТГРУЗКА
# =========================================================

class ShipmentDoc(db.Model):
    __tablename__ = "shipment_docs"
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(32), unique=True, nullable=False, index=True)
    doc_date = db.Column(db.Date, default=_utcnow, index=True)
    comment = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    created_at = db.Column(db.DateTime, default=_utcnow, index=True)

    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"),
                            nullable=False, index=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"),
                             nullable=False, index=True)
    is_cancelled = db.Column(db.Boolean, default=False, index=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancelled_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    customer = db.relationship("Customer", lazy="joined")
    warehouse = db.relationship("Warehouse", lazy="joined")
    items = db.relationship("ShipmentItem", back_populates="doc",
                            cascade="all, delete-orphan", lazy="selectin")
    canceller = db.relationship("User", foreign_keys=[cancelled_by], lazy="joined")
    def __repr__(self):
        return f"<ShipmentDoc {self.number}>"


class ShipmentItem(db.Model):
    __tablename__ = "shipment_items"
    id = db.Column(db.Integer, primary_key=True)
    doc_id = db.Column(db.Integer, db.ForeignKey("shipment_docs.id"),
                       nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"),
                           nullable=False, index=True)
    location_id = db.Column(db.Integer, db.ForeignKey("storage_locations.id"),
                            index=True)
    quantity = db.Column(db.Numeric(12, 3), nullable=False)
    price = db.Column(db.Numeric(12, 2), default=0)

    doc = db.relationship("ShipmentDoc", back_populates="items")
    product = db.relationship("Product", lazy="joined")
    location = db.relationship("StorageLocation", lazy="joined")


# =========================================================
#  ПЕРЕМЕЩЕНИЕ
# =========================================================

class TransferDoc(db.Model):
    __tablename__ = "transfer_docs"
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(32), unique=True, nullable=False, index=True)
    doc_date = db.Column(db.Date, default=_utcnow, index=True)
    comment = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    created_at = db.Column(db.DateTime, default=_utcnow, index=True)

    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"),
                             nullable=False, index=True)
    is_cancelled = db.Column(db.Boolean, default=False, index=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancelled_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    warehouse = db.relationship("Warehouse", lazy="joined")
    items = db.relationship("TransferItem", back_populates="doc",
                            cascade="all, delete-orphan", lazy="selectin")
    canceller = db.relationship("User", foreign_keys=[cancelled_by], lazy="joined")
    def __repr__(self):
        return f"<TransferDoc {self.number}>"


class TransferItem(db.Model):
    __tablename__ = "transfer_items"
    id = db.Column(db.Integer, primary_key=True)
    doc_id = db.Column(db.Integer, db.ForeignKey("transfer_docs.id"),
                       nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"),
                           nullable=False, index=True)
    from_location_id = db.Column(db.Integer, db.ForeignKey("storage_locations.id"))
    to_location_id = db.Column(db.Integer, db.ForeignKey("storage_locations.id"))
    quantity = db.Column(db.Numeric(12, 3), nullable=False)

    doc = db.relationship("TransferDoc", back_populates="items")
    product = db.relationship("Product", lazy="joined")
    from_location = db.relationship("StorageLocation",
                                    foreign_keys=[from_location_id], lazy="joined")
    to_location = db.relationship("StorageLocation",
                                  foreign_keys=[to_location_id], lazy="joined")


# =========================================================
#  СПИСАНИЕ
# =========================================================

class WriteOffDoc(db.Model):
    __tablename__ = "writeoff_docs"
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(32), unique=True, nullable=False, index=True)
    doc_date = db.Column(db.Date, default=_utcnow, index=True)
    comment = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    created_at = db.Column(db.DateTime, default=_utcnow, index=True)

    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"),
                             nullable=False, index=True)
    reason = db.Column(db.String(255))
    is_cancelled = db.Column(db.Boolean, default=False, index=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancelled_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    warehouse = db.relationship("Warehouse", lazy="joined")
    items = db.relationship("WriteOffItem", back_populates="doc",
                            cascade="all, delete-orphan", lazy="selectin")
    canceller = db.relationship("User", foreign_keys=[cancelled_by], lazy="joined")
    def __repr__(self):
        return f"<WriteOffDoc {self.number}>"


class WriteOffItem(db.Model):
    __tablename__ = "writeoff_items"
    id = db.Column(db.Integer, primary_key=True)
    doc_id = db.Column(db.Integer, db.ForeignKey("writeoff_docs.id"),
                       nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"),
                           nullable=False, index=True)
    location_id = db.Column(db.Integer, db.ForeignKey("storage_locations.id"),
                            index=True)
    quantity = db.Column(db.Numeric(12, 3), nullable=False)

    doc = db.relationship("WriteOffDoc", back_populates="items")
    product = db.relationship("Product", lazy="joined")
    location = db.relationship("StorageLocation", lazy="joined")


# =========================================================
#  ИНВЕНТАРИЗАЦИЯ
# =========================================================

class InventoryDoc(db.Model):
    __tablename__ = "inventory_docs"
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(32), unique=True, nullable=False, index=True)
    doc_date = db.Column(db.Date, default=_utcnow, index=True)
    comment = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    created_at = db.Column(db.DateTime, default=_utcnow, index=True)

    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"),
                             nullable=False, index=True)
    status = db.Column(db.String(16), default="draft", index=True)

    warehouse = db.relationship("Warehouse", lazy="joined")
    items = db.relationship("InventoryItem", back_populates="doc",
                            cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self):
        return f"<InventoryDoc {self.number}>"


class InventoryItem(db.Model):
    __tablename__ = "inventory_items"
    id = db.Column(db.Integer, primary_key=True)
    doc_id = db.Column(db.Integer, db.ForeignKey("inventory_docs.id"),
                       nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"),
                           nullable=False, index=True)
    location_id = db.Column(db.Integer, db.ForeignKey("storage_locations.id"),
                            index=True)
    fact_qty = db.Column(db.Numeric(12, 3), nullable=False)

    doc = db.relationship("InventoryDoc", back_populates="items")
    product = db.relationship("Product", lazy="joined")
    location = db.relationship("StorageLocation", lazy="joined")


# =========================================================
#  ОСТАТКИ
# =========================================================

class Stock(db.Model):
    __tablename__ = "stocks"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"),
                           nullable=False, index=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"),
                             nullable=False, index=True)
    location_id = db.Column(db.Integer, db.ForeignKey("storage_locations.id"),
                            index=True)
    quantity = db.Column(db.Numeric(12, 3), default=0, nullable=False)
    reserved = db.Column(db.Numeric(12, 3), default=0, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("product_id", "warehouse_id", "location_id",
                            name="uq_stock"),
        Index("ix_stock_product_wh", "product_id", "warehouse_id"),
    )

    product = db.relationship("Product", lazy="joined")
    warehouse = db.relationship("Warehouse", lazy="joined")
    location = db.relationship("StorageLocation", lazy="joined")

    @property
    def available(self):
        return (self.quantity or 0) - (self.reserved or 0)

    def __repr__(self):
        return f"<Stock p={self.product_id} w={self.warehouse_id} q={self.quantity}>"


# =========================================================
#  ЖУРНАЛ ДЕЙСТВИЙ
# =========================================================

# Человеко-понятные названия действий
ACTION_TITLES = {
    "login": "Вход в систему",
    "logout": "Выход из системы",
    "login_failed": "Неудачная попытка входа",
    "create_product": "Добавлен товар",
    "edit_product": "Изменён товар",
    "deactivate_product": "Товар снят с учёта",
    "create_receipt": "Создана приёмка",
    "create_shipment": "Создана отгрузка",
    "create_transfer": "Создано перемещение",
    "create_writeoff": "Создано списание",
    "create_inventory": "Создана инвентаризация",
    "apply_inventory": "Проведена инвентаризация",
    "create_user": "Создан пользователь",
    "toggle_user": "Изменён статус пользователя",
}

# Человеко-понятные названия объектов
ENTITY_TITLES = {
    "User": "Пользователь",
    "Product": "Товар",
    "ReceiptDoc": "Документ приёмки",
    "ShipmentDoc": "Документ отгрузки",
    "TransferDoc": "Документ перемещения",
    "WriteOffDoc": "Документ списания",
    "InventoryDoc": "Инвентаризация",
    "SECURITY": "Событие безопасности",
}


class ActionLog(db.Model):
    __tablename__ = "action_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    action = db.Column(db.String(64), nullable=False, index=True)
    entity = db.Column(db.String(64), index=True)
    entity_id = db.Column(db.Integer, index=True)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=_utcnow, index=True)

    user = db.relationship("User", lazy="joined")

    __table_args__ = (
        Index("ix_log_created_action", "created_at", "action"),
    )

    @property
    def action_human(self):
        return ACTION_TITLES.get(self.action, self.action)

    @property
    def entity_human(self):
        if not self.entity:
            return ""
        return ENTITY_TITLES.get(self.entity, self.entity)

    @property
    def details_human(self):
        if not self.details:
            return ""

        if self.action == "login" and self.details.startswith("username="):
            return self.details.replace("username=", "Логин: ")

        if self.action == "create_user":
            return f"Логин: {self.details}"

        if self.action == "toggle_user":
            if "active=True" in self.details:
                return "Разблокирован"
            if "active=False" in self.details:
                return "Заблокирован"
            return self.details

        if self.action in ("create_product", "edit_product", "deactivate_product"):
            return self.details.replace("SKU=", "Артикул: ")

        if self.action in (
            "create_receipt", "create_shipment", "create_transfer",
            "create_writeoff", "create_inventory", "apply_inventory",
        ):
            return f"Номер: {self.details}"

        return self.details

    def __repr__(self):
        return f"<ActionLog {self.action}>"