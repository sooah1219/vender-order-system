from fastapi import FastAPI, Depends, Request, Form
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from zoneinfo import ZoneInfo

from app.database import SessionLocal, engine, Base
from app.crud import (
    create_vendor,
    get_vendors,
    get_vendor_by_id,
    get_items_by_vendor,
    create_item,
    create_order_history,
    get_order_history,
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


def send_order_sms(phone: str, message: str):
    print("SMS sent to:", phone)
    print(message)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/vendors", response_class=HTMLResponse)
def list_vendors(request: Request, db: Session = Depends(get_db)):

    vendors = get_vendors(db)

    for vendor in vendors:
        items = get_items_by_vendor(db, vendor.id)

        vendor.item_names = [
            item.name for item in items
        ]

    today = datetime.now(
        ZoneInfo("America/Vancouver")
    ).strftime("%a")

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
    unit_price: float | None = Form(None),
    db: Session = Depends(get_db),
):
    create_item(db, vendor_id, name, unit_price)
    return RedirectResponse(url=f"/vendors/{vendor_id}/items", status_code=303)


@app.post("/vendors/{vendor_id}/items/{item_id}/edit")
def update_item(
    vendor_id: int,
    item_id: int,
    name: str = Form(...),
    unit_price: float | None = Form(None),
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
    today = datetime.now(ZoneInfo("America/Vancouver")).strftime("%Y-%m-%d (%a)")

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

    selected_lines: list[str] = []
    total_amount = 0.0

    for item in items:
        qty_raw = form.get(f"qty_{item.id}")

        if qty_raw is None or str(qty_raw).strip() == "":
            continue

        try:
            qty = int(str(qty_raw))
        except ValueError:
            continue

        if qty <= 0:
            continue

        unit_price = item.unit_price or 0
        line_total = qty * unit_price
        total_amount += line_total

        if unit_price > 0:
            selected_lines.append(
                f"{item.name} x {qty} - ${line_total:.2f}"
            )
        else:
            selected_lines.append(
                f"{item.name} x {qty}"
            )

    if not selected_lines:
        return RedirectResponse(url=f"/vendors/{vendor_id}/order", status_code=303)

    formatted_items = "\n".join(selected_lines)

    create_order_history(
        db=db,
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        order_items_text=formatted_items,
        total_amount=total_amount,
    )

    sms_body = (
        f"Hello,\n"
        f"This is Tenton Order.\n\n"
        f"{formatted_items}\n\n"
        f"Total: ${total_amount:.2f}\n\n"
        f"Thank you."
    )

    try:
        send_order_sms(vendor.phone, sms_body)
    except Exception as e:
        print("SMS send failed:", e)

    return RedirectResponse(url="/orders/history", status_code=303)


@app.get("/orders/history", response_class=HTMLResponse)
def order_history_page(
    request: Request,
    vendor_id: str = "",
    order_date: str = "",
    db: Session = Depends(get_db),
):
    vendors = get_vendors(db)

    parsed_vendor_id = None
    if vendor_id.strip():
        try:
            parsed_vendor_id = int(vendor_id)
        except ValueError:
            parsed_vendor_id = None

    parsed_order_date = order_date.strip() or None

    orders = get_order_history(
        db=db,
        vendor_id=parsed_vendor_id,
        order_date=parsed_order_date,
    )

    return templates.TemplateResponse(
        "order_history.html",
        {
            "request": request,
            "orders": orders,
            "vendors": vendors,
            "selected_vendor_id": parsed_vendor_id,
            "selected_order_date": parsed_order_date,
        },
    )