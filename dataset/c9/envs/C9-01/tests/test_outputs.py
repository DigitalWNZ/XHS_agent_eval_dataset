"""Hidden tests for C9-01 (潮玩零售店工作台). Run with pytest + Playwright (Chromium) against /app/index.html.

The page must expose window.shopTestAPI (contract in the task prompt). Money values are yuan (2 decimals).
Each test starts from a fresh browser context and calls shopTestAPI.reset().
"""
import json
import math
import os
import re
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

APP = Path(os.environ.get("C9_APP", "/app/index.html"))
CENT = 0.011  # money tolerance (rounding to cents)
ADDR = {"name": "测试员", "phone": "13912345678", "address": "上海市浦东新区世纪大道 100 号"}
STATUSES = {"pending", "paid", "shipped", "cancelled"}


# ---------- fixtures ----------
@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        kw = {"args": ["--no-sandbox", "--disable-dev-shm-usage"]}
        if os.environ.get("C9_CHROME"):
            kw["executable_path"] = os.environ["C9_CHROME"]
        b = p.chromium.launch(**kw)
        yield b
        b.close()


class Page:
    """A loaded app page with network blocked and console errors recorded."""

    def __init__(self, browser):
        self.ctx = browser.new_context()
        self.page = self.ctx.new_page()
        self.external, self.errors = [], []
        self.page.on("pageerror", lambda e: self.errors.append(str(e)))
        self.page.on("console", lambda m: self.errors.append(m.text) if m.type == "error" else None)
        self.page.on("dialog", lambda d: d.accept())

        def route(r):
            if r.request.url.startswith(("file:", "data:", "blob:", "about:")):
                return r.continue_()
            self.external.append(r.request.url)
            return r.abort()

        self.ctx.route("**/*", route)
        self.load()

    def load(self):
        self.page.goto(APP.as_uri())
        self.page.wait_for_function("() => typeof window.shopTestAPI === 'object' && window.shopTestAPI !== null", timeout=15000)

    def api(self, method, *args):
        return self.page.evaluate("([m, a]) => window.shopTestAPI[m](...a)", [method, list(args)])

    def state(self):
        return self.api("getState")


@pytest.fixture
def app(browser):
    assert APP.exists(), f"{APP} not found"
    pg = Page(browser)
    assert pg.api("reset").get("ok") is True
    yield pg
    pg.ctx.close()


def stock(st, sku):
    for p in st["products"]:
        for v in p["variants"]:
            if v["sku"] == sku:
                return v["stock"]
    raise AssertionError(f"sku {sku} not found")


def variants(st):
    return [(p, v) for p in st["products"] for v in p["variants"]]


def in_stock(st, min_stock=1, max_price=None):
    out = [v for _, v in variants(st) if v["stock"] >= min_stock and (max_price is None or v["price"] <= max_price)]
    assert out, "no variant with enough stock"
    return out


def order(st, oid):
    return next(o for o in st["orders"] if o["id"] == oid)


def place_order(app, lines, member=False, coupon=None):
    """lines: [(sku, qty)] -> order id (pending)."""
    app.api("setMember", member)
    for sku, q in lines:
        r = app.api("addToCart", sku, q)
        assert r["ok"], r
    if coupon:
        assert app.api("applyCoupon", coupon)["ok"]
    r = app.api("checkout", ADDR)
    assert r["ok"] and r.get("orderId"), r
    return r["orderId"]


def coupon_order(app):
    """A pending order with a coupon applied (so refunds must be pro-rated). Returns (order id, lines)."""
    st = app.state()
    c = min(st["coupons"], key=lambda c: c["threshold"])
    vs = sorted(in_stock(st, 3), key=lambda v: -v["price"])
    lines, total = [], 0
    for v in vs:
        if total >= c["threshold"] and len(lines) >= 2:
            break
        q = min(3, v["stock"])
        lines.append((v["sku"], q))
        total += q * v["price"]
    assert total >= c["threshold"], "seed stock too small to reach a coupon threshold"
    return place_order(app, lines, coupon=c["code"]), lines


