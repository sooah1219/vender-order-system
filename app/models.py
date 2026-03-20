from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    available_days: Mapped[str] = mapped_column(String, nullable=True)

    items = relationship("Item", back_populates="vendor", cascade="all, delete-orphan")


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String, nullable=False)

    unit_price: Mapped[int | None] = mapped_column(Integer, nullable=True)

    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), nullable=False)

    vendor = relationship("Vendor", back_populates="items")