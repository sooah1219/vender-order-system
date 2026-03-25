from datetime import datetime

from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.models import Vendor, Item, OrderHistory
from app.crud import (
    create_vendor,
    get_vendors,
    get_vendor_by_id,
    get_items_by_vendor,
    create_item,
    get_item_by_id,
    delete_item,
    create_order_history,
    get_order_history,
)

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
def root():
    return RedirectResponse(url="/vendors", status_code=303)


@app.get("/vendors", response_class=HTMLResponse)
def vendor_list_page(request: Request, db: Session = Depends(get_db)):
    vendors = get_vendors(db)
    return templates.TemplateResponse(
        "vendors.html",
        {
            "request": request,
            "vendors": vendors,
        },
    )


@app.post("/vendors")
def create_vendor_route(
    name: str = Form(...),
    phone: str = Form(...),
    available_days: str = Form(""),
    db: Session = Depends(get_db),
):
    create_vendor(
        db=db,
        name=name,
        phone=phone,
        available_days=available_days,
    )
    return RedirectResponse(url="/vendors", status_code=303)


@app.get("/vendors/{vendor_id}/items", response_class=HTMLResponse)
def vendor_items_page(
    vendor_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
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
def create_item_route(
    vendor_id: int,
    name: str = Form(...),
    unit_price: str = Form(""),
    db: Session = Depends(get_db),
):
    vendor = get_vendor_by_id(db, vendor_id)

    if not vendor:
        return RedirectResponse(url="/vendors", status_code=303)

    parsed_price: float | None = None

    if unit_price.strip() != "":
        try:
            parsed_price = float(unit_price)
        except ValueError:
            parsed_price = None

    create_item(
        db=db,
        vendor_id=vendor_id,
        name=name,
        unit_price=parsed_price,
    )

    return RedirectResponse(url=f"/vendors/{vendor_id}/items", status_code=303)


@app.post("/items/{item_id}/delete")
def delete_item_route(
    item_id: int,
    db: Session = Depends(get_db),
):
    item = get_item_by_id(db, item_id)

    if not item:
        return RedirectResponse(url="/vendors", status_code=303)

    vendor_id = item.vendor_id
    delete_item(db, item_id)

    return RedirectResponse(url=f"/vendors/{vendor_id}/items", status_code=303)


@app.get("/vendors/{vendor_id}/order", response_class=HTMLResponse)
def vendor_order_page(
    vendor_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    vendor = get_vendor_by_id(db, vendor_id)

    if not vendor:
        return RedirectResponse(url="/vendors", status_code=303)

    items = get_items_by_vendor(db, vendor_id)
    today = datetime.now().strftime("%Y-%m-%d")

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