# ---------- 1. delivery ----------
def test_single_self_contained_file(app):
    html = APP.read_text(encoding="utf-8", errors="replace")
    assert not re.search(r"<(script|link|img|iframe)[^>]+(src|href)\s*=\s*['\"]?(https?:)?//", html, re.I), "external resource reference"
    assert not re.search(r"@import\s+url\(\s*['\"]?https?:", html, re.I)
    app.page.wait_for_timeout(500)
    assert app.external == [], f"page requested network resources: {app.external[:5]}"
    assert app.errors == [], f"console/page errors: {app.errors[:5]}"


def test_workbench_ui_present(app):
    text = app.page.inner_text("body")
    for word in ("购物车", "订单", "售后"):
        assert word in text, f"UI text '{word}' not visible"


# ---------- 2. seed data ----------
def test_seed_products_and_orders(app):
    st = app.state()
    vs = variants(st)
    assert len(st["products"]) >= 5
    assert sum(len(p["variants"]) >= 2 for p in st["products"]) >= 2, "need products with several variants"
    assert len({v["price"] for _, v in vs}) >= 4, "need varied prices"
    assert any(v["stock"] == 0 for _, v in vs), "need an out-of-stock variant"
    assert any(v["stock"] > 0 for _, v in vs)
    statuses = {o["status"] for o in st["orders"]}
    assert STATUSES <= statuses, f"history must cover all statuses, got {statuses}"
    assert any(0 < o["refundedAmount"] < o["payable"] for o in st["orders"]), "history needs a partially refunded order"
    assert all(bool(o.get("paidAt")) == (o["status"] in ("paid", "shipped") or o["refundedAmount"] > 0)
               for o in st["orders"] if o["status"] != "cancelled"), "paidAt must be set exactly for paid orders"
    assert st["coupons"] and all(c["threshold"] > 0 and c["amount"] > 0 for c in st["coupons"])


# ---------- 3. cart ----------
def test_cart_add_update_remove_and_totals(app):
    st = app.state()
    a, b = in_stock(st, 3)[:2]
    assert app.api("addToCart", a["sku"], 2)["ok"]
    assert app.api("addToCart", b["sku"], 1)["ok"]
    cart = app.api("getCart")
    assert math.isclose(cart["subtotal"], 2 * a["price"] + b["price"], abs_tol=CENT)
    assert app.api("setCartQty", a["sku"], 3)["ok"]
    assert math.isclose(app.api("getCart")["subtotal"], 3 * a["price"] + b["price"], abs_tol=CENT)
    app.api("removeFromCart", b["sku"])
    cart = app.api("getCart")
    assert [l["sku"] for l in cart["lines"]] == [a["sku"]]
    assert math.isclose(cart["subtotal"], 3 * a["price"], abs_tol=CENT)


@pytest.mark.parametrize("bad", [0, -1, 1.5, "abc"])
def test_cart_rejects_illegal_quantity(app, bad):
    v = in_stock(app.state(), 2)[0]
    r = app.api("addToCart", v["sku"], bad)
    assert r["ok"] is False
    assert app.api("getCart")["lines"] == []
    assert app.api("addToCart", v["sku"], 1)["ok"]
    assert app.api("setCartQty", v["sku"], bad)["ok"] is False
    assert app.api("getCart")["lines"][0]["qty"] == 1


def test_cart_rejects_out_of_stock_and_over_stock(app):
    st = app.state()
    zero = next(v for _, v in variants(st) if v["stock"] == 0)
    assert app.api("addToCart", zero["sku"], 1)["ok"] is False
    v = in_stock(st, 1)[0]
    assert app.api("addToCart", v["sku"], v["stock"] + 1)["ok"] is False
    assert app.api("addToCart", v["sku"], v["stock"])["ok"]
    assert app.api("addToCart", v["sku"], 1)["ok"] is False, "cart total may not exceed stock"
    assert app.api("setCartQty", v["sku"], v["stock"] + 1)["ok"] is False
    assert app.api("getCart")["lines"][0]["qty"] == v["stock"]


# ---------- 4. discounts ----------
def _fill_to(app, target):
    """Add items until subtotal >= target; returns the list of (sku, qty) added."""
    added = []
    for v in sorted(in_stock(app.state(), 1), key=lambda v: -v["price"]):
        while app.api("getCart")["subtotal"] < target:
            if not app.api("addToCart", v["sku"], 1)["ok"]:
                break
            added.append((v["sku"], 1))
        if app.api("getCart")["subtotal"] >= target:
            break
    assert app.api("getCart")["subtotal"] >= target
    return added


