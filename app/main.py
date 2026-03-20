from fastapi import FastAPI, Depends, Request, Form
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime

from app.database import SessionLocal, engine, Base
from app.crud import (
    create_vendor,
    get_vendors,
    get_vendor_by_id,
    get_items_by_vendor,
    create_item,
)
from app.models import Item
from app.sms import send_order_sms

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/vendors", response_class=HTMLResponse)
def list_vendors(request: Request, db: Session = Depends(get_db)):
    vendors = get_vendors(db)
    today = datetime.today().strftime("%a")
    return templates.TemplateResponse(
        "vendors.html",
        {
            "request": request,
            "vendors": vendors,
            "today": today,
        },
    )


@app.post("/vendors")
def add_vendor(
    name: str = Form(...),
    phone: str = Form(...),
    available_days: str = Form(...),
    db: Session = Depends(get_db),
):
    create_vendor(db, name, phone, available_days)
    return RedirectResponse(url="/vendors", status_code=303)


@app.get("/vendors/{vendor_id}/edit", response_class=HTMLResponse)
def edit_vendor_page(request: Request, vendor_id: int, db: Session = Depends(get_db)):
    vendor = get_vendor_by_id(db, vendor_id)

    if not vendor:
        return RedirectResponse(url="/vendors", status_code=303)

    return templates.TemplateResponse(
        "vendor_edit.html",
        {
            "request": request,
            "vendor": vendor,
        },
    )


@app.post("/vendors/{vendor_id}/edit")
def update_vendor(
    vendor_id: int,
    name: str = Form(...),
    phone: str = Form(...),
    available_days: str = Form(...),
    db: Session = Depends(get_db),
):
    vendor = get_vendor_by_id(db, vendor_id)

    if vendor:
        vendor.name = name
        vendor.phone = phone
        vendor.available_days = available_days
        db.commit()

    return RedirectResponse(url="/vendors", status_code=303)


@app.post("/vendors/{vendor_id}/delete")
def delete_vendor(vendor_id: int, db: Session = Depends(get_db)):
    vendor = get_vendor_by_id(db, vendor_id)

    if vendor:
        db.delete(vendor)
        db.commit()

    return RedirectResponse(url="/vendors", status_code=303)


@app.get("/vendors/{vendor_id}/items", response_class=HTMLResponse)
def vendor_items_page(request: Request, vendor_id: int, db: Session = Depends(get_db)):
    vendor = get_vendor_by_id(db, vendor_id)

    if not vendor:
        return RedirectResponse(url="/vendors", status_code=303)

    items = get_items_by_vendor(db, vendor_id)

    return templates.TemplateResponse(
        "vendor_items.html",
        {
            "request": request,
            "vendor": vendor,
            "items": items,
        },
    )


@app.post("/vendors/{vendor_id}/items")
def add_item(
    vendor_id: int,
    name: str = Form(...),
    unit_price: int | None = Form(None),
    db: Session = Depends(get_db),
):
    create_item(db, vendor_id, name, unit_price)
    return RedirectResponse(url=f"/vendors/{vendor_id}/items", status_code=303)


@app.post("/vendors/{vendor_id}/items/{item_id}/edit")
def update_item(
    vendor_id: int,
    item_id: int,
    name: str = Form(...),
    unit_price: int | None = Form(None),
    db: Session = Depends(get_db),
):
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.vendor_id == vendor_id
    ).first()

    if item:
        item.name = name
        item.unit_price = unit_price
        db.commit()

    return RedirectResponse(url=f"/vendors/{vendor_id}/items", status_code=303)


@app.get("/vendors/{vendor_id}/order", response_class=HTMLResponse)
def vendor_order(request: Request, vendor_id: int, db: Session = Depends(get_db)):
    vendor = get_vendor_by_id(db, vendor_id)

    if not vendor:
        return RedirectResponse(url="/vendors", status_code=303)

    items = get_items_by_vendor(db, vendor_id)
    today = datetime.today().strftime("%Y-%m-%d (%a)")

    return templates.TemplateResponse(
        "vendor_order.html",
        {
            "request": request,
            "vendor": vendor,
            "items": items,
            "today": today,
        },
    )


@app.post("/vendors/{vendor_id}/order")
async def confirm_order(
    vendor_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    vendor = get_vendor_by_id(db, vendor_id)

    if not vendor:
        return RedirectResponse(url="/vendors", status_code=303)

    form = await request.form()
    items = get_items_by_vendor(db, vendor_id)

    selected_lines = []

    for item in items:
        qty_raw = form.get(f"qty_{item.id}")

        if qty_raw is None or str(qty_raw).strip() == "":
            continue

        try:
            qty = int(qty_raw)
        except ValueError:
            continue

        if qty > 0:
            selected_lines.append(f"{item.name} x {qty}")

    if not selected_lines:
        return RedirectResponse(url=f"/vendors/{vendor_id}/order", status_code=303)

    message_template = (
        "Hello,\n"
        "This is Tenton Order.\n\n"
        "{items}\n\n"
        "Thank you."
    )

    formatted_items = "\n".join(selected_lines)
    sms_body = message_template.format(items=formatted_items)

    try:
        send_order_sms(vendor.phone, sms_body)
    except Exception as e:
        print("SMS send failed:", e)

    return RedirectResponse(url=f"/vendors/{vendor_id}/order", status_code=303)