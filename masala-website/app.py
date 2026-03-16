from collections import Counter
from datetime import date, datetime, timedelta
from functools import wraps
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import sqlite3
from urllib import error as urllib_error
from urllib import request as urllib_request

from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash


load_dotenv(Path(__file__).resolve().parent / ".env")

app = Flask(__name__)
app.secret_key = "samidha-masale-dev-secret"

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "masala.db"

ADMIN_USERNAME = "tanuj123"
ADMIN_PASSWORD = "12345"
ORDER_STATUSES = ["Processing", "Packed", "Shipped", "Delivered", "Cancelled"]
PAYMENT_METHODS = ["COD", "Razorpay"]
DEFAULT_SEED_ORDERS = [
    ("Asha Kulkarni", "Garam Masala x2, Red Chilli Powder x1", 460.0, "Delivered"),
    ("Rohan Patil", "Besan Ladoo x2, Kaju Katli x1", 980.0, "Delivered"),
    ("Sneha Joshi", "Mango Pickle x1, Papad x2", 490.0, "Packed"),
    ("Meera Shah", "Turmeric Powder x2, Masala Chutney x2", 500.0, "Shipped"),
    ("Vikram Desai", "Shakkarpara x1, Garam Masala x1", 380.0, "Processing"),
]

IMAGE_MAP = {
    "spice-one": "https://images.unsplash.com/photo-1615485925873-8e2fdf12f1f1?auto=format&fit=crop&w=900&q=80",
    "spice-two": "https://images.unsplash.com/photo-1509358271058-acd22cc93898?auto=format&fit=crop&w=900&q=80",
    "spice-three": "https://images.unsplash.com/photo-1612257998646-67f075c0db2e?auto=format&fit=crop&w=900&q=80",
    "sweet-one": "https://images.unsplash.com/photo-1605196560547-4d43032d6b20?auto=format&fit=crop&w=900&q=80",
    "sweet-two": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?auto=format&fit=crop&w=900&q=80",
    "sweet-three": "https://images.unsplash.com/photo-1621939514649-280e2ee25f60?auto=format&fit=crop&w=900&q=80",
    "homemade-one": "https://images.unsplash.com/photo-1596797038530-2c107aaedc0c?auto=format&fit=crop&w=900&q=80",
    "homemade-two": "https://images.unsplash.com/photo-1651227819286-d85c1f45f90d?auto=format&fit=crop&w=900&q=80",
    "homemade-three": "https://images.unsplash.com/photo-1512058564366-18510be2db19?auto=format&fit=crop&w=900&q=80",
}

CATEGORY_CONFIG = {
    "Spices": "spices",
    "Diwali Sweets": "sweets",
    "Other Homemade Items": "homemade",
}
RAZORPAY_ORDER_URL = "https://api.razorpay.com/v1/orders"