def test_coupon_threshold_and_invalidation(app):
    st = app.state()
    c = min(st["coupons"], key=lambda c: c["threshold"])
    cheap = min(in_stock(st, 1), key=lambda v: v["price"])
    if cheap["price"] < c["threshold"]:
        assert app.api("addToCart", cheap["sku"], 1)["ok"]
        assert app.api("applyCoupon", c["code"])["ok"] is False, "coupon below threshold must be rejected"
        app.api("removeFromCart", cheap["sku"])
    added = _fill_to(app, c["threshold"])
    assert app.api("applyCoupon", c["code"])["ok"]
    cart = app.api("getCart")
    cd = sum(d["amount"] for d in cart["discounts"] if d["type"] == "coupon")
    assert math.isclose(cd, c["amount"], abs_tol=CENT)
    assert math.isclose(cart["total"], cart["subtotal"] - sum(d["amount"] for d in cart["discounts"]), abs_tol=CENT)
    # drop below the threshold: the coupon discount must disappear
    cart = app.api("getCart")
    while cart["subtotal"] >= c["threshold"]:
        app.api("removeFromCart", cart["lines"][0]["sku"])
        cart = app.api("getCart")  # first read after the change must already be correct
    assert sum(d["amount"] for d in cart["discounts"] if d["type"] == "coupon") == 0, "stale coupon discount kept"
    assert math.isclose(cart["total"], cart["subtotal"], abs_tol=CENT)


def test_member_discount_recalculates(app):
    v = max(in_stock(app.state(), 2), key=lambda v: v["price"])
    assert app.api("addToCart", v["sku"], 2)["ok"]
    app.api("setMember", False)
    c0 = app.api("getCart")
    assert not [d for d in c0["discounts"] if d["type"] == "member"]
    assert math.isclose(c0["total"], c0["subtotal"], abs_tol=CENT)
    app.api("setMember", True)
    c1 = app.api("getCart")
    md = sum(d["amount"] for d in c1["discounts"] if d["type"] == "member")
    assert 0 < md < c1["subtotal"]
    assert math.isclose(c1["total"], c1["subtotal"] - sum(d["amount"] for d in c1["discounts"]), abs_tol=CENT)
    app.api("setCartQty", v["sku"], 1)
    c2 = app.api("getCart")
    md2 = sum(d["amount"] for d in c2["discounts"] if d["type"] == "member")
    assert md2 < md and math.isclose(c2["total"], c2["subtotal"] - sum(d["amount"] for d in c2["discounts"]), abs_tol=CENT)
    app.api("setMember", False)
    c3 = app.api("getCart")
    assert not [d for d in c3["discounts"] if d["type"] == "member"] and math.isclose(c3["total"], c3["subtotal"], abs_tol=CENT)


# ---------- 5. checkout ----------
@pytest.mark.parametrize("bad", [
    {"name": "", "phone": "13912345678", "address": "上海市浦东新区世纪大道 100 号"},
    {"name": "测试员", "phone": "12345", "address": "上海市浦东新区世纪大道 100 号"},
    {"name": "测试员", "phone": "13912345678", "address": ""},
])
def test_checkout_validates_address(app, bad):
    v = in_stock(app.state(), 1)[0]
    n = len(app.state()["orders"])
    app.api("addToCart", v["sku"], 1)
    assert app.api("checkout", bad)["ok"] is False
    st = app.state()
    assert len(st["orders"]) == n and stock(st, v["sku"]) == v["stock"]


def test_checkout_creates_order_and_reserves_stock(app):
    st = app.state()
    v = in_stock(st, 3)[0]
    n = len(st["orders"])
    oid = place_order(app, [(v["sku"], 2)])
    st = app.state()
    assert len(st["orders"]) == n + 1
    o = order(st, oid)
    assert o["status"] == "pending"
    assert stock(st, v["sku"]) == v["stock"] - 2
    assert [o["id"] for o in app.api("queryOrders", {"orderId": oid})] == [oid]
    assert app.api("getCart")["lines"] == [], "cart should be emptied after checkout"


