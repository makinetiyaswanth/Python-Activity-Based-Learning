from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Product:
    sku: str
    name: str
    price: float
    initial_stock: int
    current_stock: int = field(init=False)

    def __post_init__(self):
        self.current_stock = self.initial_stock


@dataclass
class Order:
    order_id: str
    sku: str
    quantity: int
    discount_pct: float = 0.0
    status: str = "PENDING"  # PENDING, FULFILLED, REJECTED, RETURNED
    revenue_collected: float = 0.0
    rejection_reason: str = ""


class ECommerceReconciler:
    def __init__(self, inventory: List[Product]):
        self.inventory: Dict[str, Product] = {p.sku: p for p in inventory}
        self.orders: Dict[str, Order] = {}
        self.dispatched_log: List[str] = []
        self.returned_log: List[str] = []
        self.discrepancies: List[str] = []

    def process_order(self, order: Order) -> None:
        """Validates stock, applies discounts, calculates revenue, and updates inventory."""
        self.orders[order.order_id] = order

        if order.sku not in self.inventory:
            order.status = "REJECTED"
            order.rejection_reason = f"Invalid SKU: {order.sku}"
            self.discrepancies.append(f"[{order.order_id}] Ordered non-existent SKU '{order.sku}'.")
            return

        product = self.inventory[order.sku]

        if order.quantity <= 0:
            order.status = "REJECTED"
            order.rejection_reason = "Invalid quantity (<= 0)"
            self.discrepancies.append(f"[{order.order_id}] Invalid quantity {order.quantity}.")
            return

        if product.current_stock < order.quantity:
            order.status = "REJECTED"
            order.rejection_reason = f"Insufficient stock (Requested: {order.quantity}, Available: {product.current_stock})"
            self.discrepancies.append(
                f"[{order.order_id}] Stockout for {product.sku}: requested {order.quantity}, only {product.current_stock} left."
            )
            return

        # Fulfill order & deduct stock
        product.current_stock -= order.quantity
        gross_amount = product.price * order.quantity
        discount_amount = gross_amount * (order.discount_pct / 100.0)
        order.revenue_collected = round(gross_amount - discount_amount, 2)
        order.status = "FULFILLED"

    def dispatch_order(self, order_id: str) -> None:
        """Marks a fulfilled order as dispatched; flags unfulfilled or duplicate dispatches."""
        if order_id not in self.orders:
            self.discrepancies.append(f"[DISPATCH] Attempted to dispatch unknown order '{order_id}'.")
            return

        order = self.orders[order_id]
        if order_id in self.dispatched_log:
            self.discrepancies.append(f"[DISPATCH] Duplicate dispatch attempt for '{order_id}'.")
            return

        if order.status != "FULFILLED":
            self.discrepancies.append(
                f"[DISPATCH] Cannot dispatch '{order_id}' because status is '{order.status}' ({order.rejection_reason})."
            )
            return

        self.dispatched_log.append(order_id)

    def process_return(self, order_id: str, return_qty: int, restock: bool = True) -> None:
        """Processes full/partial returns, refunds revenue proportionally, and optionally restocks."""
        if order_id not in self.orders:
            self.discrepancies.append(f"[RETURN] Return received for unknown order '{order_id}'.")
            return

        order = self.orders[order_id]

        if order_id not in self.dispatched_log:
            self.discrepancies.append(f"[RETURN] Order '{order_id}' was returned without a dispatch record.")
            return

        if return_qty > order.quantity or return_qty <= 0:
            self.discrepancies.append(
                f"[RETURN] Invalid return quantity ({return_qty}) for '{order_id}' (Ordered: {order.quantity})."
            )
            return

        # Calculate proportional refund
        unit_net_price = order.revenue_collected / order.quantity
        refund_amount = round(unit_net_price * return_qty, 2)
        order.revenue_collected = round(order.revenue_collected - refund_amount, 2)
        order.status = "RETURNED" if return_qty == order.quantity else "PARTIALLY_RETURNED"
        self.returned_log.append(order_id)

        if restock:
            self.inventory[order.sku].current_stock += return_qty
        else:
            self.discrepancies.append(
                f"[RETURN] {return_qty} unit(s) of {order.sku} from '{order_id}' returned damaged (not restocked)."
            )

    def audit_physical_stock(self, physical_counts: Dict[str, int]) -> None:
        """Compares system stock against actual warehouse physical counts."""
        for sku, actual_qty in physical_counts.items():
            if sku not in self.inventory:
                self.discrepancies.append(f"[AUDIT] Physical warehouse has unknown SKU '{sku}' ({actual_qty} units).")
                continue

            expected_qty = self.inventory[sku].current_stock
            if actual_qty != expected_qty:
                diff = actual_qty - expected_qty
                self.discrepancies.append(
                    f"[AUDIT] Stock mismatch for {sku}: System={expected_qty}, Physical={actual_qty} (Diff: {diff:+d})."
                )

    def generate_report(self) -> None:
        """Prints financial metrics, discrepancy logs, and final inventory summary."""
        total_revenue = sum(o.revenue_collected for o in self.orders.values())
        fulfilled_count = sum(1 for o in self.orders.values() if o.status in ("FULFILLED", "PARTIALLY_RETURNED"))
        rejected_count = sum(1 for o in self.orders.values() if o.status == "REJECTED")

        print("=" * 65)
        print("E-COMMERCE ORDER & INVENTORY RECONCILIATION REPORT")
        print("=" * 65)

        print(f"\n[1] FINANCIAL & ORDER SUMMARY")
        print(f"  Total Orders Received : {len(self.orders)}")
        print(f"  Active Fulfilled      : {fulfilled_count}")
        print(f"  Rejected Orders       : {rejected_count}")
        print(f"  Dispatched Shipments  : {len(self.dispatched_log)}")
        print(f"  Net Revenue Collected : ₹{total_revenue:,.2f}")

        print(f"\n[2] FINAL INVENTORY SUMMARY")
        print(f"  {'SKU':<10} {'Product Name':<22} {'Initial':<10} {'Final':<10} {'Unit Price'}")
        print("  " + "-" * 61)
        for p in self.inventory.values():
            print(f"  {p.sku:<10} {p.name:<22} {p.initial_stock:<10} {p.current_stock:<10} ₹{p.price:,.2f}")

        print(f"\n[3] IDENTIFIED DISCREPANCIES ({len(self.discrepancies)})")
        if not self.discrepancies:
            print("  None — All records reconciled cleanly.")
        else:
            for idx, issue in enumerate(self.discrepancies, 1):
                print(f"  {idx}. {issue}")
        print("=" * 65)