STOREFRONT_PRODUCTS = {
    "spices": {
        "slug": "spices",
        "title": "Spices",
        "title_mr": "मसाले",
        "tag": "Kitchen Staples",
        "tag_mr": "स्वयंपाकघरातील आवश्यक पदार्थ",
        "description": "Everyday masale inspired by traditional home kitchens and spice bazaars.",
        "description_mr": "पारंपरिक घरगुती चवी आणि मसाला बाजारांच्या प्रेरणेने तयार केलेले रोजच्या वापराचे मसाले.",
        "hero_title": "Freshly Ground Spices",
        "hero_title_mr": "ताजे दळलेले मसाले",
        "hero_text": "Bold aromas, rich color, and authentic flavors for daily Indian cooking.",
        "hero_text_mr": "दररोजच्या भारतीय स्वयंपाकासाठी समृद्ध रंग, सुगंध आणि अस्सल चव.",
        "divider_class": "spice-divider",
        "products": [
            {
                "id": "garam-masala",
                "name": "Garam Masala",
                "name_mr": "गरम मसाला",
                "description": "Bold, aromatic blend for curries, pulao, and home-style sabzis.",
                "description_mr": "करी, पुलाव आणि घरगुती भाज्यांसाठी सुगंधी आणि ठसकेबाज मिश्रण.",
                "ingredients": "Coriander, cumin, black pepper, cloves, cinnamon, cardamom",
                "ingredients_mr": "धणे, जिरे, काळी मिरी, लवंग, दालचिनी, वेलदोडा",
                "price": 160,
                "image_class": "spice-one",
            },
            {
                "id": "red-chilli-powder",
                "name": "Red Chilli Powder",
                "name_mr": "लाल तिखट",
                "description": "Rich color and balanced heat from carefully selected sun-dried chillies.",
                "description_mr": "काळजीपूर्वक निवडलेल्या उन्हात वाळवलेल्या मिरच्यांपासून तयार केलेले रंगदार आणि संतुलित तिखट.",
                "ingredients": "Sun-dried red chillies",
                "ingredients_mr": "उन्हात वाळवलेल्या लाल मिरच्या",
                "price": 140,
                "image_class": "spice-two",
            },
            {
                "id": "turmeric-powder",
                "name": "Turmeric Powder",
                "name_mr": "हळद पावडर",
                "description": "Golden earthy haldi made for daily tadka, curries, and healing drinks.",
                "description_mr": "दररोजच्या फोडणी, करी आणि आरोग्यदायी पेयांसाठी तयार केलेली सुवर्ण हळद.",
                "ingredients": "Single-origin turmeric roots",
                "ingredients_mr": "निवडक हळदीच्या गांठी",
                "price": 120,
                "image_class": "spice-three",
            },
        ],
    },
    "sweets": {
        "slug": "sweets",
        "title": "Diwali Sweets",
        "title_mr": "दिवाळी फराळ आणि मिठाई",
        "tag": "Festive Favorites",
        "tag_mr": "सणासुदीचे आवडते पदार्थ",
        "description": "Celebration-ready homemade mithai with a warm festive touch.",
        "description_mr": "उत्सवी आनंद देणारी घरगुती मिठाई आणि सणासुदीचा खास स्पर्श.",
        "hero_title": "Traditional Festive Mithai",
        "hero_title_mr": "पारंपरिक सणासुदीची मिठाई",
        "hero_text": "Homemade sweets crafted for gifting, puja trays, and joyful family gatherings.",
        "hero_text_mr": "भेटवस्तू, पूजा थाळी आणि कौटुंबिक समारंभांसाठी प्रेमाने तयार केलेली घरगुती मिठाई.",
        "divider_class": "sweet-divider",
        "products": [
            {
                "id": "besan-ladoo",
                "name": "Besan Ladoo",
                "name_mr": "बेसन लाडू",
                "description": "Slow-roasted gram flour laddoos with ghee, cardamom, and festive warmth.",
                "description_mr": "तूप, वेलदोडा आणि सणासुदीची ऊब असलेले मंद आचेवर भाजलेले बेसन लाडू.",
                "ingredients": "Besan, ghee, sugar, cardamom, dry fruits",
                "ingredients_mr": "बेसन, तूप, साखर, वेलदोडा, सुका मेवा",
                "price": 280,
                "image_class": "sweet-one",
            },
            {
                "id": "shakkarpara",
                "name": "Shakkarpara",
                "name_mr": "शंकरपाळे",
                "description": "Crisp festive bites with a nostalgic homemade crunch and light sweetness.",
                "description_mr": "घरगुती कुरकुरीतपणा आणि हलकी गोडी असलेले सणासुदीचे कुरकुरीत तुकडे.",
                "ingredients": "Maida, ghee, sugar syrup, cardamom",
                "ingredients_mr": "मैदा, तूप, साखरेचा पाक, वेलदोडा",
                "price": 220,
                "image_class": "sweet-two",
            },
            {
                "id": "kaju-katli",
                "name": "Kaju Katli",
                "name_mr": "काजू कतली",
                "description": "Soft rich cashew sweets crafted for gifting, puja trays, and family visits.",
                "description_mr": "भेटवस्तू, पूजा थाळी आणि पाहुणचारासाठी तयार केलेली मऊ आणि समृद्ध काजू मिठाई.",
                "ingredients": "Cashews, sugar, cardamom, edible silver leaf",
                "ingredients_mr": "काजू, साखर, वेलदोडा, खाण्यायोग्य वर्ख",
                "price": 420,
                "image_class": "sweet-three",
            },
        ],
    },
    "homemade": {
        "slug": "homemade",
        "title": "Other Homemade Items",
        "title_mr": "इतर घरगुती पदार्थ",
        "tag": "Home Pantry",
        "tag_mr": "घरगुती साठा",
        "description": "Comforting homemade essentials that bring warmth to every meal.",
        "description_mr": "प्रत्येक जेवणात ऊब आणि चव वाढवणारे घरगुती आवश्यक पदार्थ.",
        "hero_title": "Homestyle Pantry Favorites",
        "hero_title_mr": "घरगुती आवडीचे साठवणीचे पदार्थ",
        "hero_text": "Pickles, papad, and accompaniments rooted in small-batch family recipes.",
        "hero_text_mr": "कुटुंबीयांच्या छोट्या बॅचमध्ये तयार होणाऱ्या रेसिपींवर आधारित लोणची, पापड आणि सोबतीचे पदार्थ.",
        "divider_class": "pantry-divider",
        "products": [
            {
                "id": "mango-pickle",
                "name": "Mango Pickle",
                "name_mr": "आंब्याचे लोणचे",
                "description": "Spicy tangy achar prepared in a traditional style with bold masala notes.",
                "description_mr": "पारंपरिक पद्धतीने तयार केलेले मसालेदार आणि आंबट-चटपटीत लोणचे.",
                "ingredients": "Raw mango, mustard oil, fenugreek, chilli, turmeric, salt",
                "ingredients_mr": "कच्चा आंबा, मोहरीचे तेल, मेथी, तिखट, हळद, मीठ",
                "price": 190,
                "image_class": "homemade-one",
            },
            {
                "id": "papad",
                "name": "Papad",
                "name_mr": "पापड",
                "description": "Crisp homemade papad for snacks, festive thalis, and everyday meals.",
                "description_mr": "नाश्ता, सणासुदीची थाळी आणि रोजच्या जेवणासाठी कुरकुरीत घरगुती पापड.",
                "ingredients": "Urad dal flour, black pepper, cumin, salt",
                "ingredients_mr": "उडीद डाळ पीठ, काळी मिरी, जिरे, मीठ",
                "price": 150,
                "image_class": "homemade-two",
            },
            {
                "id": "masala-chutney",
                "name": "Masala Chutney",
                "name_mr": "मसाला चटणी",
                "description": "Flavorful accompaniment that brightens snacks, breakfasts, and simple meals.",
                "description_mr": "नाश्ता, सकाळचे पदार्थ आणि साधे जेवण अधिक चविष्ट करणारी चटपटीत साथ.",
                "ingredients": "Coconut, peanuts, chilli, garlic, spices",
                "ingredients_mr": "खोबरे, शेंगदाणे, मिरची, लसूण, मसाले",
                "price": 130,
                "image_class": "homemade-three",
            },
        ],
    },
}


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT NOT NULL,
            image TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            items TEXT NOT NULL,
            total_price REAL NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL
        )
        """
    )

    order_columns = {row[1] for row in cursor.execute("PRAGMA table_info(orders)").fetchall()}
    required_order_columns = {
        "user_id": "INTEGER",
        "phone": "TEXT",
        "address": "TEXT",
        "payment_method": "TEXT DEFAULT 'COD'",
        "payment_status": "TEXT DEFAULT 'Pending'",
        "razorpay_order_id": "TEXT",
        "razorpay_payment_id": "TEXT",
        "created_at": "TEXT",
    }
    for column_name, column_type in required_order_columns.items():
        if column_name not in order_columns:
            cursor.execute(f"ALTER TABLE orders ADD COLUMN {column_name} {column_type}")

    product_count = cursor.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if product_count == 0:
        seed_products = [
            ("Garam Masala", "Spices", 160, "Bold, aromatic blend for curries, pulao, and home-style sabzis.", IMAGE_MAP["spice-one"]),
            ("Red Chilli Powder", "Spices", 140, "Rich color and balanced heat from carefully selected sun-dried chillies.", IMAGE_MAP["spice-two"]),
            ("Turmeric Powder", "Spices", 120, "Golden earthy haldi made for daily tadka, curries, and healing drinks.", IMAGE_MAP["spice-three"]),
            ("Besan Ladoo", "Diwali Sweets", 280, "Slow-roasted gram flour laddoos with ghee, cardamom, and festive warmth.", IMAGE_MAP["sweet-one"]),
            ("Shakkarpara", "Diwali Sweets", 220, "Crisp festive bites with a nostalgic homemade crunch and light sweetness.", IMAGE_MAP["sweet-two"]),
            ("Kaju Katli", "Diwali Sweets", 420, "Soft rich cashew sweets crafted for gifting, puja trays, and family visits.", IMAGE_MAP["sweet-three"]),
            ("Mango Pickle", "Other Homemade Items", 190, "Spicy tangy achar prepared in a traditional style with bold masala notes.", IMAGE_MAP["homemade-one"]),
            ("Papad", "Other Homemade Items", 150, "Crisp homemade papad for snacks, festive thalis, and everyday meals.", IMAGE_MAP["homemade-two"]),
            ("Masala Chutney", "Other Homemade Items", 130, "Flavorful accompaniment that brightens snacks, breakfasts, and simple meals.", IMAGE_MAP["homemade-three"]),
        ]
        cursor.executemany(
            "INSERT INTO products (name, category, price, description, image) VALUES (?, ?, ?, ?, ?)",
            seed_products,
        )

    # Keep dashboard analytics tied to real orders only.
    existing_orders = cursor.execute(
        "SELECT id, customer_name, items, total_price, status FROM orders"
    ).fetchall()
    seed_order_ids = [
        row[0]
        for row in existing_orders
        if (row[1], row[2], float(row[3]), row[4]) in DEFAULT_SEED_ORDERS
    ]
    if seed_order_ids:
        cursor.executemany("DELETE FROM orders WHERE id = ?", [(order_id,) for order_id in seed_order_ids])

    db.commit()
    db.close()


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    return wrapped_view


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            next_url = request.path
            if request.query_string:
                next_url = f"{next_url}?{request.query_string.decode()}"
            return redirect(url_for("user_login", next=next_url))
        return view(*args, **kwargs)

    return wrapped_view


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_db().execute(
        "SELECT id, name, email, phone FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()


@app.context_processor
def inject_user_context():
    return {
        "current_user": get_current_user(),
        "razorpay_key_id": os.environ.get("RAZORPAY_KEY_ID", ""),
        "razorpay_enabled": bool(os.environ.get("RAZORPAY_KEY_ID") and os.environ.get("RAZORPAY_KEY_SECRET")),
    }


def flatten_storefront_products():
    products = []
    for category_key, category in STOREFRONT_PRODUCTS.items():
        for product in category["products"]:
            products.append(
                {
                    **product,
                    "image": IMAGE_MAP.get(product["image_class"], ""),
                    "category_key": category_key,
                    "category_title": category["title"],
                    "category_title_mr": category["title_mr"],
                    "category_tag": category["tag"],
                    "category_tag_mr": category["tag_mr"],
                }
            )
    return products


def render_storefront(template_name, **context):
    return render_template(template_name, all_products=flatten_storefront_products(), **context)


def get_storefront_products(category_name=None):
    query = "SELECT * FROM products"
    params = ()
    if category_name:
        query += " WHERE category = ?"
        params = (category_name,)
    query += " ORDER BY id DESC"

    rows = get_db().execute(query, params).fetchall()
    products = []
    for row in rows:
        category_key = CATEGORY_CONFIG.get(row["category"])
        category = STOREFRONT_PRODUCTS.get(category_key, {})
        products.append(
            {
                "id": str(row["id"]),
                "name": row["name"],
                "name_mr": row["name"],
                "description": row["description"],
                "description_mr": row["description"],
                "ingredients": row["description"],
                "ingredients_mr": row["description"],
                "price": float(row["price"]),
                "image": row["image"],
                "image_class": "",
                "category_key": category_key,
                "category_title": row["category"],
                "category_title_mr": category.get("title_mr", row["category"]),
                "category_tag": category.get("tag", row["category"]),
                "category_tag_mr": category.get("tag_mr", row["category"]),
            }
        )
    return products


def get_admin_products():
    rows = get_db().execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    return rows


def get_admin_orders():
    return get_db().execute("SELECT * FROM orders ORDER BY date DESC, id DESC").fetchall()


def parse_cart_items(raw_cart):
    if isinstance(raw_cart, str):
        try:
            cart_items = json.loads(raw_cart)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid cart payload.") from exc
    else:
        cart_items = raw_cart

    if not isinstance(cart_items, list) or not cart_items:
        raise ValueError("Your cart is empty.")

    normalized_items = []
    total_price = 0.0
    item_summary = []

    for item in cart_items:
        try:
            product_id = int(item.get("id"))
            quantity = max(1, int(item.get("quantity", 1)))
        except (TypeError, ValueError, AttributeError) as exc:
            raise ValueError("Invalid cart item.") from exc

        product = get_db().execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if not product:
            raise ValueError("One of the selected products no longer exists.")

        line_total = float(product["price"]) * quantity
        total_price += line_total
        item_summary.append(f"{product['name']} x{quantity}")
        normalized_items.append(
            {
                "id": product["id"],
                "name": product["name"],
                "category": product["category"],
                "price": float(product["price"]),
                "quantity": quantity,
                "line_total": line_total,
            }
        )

    return normalized_items, ", ".join(item_summary), round(total_price, 2)


def create_razorpay_order(amount, receipt):
    key_id = os.environ.get("RAZORPAY_KEY_ID", "").strip()
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "").strip()
    if not key_id or not key_secret:
        raise ValueError("Razorpay keys are not configured.")

    payload = json.dumps(
        {"amount": int(round(amount * 100)), "currency": "INR", "receipt": receipt}
    ).encode("utf-8")
    credentials = base64.b64encode(f"{key_id}:{key_secret}".encode("utf-8")).decode("utf-8")
    req = urllib_request.Request(
        RAZORPAY_ORDER_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib_request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib_error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise ValueError(f"Razorpay order creation failed: {detail or exc.reason}") from exc
    except urllib_error.URLError as exc:
        raise ValueError("Unable to reach Razorpay. Please try again.") from exc


def verify_razorpay_signature(order_id, payment_id, signature):
    secret = os.environ.get("RAZORPAY_KEY_SECRET", "").strip()
    if not secret:
        return False
    generated = hmac.new(
        secret.encode("utf-8"),
        f"{order_id}|{payment_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(generated, signature)


def create_customer_order(user_id, customer_name, phone, address, cart_payload, payment_method, payment_state):
    cart_items, items_text, total_price = parse_cart_items(cart_payload)
    db = get_db()
    db.execute(
        """
        INSERT INTO orders (
            user_id, customer_name, phone, address, items, total_price, date, status,
            payment_method, payment_status, razorpay_order_id, razorpay_payment_id, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            customer_name,
            phone,
            address,
            items_text,
            total_price,
            date.today().isoformat(),
            "Processing",
            payment_method,
            payment_state.get("payment_status", "Pending"),
            payment_state.get("razorpay_order_id"),
            payment_state.get("razorpay_payment_id"),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    db.commit()
    order_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    return {"order_id": order_id, "items": cart_items, "total_price": total_price}


def serialize_order(order):
    return {
        "id": order["id"],
        "customer_name": order["customer_name"],
        "items": order["items"],
        "total_price": float(order["total_price"]),
        "date": order["date"],
        "status": order["status"],
        "payment_method": order["payment_method"] if "payment_method" in order.keys() else "",
        "payment_status": order["payment_status"] if "payment_status" in order.keys() else "",
    }


def get_dashboard_metrics():
    db = get_db()
    total_orders = db.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    total_revenue = db.execute("SELECT COALESCE(SUM(total_price), 0) FROM orders").fetchone()[0]
    total_products = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    processing_orders = db.execute(
        "SELECT COUNT(*) FROM orders WHERE status IN ('Processing', 'Packed', 'Shipped')"
    ).fetchone()[0]
    todays_sales = db.execute(
        "SELECT COALESCE(SUM(total_price), 0) FROM orders WHERE date = ?",
        (date.today().isoformat(),),
    ).fetchone()[0]

    labels = []
    sales_values = []
    for day_offset in range(6, -1, -1):
        current_day = date.today() - timedelta(days=day_offset)
        labels.append(current_day.strftime("%d %b"))
        sales = db.execute(
            "SELECT COALESCE(SUM(total_price), 0) FROM orders WHERE date = ?",
            (current_day.isoformat(),),
        ).fetchone()[0]
        sales_values.append(float(sales))

    order_rows = db.execute("SELECT items FROM orders").fetchall()
    counter = Counter()
    for row in order_rows:
        for item_text in row["items"].split(","):
            cleaned = item_text.strip()
            if " x" in cleaned:
                name, qty = cleaned.rsplit(" x", 1)
                try:
                    counter[name] += int(qty)
                except ValueError:
                    counter[name] += 1
            elif cleaned:
                counter[cleaned] += 1

    top_items = counter.most_common(5)
    top_labels = [item[0] for item in top_items]
    top_values = [item[1] for item in top_items]
    has_order_data = total_orders > 0

    return {
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
        "total_products": total_products,
        "processing_orders": processing_orders,
        "todays_sales": float(todays_sales),
        "sales_labels": labels,
        "sales_values": sales_values,
        "top_labels": top_labels,
        "top_values": top_values,
        "has_order_data": has_order_data,
    }


@app.route("/")
def home():
    return render_storefront("index.html", current_page="home")


@app.route("/products")
def products():
    return render_template(
        "products.html",
        current_page="products",
        all_products=get_storefront_products(),
    )


@app.route("/cart")
def cart():
    return render_storefront(
        "cart.html",
        current_page="cart",
        razorpay_enabled=bool(
            os.environ.get("RAZORPAY_KEY_ID", "").strip()
            and os.environ.get("RAZORPAY_KEY_SECRET", "").strip()
        ),
    )


@app.route("/register", methods=["GET", "POST"])
def user_register():
    if session.get("user_id"):
        return redirect(url_for("cart"))

    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "").strip()

        if not all([name, email, phone, password]):
            error = "Please fill in all registration fields."
        else:
            db = get_db()
            existing_user = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if existing_user:
                error = "An account with this email already exists."
            else:
                db.execute(
                    """
                    INSERT INTO users (name, email, phone, password_hash, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (name, email, phone, generate_password_hash(password), datetime.now().isoformat(timespec="seconds")),
                )
                db.commit()
                user = db.execute("SELECT id, name FROM users WHERE email = ?", (email,)).fetchone()
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                flash("Your account has been created.", "success")
                return redirect(request.args.get("next") or url_for("cart"))

    return render_template("user_auth.html", auth_mode="register", error=error, current_page="auth")


@app.route("/login", methods=["GET", "POST"])
def user_login():
    if session.get("user_id"):
        return redirect(request.args.get("next") or url_for("cart"))

    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            error = "Invalid email or password."
        else:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash("You are now logged in.", "success")
            return redirect(request.args.get("next") or url_for("cart"))

    return render_template("user_auth.html", auth_mode="login", error=error, current_page="auth")


@app.route("/logout")
def user_logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@app.route("/spices")
def spices():
    return render_template(
        "category.html",
        current_page="spices",
        category=STOREFRONT_PRODUCTS["spices"],
        category_products=get_storefront_products("Spices"),
        all_products=get_storefront_products(),
    )


@app.route("/diwali-sweets")
def diwali_sweets():
    return render_template(
        "category.html",
        current_page="sweets",
        category=STOREFRONT_PRODUCTS["sweets"],
        category_products=get_storefront_products("Diwali Sweets"),
        all_products=get_storefront_products(),
    )


@app.route("/homemade-items")
def homemade_items():
    return render_template(
        "category.html",
        current_page="homemade",
        category=STOREFRONT_PRODUCTS["homemade"],
        category_products=get_storefront_products("Other Homemade Items"),
        all_products=get_storefront_products(),
    )


@app.route("/admin")
def admin_index():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("admin_login"))


@app.route("/admin/login", methods=["GET", "POST"])
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            session["admin_username"] = username
            return redirect(url_for("admin_dashboard"))
        error = "Invalid username or password."

    return render_template("admin_login.html", error=error)


@app.route("/api/checkout/razorpay-order", methods=["POST"])
@login_required
def checkout_razorpay_order():
    user = get_current_user()
    payload = request.get_json(silent=True) or {}
    customer_name = payload.get("customer_name", "").strip() or user["name"]
    phone = payload.get("phone", "").strip() or user["phone"]
    address = payload.get("address", "").strip()
    cart = payload.get("cart")

    if not address:
        return jsonify({"ok": False, "message": "Delivery address is required."}), 400

    try:
        _, _, total_price = parse_cart_items(cart)
        razorpay_order = create_razorpay_order(total_price, f"samidha-{int(datetime.now().timestamp())}")
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400

    return jsonify(
        {
            "ok": True,
            "key_id": os.environ.get("RAZORPAY_KEY_ID", ""),
            "razorpay_order": razorpay_order,
            "customer": {"name": customer_name, "email": user["email"], "phone": phone},
            "address": address,
            "amount": total_price,
        }
    )


@app.route("/api/place-order", methods=["POST"])
@login_required
def place_order():
    user = get_current_user()
    payload = request.get_json(silent=True) or {}
    customer_name = payload.get("customer_name", "").strip() or user["name"]
    phone = payload.get("phone", "").strip() or user["phone"]
    address = payload.get("address", "").strip()
    payment_method = payload.get("payment_method", "").strip()
    cart = payload.get("cart")

    if not all([customer_name, phone, address, payment_method]):
        return jsonify({"ok": False, "message": "Please complete all checkout details."}), 400

    if payment_method not in PAYMENT_METHODS:
        return jsonify({"ok": False, "message": "Please choose a valid payment method."}), 400

    payment_state = {"payment_status": "Pending"}
    if payment_method == "COD":
        payment_state["payment_status"] = "Pending"
    else:
        razorpay_order_id = payload.get("razorpay_order_id", "").strip()
        razorpay_payment_id = payload.get("razorpay_payment_id", "").strip()
        razorpay_signature = payload.get("razorpay_signature", "").strip()
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return jsonify({"ok": False, "message": "Razorpay payment verification data is missing."}), 400
        if not verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
            return jsonify({"ok": False, "message": "Razorpay payment verification failed."}), 400
        payment_state = {
            "payment_status": "Paid",
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
        }

    try:
        order = create_customer_order(user["id"], customer_name, phone, address, cart, payment_method, payment_state)
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400

    return jsonify(
        {
            "ok": True,
            "message": "Order placed successfully.",
            "order_id": order["order_id"],
            "total_price": order["total_price"],
        }
    )


@app.route("/admin/logout")
@app.route("/admin-logout")
@admin_required
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin/dashboard")
@app.route("/admin-dashboard")
@admin_required
def admin_dashboard():
    metrics = get_dashboard_metrics()
    recent_orders = get_admin_orders()[:5]
    return render_template(
        "admin_dashboard.html",
        active_admin_page="dashboard",
        metrics=metrics,
        recent_orders=recent_orders,
        recent_orders_data=[serialize_order(order) for order in recent_orders],
        admin_username=session.get("admin_username", ADMIN_USERNAME),
    )


@app.route("/admin/dashboard-data")
@admin_required
def admin_dashboard_data():
    metrics = get_dashboard_metrics()
    recent_orders = [serialize_order(order) for order in get_admin_orders()[:5]]
    return jsonify({"metrics": metrics, "recent_orders": recent_orders})


@app.route("/admin/products", methods=["GET", "POST"])
@app.route("/admin-products", methods=["GET", "POST"])
@admin_required
def admin_products():
    db = get_db()
    if request.method == "POST":
        product_id = request.form.get("product_id", "").strip()
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        price = request.form.get("price", "").strip()
        description = request.form.get("description", "").strip()
        image = request.form.get("image", "").strip()

        if not all([name, category, price, description, image]):
            flash("Please fill in all product fields.", "error")
            return redirect(url_for("admin_products"))

        try:
            price_value = float(price)
        except ValueError:
            flash("Please enter a valid product price.", "error")
            return redirect(url_for("admin_products"))

        if product_id:
            db.execute(
                """
                UPDATE products
                SET name = ?, category = ?, price = ?, description = ?, image = ?
                WHERE id = ?
                """,
                (name, category, price_value, description, image, int(product_id)),
            )
            flash("Product updated successfully.", "success")
        else:
            db.execute(
                "INSERT INTO products (name, category, price, description, image) VALUES (?, ?, ?, ?, ?)",
                (name, category, price_value, description, image),
            )
            flash("Product added successfully.", "success")
        db.commit()
        return redirect(url_for("admin_products"))

    edit_id = request.args.get("edit", type=int)
    edit_product = None
    if edit_id:
        edit_product = db.execute("SELECT * FROM products WHERE id = ?", (edit_id,)).fetchone()

    return render_template(
        "admin_products.html",
        active_admin_page="products",
        products=get_admin_products(),
        edit_product=edit_product,
    )


@app.route("/admin/products/<int:product_id>/delete", methods=["POST"])
@app.route("/admin-products/<int:product_id>/delete", methods=["POST"])
@admin_required
def delete_admin_product(product_id):
    db = get_db()
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    flash("Product deleted successfully.", "success")
    return redirect(url_for("admin_products"))


@app.route("/admin/orders", methods=["GET", "POST"])
@app.route("/admin-orders", methods=["GET", "POST"])
@admin_required
def admin_orders():
    db = get_db()
    if request.method == "POST":
        order_id = request.form.get("order_id", "").strip()
        customer_name = request.form.get("customer_name", "").strip()
        items = request.form.get("items", "").strip()
        total_price = request.form.get("total_price", "").strip()
        order_date = request.form.get("date", "").strip() or date.today().isoformat()
        status = request.form.get("status", "").strip()

        if not all([customer_name, items, total_price, order_date, status]):
            flash("Please fill in all order fields.", "error")
            return redirect(url_for("admin_orders"))

        if status not in ORDER_STATUSES:
            flash("Please choose a valid order status.", "error")
            return redirect(url_for("admin_orders"))

        try:
            total_price_value = float(total_price)
            datetime.strptime(order_date, "%Y-%m-%d")
        except ValueError:
            flash("Please enter a valid total amount and order date.", "error")
            return redirect(url_for("admin_orders"))

        if order_id:
            db.execute(
                """
                UPDATE orders
                SET customer_name = ?, items = ?, total_price = ?, date = ?, status = ?
                WHERE id = ?
                """,
                (customer_name, items, total_price_value, order_date, status, int(order_id)),
            )
            flash("Order updated successfully.", "success")
        else:
            db.execute(
                """
                INSERT INTO orders (customer_name, items, total_price, date, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (customer_name, items, total_price_value, order_date, status),
            )
            flash("Order added successfully.", "success")
        db.commit()
        return redirect(url_for("admin_orders"))

    edit_id = request.args.get("edit", type=int)
    edit_order = None
    if edit_id:
        edit_order = db.execute("SELECT * FROM orders WHERE id = ?", (edit_id,)).fetchone()

    return render_template(
        "admin_orders.html",
        active_admin_page="orders",
        orders=get_admin_orders(),
        edit_order=edit_order,
        order_statuses=ORDER_STATUSES,
    )


@app.route("/admin/orders/<int:order_id>/delete", methods=["POST"])
@app.route("/admin-orders/<int:order_id>/delete", methods=["POST"])
@admin_required
def delete_admin_order(order_id):
    db = get_db()
    db.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    db.commit()
    flash("Order deleted successfully.", "success")
    return redirect(url_for("admin_orders"))


init_db()


if __name__ == "__main__":
    app.run(debug=True)