def test_double_click_confirm_creates_one_order(app):
    st = app.state()
    v = in_stock(st, 2)[0]
    n = len(st["orders"])
    assert app.api("addToCart", v["sku"], 1)["ok"]
    assert app.api("prepareCheckout", ADDR)["ok"]
    btn = app.page.locator('[data-testid="confirm-order"]')
    btn.wait_for(state="visible", timeout=5000)
    app.page.evaluate("""() => { const b = document.querySelector('[data-testid="confirm-order"]');
        b.click(); b.click(); b.click(); }""")
    app.page.wait_for_timeout(800)
    st = app.state()
    assert len(st["orders"]) == n + 1, f"expected exactly one new order, got {len(st['orders']) - n}"
    assert stock(st, v["sku"]) == v["stock"] - 1, "stock deducted more than once"


# ---------- 6. status flow ----------
def test_status_transitions(app):
    st = app.state()
    v = in_stock(st, 2)[0]
    oid = place_order(app, [(v["sku"], 1)])
    assert app.api("ship", oid)["ok"] is False, "pending order cannot ship"
    assert app.api("pay", oid)["ok"]
    assert app.api("pay", oid)["ok"] is False, "cannot pay twice"
    assert app.api("ship", oid)["ok"]
    assert order(app.state(), oid)["status"] == "shipped"
    assert app.api("cancel", oid)["ok"] is False, "shipped order cannot be cancelled"
    assert order(app.state(), oid)["status"] == "shipped"


def test_cancel_pending_releases_stock_once(app):
    v = in_stock(app.state(), 3)[0]
    oid = place_order(app, [(v["sku"], 2)])
    assert stock(app.state(), v["sku"]) == v["stock"] - 2
    assert app.api("cancel", oid)["ok"]
    st = app.state()
    assert order(st, oid)["status"] == "cancelled" and stock(st, v["sku"]) == v["stock"]
    assert app.api("cancel", oid)["ok"] is False
    assert app.api("pay", oid)["ok"] is False, "cancelled order cannot be paid"
    assert stock(app.state(), v["sku"]) == v["stock"], "repeated cancel released stock again"


def test_cancel_paid_unshipped_releases_stock(app):
    v = in_stock(app.state(), 3)[0]
    oid = place_order(app, [(v["sku"], 2)])
    assert app.api("pay", oid)["ok"]
    assert app.api("cancel", oid)["ok"]
    st = app.state()
    assert stock(st, v["sku"]) == v["stock"] and order(st, oid)["status"] == "cancelled"
    assert app.api("cancel", oid)["ok"] is False and stock(app.state(), v["sku"]) == v["stock"]


# ---------- 7. partial refunds ----------
def _expected_refund(o, items):
    total = sum(i["unitPrice"] * i["qty"] for i in o["items"])
    return sum(next(i["unitPrice"] for i in o["items"] if i["sku"] == it["sku"]) * it["qty"] for it in items) * o["payable"] / total


def test_partial_refund_prorated_and_capped(app):
    oid, lines = coupon_order(app)
    assert app.api("pay", oid)["ok"] and app.api("ship", oid)["ok"]
    o = order(app.state(), oid)
    assert o["payable"] < o["subtotal"], "coupon order should have a discount"
    sku, q = lines[0]
    r1 = app.api("requestAfterSale", oid, [{"sku": sku, "qty": 1}], {"returnGoods": True})
    assert r1["ok"], r1
    exp = _expected_refund(o, [{"sku": sku, "qty": 1}])
    unit = next(i["unitPrice"] for i in o["items"] if i["sku"] == sku)
    assert math.isclose(r1["amount"], exp, abs_tol=0.02), f"refund {r1['amount']} vs pro-rated {exp:.2f}"
    assert r1["amount"] < unit, "refund must not use the original price when a discount applied"
    # more than refundable
    assert app.api("requestAfterSale", oid, [{"sku": sku, "qty": q}], {"returnGoods": True})["ok"] is False
    assert app.api("requestAfterSale", oid, [{"sku": sku, "qty": 0}], {"returnGoods": True})["ok"] is False
    # refund everything that is left: total refunded == paid amount, never more
    rest = [{"sku": s, "qty": n - (1 if s == sku else 0)} for s, n in lines if n - (1 if s == sku else 0) > 0]
    r2 = app.api("requestAfterSale", oid, rest, {"returnGoods": True})
    assert r2["ok"], r2
    o = order(app.state(), oid)
    assert o["refundedAmount"] <= o["payable"] + 1e-9
    assert math.isclose(o["refundedAmount"], o["payable"], abs_tol=CENT)
    assert app.api("requestAfterSale", oid, [{"sku": sku, "qty": 1}], {"returnGoods": True})["ok"] is False


