from datetime import datetime, time

from sqlalchemy.orm import Session

from app.models import Vendor, Item, OrderHistory


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
    return db.query(Vendor).order_by(Vendor.name.asc()).all()


def get_vendor_by_id(db: Session, vendor_id: int):
    return db.query(Vendor).filter(Vendor.id == vendor_id).first()


def get_items(db: Session):
    return db.query(Item).all()


def get_items_by_vendor(db: Session, vendor_id: int):
    return (
        db.query(Item)
        .filter(Item.vendor_id == vendor_id)
        .order_by(Item.name.asc())
        .all()
    )


def create_item(db: Session, vendor_id: int, name: str, unit_price: float | None):
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


def create_order_history(
    db: Session,
    vendor_id: int,
    vendor_name: str,
    order_items_text: str,
    total_amount: float,
):
    order = OrderHistory(
        vendor_id=vendor_id,
        vendor_name=vendor_name,
        order_items_text=order_items_text,
        total_amount=total_amount,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def get_order_history(
    db: Session,
    vendor_id: int | None = None,
    order_date: str | None = None,
):
    query = db.query(OrderHistory)

    if vendor_id:
        query = query.filter(OrderHistory.vendor_id == vendor_id)

    if order_date:
        try:
            selected_date = datetime.strptime(order_date, "%Y-%m-%d").date()
            start_dt = datetime.combine(selected_date, time.min)
            end_dt = datetime.combine(selected_date, time.max)
            query = query.filter(OrderHistory.ordered_at >= start_dt)
            query = query.filter(OrderHistory.ordered_at <= end_dt)
        except ValueError:
            pass

    return query.order_by(OrderHistory.ordered_at.desc()).all()