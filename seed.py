from app.database import SessionLocal
from app.models import Vendor

db = SessionLocal()

# vendor = Vendor(
#   name="Big Brothers Food",
#   phone="7788796281"
# )

# db.add(vendor)
# db.commit()



vendor_data = [
  {"name": "Big Brothers Food", "phone": "7788796281"},
  {"name": "Wismettac", "phone": "7788796281"},
  {"name": "Canaan Meat", "phone": "7788796281"},
  {"name": "JFC", "phone": "7788796281"},
  {"name": "D-way", "phone": "7788796281"},
  {"name": "Ecopac", "phone": "7788796281"},
  {"name": "Don", "phone": "7788796281"},
]

for item in vendor_data :
  existing = db.query(Vendor).filter(Vendor.name == item["name"]).first()
  if not existing:
    db.add(Vendor(name=item["name"], phone=item["phone"]))

db.commit()
db.close()

print("seed complete.")