def test_refund_not_allowed_for_pending_or_cancelled(app):
    v = in_stock(app.state(), 2)[0]
    oid = place_order(app, [(v["sku"], 1)])
    assert app.api("requestAfterSale", oid, [{"sku": v["sku"], "qty": 1}], {"returnGoods": False})["ok"] is False
    app.api("cancel", oid)
    assert app.api("requestAfterSale", oid, [{"sku": v["sku"], "qty": 1}], {"returnGoods": False})["ok"] is False


# ---------- 8. stock <-> after-sale ----------
def test_return_restocks_only_after_confirmation_once(app):
    v = in_stock(app.state(), 3)[0]
    oid = place_order(app, [(v["sku"], 2)])
    app.api("pay", oid)
    app.api("ship", oid)
    s0 = stock(app.state(), v["sku"])
    n_logs = len(app.state()["logs"])
    r = app.api("requestAfterSale", oid, [{"sku": v["sku"], "qty": 1}], {"returnGoods": True})
    assert r["ok"] and r.get("refundId")
    assert stock(app.state(), v["sku"]) == s0, "refund request alone must not restock shipped goods"
    assert app.api("confirmReturn", r["refundId"])["ok"]
    assert stock(app.state(), v["sku"]) == s0 + 1
    assert app.api("confirmReturn", r["refundId"])["ok"] is False
    st = app.state()
    assert stock(st, v["sku"]) == s0 + 1, "restocked twice"
    assert len(st["logs"]) >= n_logs + 2, "operations should be logged"


# ---------- 9. query & stats ----------
def _stats_from_records(st):
    sales = refunds = 0.0
    units = {}
    for o in st["orders"]:
        if not o.get("paidAt"):
            continue
        sales += o["payable"]
        refunds += o["refundedAmount"]
        for i in o["items"]:
            units[i["sku"]] = units.get(i["sku"], 0) + i["qty"]
        for r in o["refunds"]:
            for i in r["items"]:
                units[i["sku"]] = units.get(i["sku"], 0) - i["qty"]
    return sales, refunds, units


def test_stats_follow_records(app):
    def check():
        st, s = app.state(), app.api("getStats")
        sales, refunds, units = _stats_from_records(st)
        assert math.isclose(s["sales"], sales, abs_tol=0.02), (s, sales)
        assert math.isclose(s["refunds"], refunds, abs_tol=0.02), (s, refunds)
        assert math.isclose(s["net"], s["sales"] - s["refunds"], abs_tol=0.02)
        for sku, n in units.items():
            assert s["unitsSold"].get(sku, 0) == n, (sku, s["unitsSold"].get(sku), n)
        return s

    s0 = check()
    v = in_stock(app.state(), 3)[0]
    oid = place_order(app, [(v["sku"], 2)])
    assert check()["sales"] == pytest.approx(s0["sales"], abs=0.02), "unpaid orders are not sales"
    app.api("pay", oid)
    s1 = check()
    assert s1["sales"] > s0["sales"]
    app.api("ship", oid)
    app.api("requestAfterSale", oid, [{"sku": v["sku"], "qty": 1}], {"returnGoods": True})
    s2 = check()
    assert s2["refunds"] > s1["refunds"] and s2["net"] < s1["net"]
    assert s2["unitsSold"][v["sku"]] == s1["unitsSold"][v["sku"]] - 1