# ==========================================
# EXAMPLE EXECUTION / SIMULATION
# ==========================================
if __name__ == "__main__":
    # 1. Initialize Warehouse Inventory
    catalog = [
        Product(sku="LAP-01", name="ProBook Laptop", price=65000.00, initial_stock=10),
        Product(sku="MOU-02", name="Wireless Mouse", price=1200.00, initial_stock=25),
        Product(sku="KEY-03", name="Mechanical Keyboard", price=3500.00, initial_stock=5),
    ]

    system = ECommerceReconciler(catalog)

    # 2. Process Incoming Orders (with discounts)
    incoming_orders = [
        Order(order_id="ORD-101", sku="LAP-01", quantity=2, discount_pct=10.0),   # Valid: ₹1,17,000
        Order(order_id="ORD-102", sku="KEY-03", quantity=4, discount_pct=5.0),    # Valid: ₹13,300
        Order(order_id="ORD-103", sku="KEY-03", quantity=3, discount_pct=0.0),    # Fails: Only 1 left!
        Order(order_id="ORD-104", sku="MOU-02", quantity=5, discount_pct=15.0),   # Valid: ₹5,100
        Order(order_id="ORD-105", sku="UNK-99", quantity=1, discount_pct=0.0),    # Fails: Unknown SKU
    ]

    for ord_item in incoming_orders:
        system.process_order(ord_item)

    # 3. Dispatch Shipments
    system.dispatch_order("ORD-101")
    system.dispatch_order("ORD-102")
    system.dispatch_order("ORD-103")  # Discrepancy: Trying to dispatch rejected order
    system.dispatch_order("ORD-101")  # Discrepancy: Duplicate dispatch

    # 4. Process Returns
    system.process_return("ORD-101", return_qty=1, restock=True)   # Partial return, restocked
    system.process_return("ORD-102", return_qty=1, restock=False)  # Damaged return, not restocked
    system.process_return("ORD-104", return_qty=1, restock=True)   # Discrepancy: Returned before dispatch

    # 5. Physical Warehouse Audit vs. System Stock
    warehouse_physical_counts = {
        "LAP-01": 9,   # Matches system (10 - 2 + 1)
        "MOU-02": 19,  # Discrepancy: System thinks 20, warehouse only found 19 (1 missing/pilfered)
        "KEY-03": 1,   # Matches system (5 - 4 + 0 damaged)
    }
    system.audit_physical_stock(warehouse_physical_counts)

    # 6. Output Final Reconciliation Report
    system.generate_report()