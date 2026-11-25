"""
Multi-Product Shopping Budget Constraint
----------------------------------------
Evaluate a basket (several products, each with a quantity), apply discounts,
and, if the total is over budget, decide which purchases must be reduced.

Discount rules
  1. Bulk discount (per product): if qty >= bulk_min, bulk_pct % is taken off that product.
  2. Basket discount: if the total after bulk discounts >= BASKET_MIN, BASKET_PCT % is taken off.

Reduction rules (only when the total is over budget)
  - Remove one unit at a time from the LEAST important product (highest priority
    number, 1 = most important). Ties: the product with the higher unit price goes first.
  - A product is never reduced below its min_qty (the must-buy quantity).
  - Discounts are recalculated after every removal.
  - Finally, units are added back (most important first) while the total stays within budget.
"""

from dataclasses import dataclass

BASKET_MIN = 1000.0   # basket discount applies from this amount
BASKET_PCT = 5.0      # percent


@dataclass
class Product:
    name: str
    price: float          # per unit
    qty: int              # wanted quantity
    priority: int         # 1 = most important, larger = less important
    min_qty: int = 0      # quantity that must not be cut
    bulk_min: int = 0     # bulk discount threshold (0 = no bulk discount)
    bulk_pct: float = 0.0 # bulk discount percent


def line_cost(p: Product, qty: int):
    """Return (gross, bulk_discount) for qty units of product p."""
    gross = p.price * qty
    discount = gross * p.bulk_pct / 100 if p.bulk_min and qty >= p.bulk_min else 0.0
    return gross, discount


def basket_total(products, qtys):
    gross = bulk = 0.0
    for p, q in zip(products, qtys):
        g, d = line_cost(p, q)
        gross += g
        bulk += d
    after_bulk = gross - bulk
    basket_disc = after_bulk * BASKET_PCT / 100 if after_bulk >= BASKET_MIN else 0.0
    return {"gross": gross, "bulk": bulk, "basket": basket_disc,
            "total": after_bulk - basket_disc}


def fit_to_budget(products, budget):
    """Return the final quantities (list) that fit the budget, if possible."""
    qtys = [p.qty for p in products]
    # Phase 1: reduce the least important items until within budget
    while basket_total(products, qtys)["total"] > budget:
        candidates = [i for i, p in enumerate(products) if qtys[i] > p.min_qty]
        if not candidates:
            break  # nothing left that may be reduced
        i = max(candidates, key=lambda k: (products[k].priority, products[k].price))
        qtys[i] -= 1
    # Phase 2: add units back (most important first) while still within budget
    if basket_total(products, qtys)["total"] <= budget:
        for i in sorted(range(len(products)), key=lambda k: (products[k].priority, -products[k].price)):
            while qtys[i] < products[i].qty:
                qtys[i] += 1
                if basket_total(products, qtys)["total"] > budget:
                    qtys[i] -= 1
                    break
    return qtys


def print_basket(products, qtys, title):
    print(title)
    head = f"{'Product':<14}{'Price':>8}{'Qty':>5}{'Gross':>10}{'Bulk disc':>11}{'Net':>10}"
    print(head)
    print("-" * len(head))
    for p, q in zip(products, qtys):
        g, d = line_cost(p, q)
        print(f"{p.name:<14}{p.price:>8.2f}{q:>5}{g:>10.2f}{d:>11.2f}{g - d:>10.2f}")
    t = basket_total(products, qtys)
    print("-" * len(head))
    print(f"{'Basket discount (' + str(BASKET_PCT) + '%)':<37}{t['basket']:>24.2f}")
    print(f"{'TOTAL':<37}{t['total']:>24.2f}")
    return t


def report(products, budget):
    print(f"Budget: {budget:.2f}\n")
    original = [p.qty for p in products]
    t0 = print_basket(products, original, "ORIGINAL BASKET")
    print()
    if t0["total"] <= budget:
        print(f"Within budget (saves {budget - t0['total']:.2f}). No reduction needed.")
        return
    print(f"Over budget by {t0['total'] - budget:.2f}. Reducing purchases...\n")
    final = fit_to_budget(products, budget)
    t1 = print_basket(products, final, "ADJUSTED BASKET")
    print("\nReductions:")
    changed = False
    for p, o, f in zip(products, original, final):
        if f < o:
            changed = True
            print(f"  {p.name:<14}{o} -> {f}  (reduce by {o - f}, priority {p.priority})")
    if not changed:
        print("  none possible")
    if t1["total"] <= budget:
        print(f"\nFinal total {t1['total']:.2f} is within the budget (left over {budget - t1['total']:.2f}).")
    else:
        print(f"\nStill over budget by {t1['total'] - budget:.2f}: only must-buy quantities remain.")


def read_num(prompt, cast=float, minimum=0.0, strict=False):
    while True:
        try:
            v = cast(input(prompt))
            if (v > minimum) if strict else (v >= minimum):
                return v
            print(f"  Enter a value {'greater than' if strict else 'of at least'} {minimum}.")
        except ValueError:
            print("  Invalid number, try again.")


def get_input():
    budget = read_num("Budget: ", float, 0, strict=True)
    products = []
    for i in range(read_num("Number of products: ", int, 0, strict=True)):
        name = input(f"Product {i + 1} name: ").strip() or f"Item{i + 1}"
        price = read_num("  Unit price: ", float, 0, strict=True)
        qty = read_num("  Quantity wanted: ", int, 0, strict=True)
        pri = read_num("  Priority (1 = most important): ", int, 1)
        mn = int(read_num(f"  Must-buy quantity (0 to {qty}): ", int, 0))
        mn = min(mn, qty)
        bmin = read_num("  Bulk discount from qty (0 = none): ", int, 0)
        bpct = read_num("  Bulk discount percent: ", float, 0) if bmin else 0.0
        products.append(Product(name, price, qty, pri, mn, bmin, bpct))
    return products, budget


def sample_data():
    products = [
        Product("Rice (kg)",   60, 10, 1, 5, 8, 10),
        Product("Milk (L)",    25,  8, 1, 4, 6, 5),
        Product("Biscuits",    30,  6, 3, 0, 5, 10),
        Product("Juice",       45,  4, 3, 0, 4, 8),
        Product("Chocolates",  50,  5, 4, 0, 0, 0),
    ]
    return products, 900.0


if __name__ == "__main__":
    choice = input("Use sample data? (y/n): ").strip().lower()
    products, budget = sample_data() if choice == "y" else get_input()
    print()
    report(products, budget)