def test_query_filters(app):
    st = app.state()
    v = in_stock(st, 2)[0]
    oid = place_order(app, [(v["sku"], 1)])
    assert [o["id"] for o in app.api("queryOrders", {"orderId": oid})] == [oid]
    by_sku = app.api("queryOrders", {"sku": v["sku"]})
    assert oid in [o["id"] for o in by_sku] and all(any(i["sku"] == v["sku"] for i in o["items"]) for o in by_sku)
    for status in STATUSES:
        res = app.api("queryOrders", {"status": status})
        assert res and all(o["status"] == status for o in res)
    created = order(app.state(), oid)["createdAt"]
    day = created[:10]
    res = app.api("queryOrders", {"from": day, "to": day})
    assert oid in [o["id"] for o in res]
    old = min(o["createdAt"] for o in st["orders"])
    assert oid not in [o["id"] for o in app.api("queryOrders", {"to": old[:10]})]


# ---------- 10. persistence & backup ----------
def _snapshot(st):
    return (sorted((o["id"], o["status"], round(o["payable"], 2), round(o["refundedAmount"], 2)) for o in st["orders"]),
            sorted((v["sku"], v["stock"]) for _, v in variants(st)))


def test_reload_restores_data(app):
    v = in_stock(app.state(), 3)[0]
    oid = place_order(app, [(v["sku"], 2)])
    app.api("pay", oid)
    before = _snapshot(app.state())
    app.page.reload()
    app.page.wait_for_function("() => typeof window.shopTestAPI === 'object'")
    assert _snapshot(app.state()) == before


def test_export_import_roundtrip(app):
    v = in_stock(app.state(), 3)[0]
    oid = place_order(app, [(v["sku"], 1)])
    dump = app.api("exportData")
    assert isinstance(dump, str) and json.loads(dump)
    snap = _snapshot(app.state())
    app.api("cancel", oid)
    assert _snapshot(app.state()) != snap
    assert app.api("importData", dump)["ok"]
    assert _snapshot(app.state()) == snap


@pytest.mark.parametrize("bad", ["not json {", "{}", '{"products": []}', "[]"])
def test_bad_import_rejected_without_overwrite(app, bad):
    v = in_stock(app.state(), 2)[0]
    place_order(app, [(v["sku"], 1)])
    snap = _snapshot(app.state())
    r = app.api("importData", bad)
    assert r["ok"] is False and r.get("error"), "a bad import must report an error"
    assert _snapshot(app.state()) == snap


def test_truncated_export_rejected(app):
    dump = app.api("exportData")
    snap = _snapshot(app.state())
    r = app.api("importData", dump[: len(dump) // 2])
    assert r["ok"] is False
    obj = json.loads(dump)

    def strip_orders(o):  # remove the order list wherever it lives
        if isinstance(o, dict):
            return {k: ([] if k == "orders" else None if k in ("products",) else strip_orders(v)) for k, v in o.items()}
        return o

    r = app.api("importData", json.dumps(strip_orders(obj)))
    assert r["ok"] is False, "backup without products must be rejected"
    assert _snapshot(app.state()) == snap


# ---------- 11. end-to-end flows from the brief ----------
def test_flow_order_pay_ship_partial_return_restock(app):
    oid, lines = coupon_order(app)
    st0 = app.state()
    s0 = app.api("getStats")
    assert app.api("pay", oid)["ok"] and app.api("ship", oid)["ok"]
    sku, q = lines[0]
    stock_after_ship = stock(app.state(), sku)
    r = app.api("requestAfterSale", oid, [{"sku": sku, "qty": 1}], {"returnGoods": True})
    assert r["ok"]
    assert stock(app.state(), sku) == stock_after_ship
    assert app.api("confirmReturn", r["refundId"])["ok"]
    st = app.state()
    assert stock(st, sku) == stock_after_ship + 1
    o = order(st, oid)
    assert 0 < o["refundedAmount"] < o["payable"]
    s = app.api("getStats")
    assert math.isclose(s["refunds"] - s0["refunds"], r["amount"], abs_tol=CENT)
    assert math.isclose(s["sales"] - s0["sales"], o["payable"], abs_tol=CENT)


def test_flow_order_cancel(app):
    v = in_stock(app.state(), 2)[0]
    s0 = app.api("getStats")
    oid = place_order(app, [(v["sku"], 2)])
    assert app.api("cancel", oid)["ok"]
    st = app.state()
    assert stock(st, v["sku"]) == v["stock"] and order(st, oid)["status"] == "cancelled"
    s = app.api("getStats")
    assert math.isclose(s["net"], s0["net"], abs_tol=CENT)
