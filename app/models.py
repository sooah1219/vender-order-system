from datetime import datetime

from sqlalchemy import String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    available_days: Mapped[str | None] = mapped_column(String, nullable=True)

    items = relationship(
        "Item",
        back_populates="vendor",
        cascade="all, delete-orphan"
    )

    orders = relationship(
        "OrderHistory",
        back_populates="vendor",
        cascade="all, delete-orphan"
    )


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String, nullable=False)

    unit_price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    vendor_id: Mapped[int] = mapped_column(
        ForeignKey("vendors.id"),
        nullable=False
    )

    vendor = relationship(
        "Vendor",
        back_populates="items"
    )


class OrderHistory(Base):
    __tablename__ = "order_history"

    id: Mapped[int] = mapped_column(primary_key=True)

    vendor_id: Mapped[int] = mapped_column(
        ForeignKey("vendors.id"),
        nullable=False
    )

    vendor_name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    ordered_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    order_items_text: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    total_amount: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False
    )

    vendor = relationship(
        "Vendor",
        back_populates="orders"
    )