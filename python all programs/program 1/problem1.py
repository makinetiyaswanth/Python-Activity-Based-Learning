"""
Fuel Consumption and Route Comparison
-------------------------------------
For every (route, vehicle) pair:
  fuel_needed   = distance / mileage
  total_needed  = fuel_needed + reserve
  feasible      = total_needed <= tank_capacity   (single trip, no refuelling)
  journey_cost  = fuel_needed * fuel_price
The lowest-cost feasible option is reported.
"""

from dataclasses import dataclass


@dataclass
class Vehicle:
    name: str
    mileage: float        # km per litre
    fuel_price: float     # price per litre
    tank_capacity: float  # litres
    reserve: float        # litres that must remain in the tank at arrival


@dataclass
class Route:
    name: str
    distance: float       # km


def evaluate(route: Route, vehicle: Vehicle) -> dict:
    fuel_needed = route.distance / vehicle.mileage
    total_needed = fuel_needed + vehicle.reserve
    return {
        "route": route.name,
        "vehicle": vehicle.name,
        "distance": route.distance,
        "fuel_needed": fuel_needed,
        "total_with_reserve": total_needed,
        "cost": fuel_needed * vehicle.fuel_price,
        "feasible": total_needed <= vehicle.tank_capacity,
    }


def compare(routes, vehicles):
    results = [evaluate(r, v) for r in routes for v in vehicles]
    feasible = [r for r in results if r["feasible"]]
    best = min(feasible, key=lambda r: r["cost"]) if feasible else None
    return results, best


def print_report(results, best):
    header = (f"{'Route':<12}{'Vehicle':<12}{'Dist(km)':>9}{'Fuel(L)':>9}"
              f"{'+Reserve(L)':>13}{'Cost':>10}  Feasible")
    print(header)
    print("-" * len(header))
    for r in results:
        print(f"{r['route']:<12}{r['vehicle']:<12}{r['distance']:>9.1f}"
              f"{r['fuel_needed']:>9.2f}{r['total_with_reserve']:>13.2f}"
              f"{r['cost']:>10.2f}  {'Yes' if r['feasible'] else 'No'}")
    print()
    if best:
        print("Lowest-cost feasible option:")
        print(f"  Route   : {best['route']} ({best['distance']} km)")
        print(f"  Vehicle : {best['vehicle']}")
        print(f"  Fuel    : {best['fuel_needed']:.2f} L (+ reserve = {best['total_with_reserve']:.2f} L)")
        print(f"  Cost    : {best['cost']:.2f}")
    else:
        print("No feasible option: every vehicle needs more fuel (with reserve) than its tank holds.")


def read_float(prompt):
    while True:
        try:
            value = float(input(prompt))
            if value > 0:
                return value
            print("  Enter a value greater than 0.")
        except ValueError:
            print("  Invalid number, try again.")


def read_reserve(prompt):
    while True:
        try:
            value = float(input(prompt))
            if value >= 0:
                return value
            print("  Reserve cannot be negative.")
        except ValueError:
            print("  Invalid number, try again.")


def get_input():
    routes = []
    for i in