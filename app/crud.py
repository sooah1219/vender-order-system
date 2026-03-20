from sqlalchemy.orm import Session
from app.models import Vendor, Item


def create_vendor(db: Session, name: str, phone: str, available_days: str):
    vendor = Vendor(
        name=name,
        phone=phone,
        available_days=available_days
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


def get_vendors(db: Session):
    return db.query(Vendor).all()


def get_vendor_by_id(db: Session, vendor_id: int):
    return db.query(Vendor).filter(Vendor.id == vendor_id).first()


def get_items(db: Session):
    return db.query(Item).all()


def get_items_by_vendor(db: Session, vendor_id: int):
    return db.query(Item).filter(Item.vendor_id == vendor_id).all()


def create_item(db: Session, vendor_id: int, name: str, unit_price: int | None):
    item = Item(
        name=name,
        unit_price=unit_price,
        vendor_id=vendor_id
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_item_by_id(db: Session, item_id: int):
    return db.query(Item).filter(Item.id == item_id).first()


def delete_item(db: Session, item_id: int):
    item = db.query(Item).filter(Item.id == item_id).first()

    if item:
        db.delete(item)
        db.commit()

    return item