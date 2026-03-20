from app.database import SessionLocal
from app.models import Vendor

db = SessionLocal()

vendor_data = [
  {"name": "Big Brothers Food", "phone": "7781234567"},
  {"name": "Wismettac", "phone": "7781234567"},
  {"name": "Canaan Meat", "phone": "7781234567"},
  {"name": "JFC", "phone": "7781234567"},
  {"name": "D-way", "phone": "7781234567"},
  {"name": "Ecopac", "phone": "7781234567"},
  {"name": "Don", "phone": "7781234567"},
]

for item in vendor_data :
  existing = db.query(Vendor).filter(Vendor.name == item["name"]).first()
  if not existing:
    db.add(Vendor(name=item["name"], phone=item["phone"]))

db.commit()
db.close()

print("seed complete.")