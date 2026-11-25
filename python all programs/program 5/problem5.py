"""
Laboratory Chemical Inventory Validation
----------------------------------------
Checks hypothetical chemical inventory records against storage rules and flags invalid ones.

A record is flagged INVALID when any of these is true
  1. its record ID is duplicated
  2. its quantity is not a positive number
  3. its hazard class is unknown
  4. its storage location does not exist
  5. its hazard class is not allowed in that location's storage category
  6. it shares a location with a hazard class it is incompatible with
  7. the total quantity in its location exceeds the location's maximum
All rules (categories, maximum quantities, incompatible pairs) are hypothetical and
can be edited in the tables below.
"""

from dataclasses import dataclass

HAZARD_CLASSES = ["Flammable", "Oxidizer", "Acid", "Base", "Toxic", "General"]

# storage category -> hazard classes that may be stored there
CATEGORY_ALLOWED = {
    "Flammable":  {"Flammable"},
    "Corrosive":  {"Acid", "Base"},
    "Oxidizer":   {"Oxidizer"},
    "Toxic":      {"Toxic"},
    "General":    {"General", "Toxic", "Acid", "Base"},
    "Open shelf": set(HAZARD_CLASSES),
}

# pairs of hazard classes that must not share a location
INCOMPATIBLE = [
    frozenset({"Acid", "Base"}),
    frozenset({"Flammable", "Oxidizer"}),
    frozenset({"Acid", "Toxic"}),
]


@dataclass
class Location:
    loc_id: str
    category: str
    max_qty: float          # litres, total allowed in the location


@dataclass
class Chemical:
    rec_id: str
    name: str
    hazard: str
    qty: float              # litres
    location: str


def validate(locations, chemicals):
    """Return (record results, location summaries)."""
    loc_map = {l.loc_id: l for l in locations}
    id_counts = {}
    for c in chemicals:
        id_counts[c.rec_id] = id_counts.get(c.rec_id, 0) + 1

    # group the usable records by location
    by_loc = {}
    for c in chemicals:
        if c.location in loc_map:
            by_loc.setdefault(c.location, []).append(c)

    loc_summary = {}
    for l in locations:
        recs = by_loc.get(l.loc_id, [])
        total = sum(c.qty for c in recs if c.qty > 0)
        loc_summary[l.loc_id] = {"loc": l, "total": total, "over": total > l.max_qty}

    results = []
    for c in chemicals:
        issues = []
        if id_counts[c.rec_id] > 1:
            issues.append("duplicate record ID")
        if c.qty <= 0:
            issues.append(f"invalid quantity ({c.qty:g})")
        if c.hazard not in HAZARD_CLASSES:
            issues.append(f"unknown hazard class '{c.hazard}'")
        if c.location not in loc_map:
            issues.append(f"unknown location '{c.location}'")
        else:
            loc = loc_map[c.location]
            if c.hazard in HAZARD_CLASSES and c.hazard not in CATEGORY_ALLOWED[loc.category]:
                issues.append(f"{c.hazard} not allowed in {loc.category} storage ({loc.loc_id})")
            for other in by_loc[c.location]:
                if other is not c and frozenset({c.hazard, other.hazard}) in INCOMPATIBLE:
                    issues.append(f"incompatible with {other.name} ({other.hazard}) in {loc.loc_id}")
            summ = loc_summary[c.location]
            if summ["over"]:
                issues.append(f"{loc.loc_id} over capacity ({summ['total']:g} L > {loc.max_qty:g} L)")
        results.append({"chem": c, "issues": issues, "valid": not issues})
    return results, list(loc_summary.values())


def print_report(results, loc_summaries):
    head = f"{'ID':<6}{'Chemical':<24}{'Class':<11}{'Qty(L)':>7}  {'Loc':<5}Status"
    print("RECORDS")
    print(head)
    print("-" * (len(head) + 8))
    for r in results:
        c = r["chem"]
        print(f"{c.rec_id:<6}{c.name:<24}{c.hazard:<11}{c.qty:>7g}  {c.location:<5}{'VALID' if r['valid'] else 'INVALID'}")
        for issue in r["issues"]:
            print(f"        - {issue}")
    print("\nLOCATIONS")
    head = f"{'Loc':<5}{'Category':<12}{'Max(L)':>7}{'Total(L)':>10}  Status"
    print(head)
    print("-" * (len(head) + 6))
    for s in loc_summaries:
        l = s["loc"]
        print(f"{l.loc_id:<5}{l.category:<12}{l.max_qty:>7g}{s['total']:>10g}  {'OVER CAPACITY' if s['over'] else 'OK'}")
    bad = sum(not r["valid"] for r in results)
    print(f"\nSummary: {len(results)} records checked, {len(results) - bad} valid, {bad} flagged invalid.")


def read_float(prompt):
    while True:
        try:
            v = float(input(prompt))
            if v > 0:
                return v
            print("  Enter a value greater than 0.")
        except ValueError:
            print("  Invalid number, try again.")


def read_count(prompt):
    while True:
        try:
            n = int(input(prompt))
            if n >= 1:
                return n
        except ValueError:
            pass
        print("  Enter a whole number of at least 1.")


def read_choice(prompt, options):
    for n, o in enumerate(options, 1):
        print(f"    {n}. {o}")
    while True:
        try:
            k = int(input(prompt))
            if 1 <= k <= len(options):
                return options[k - 1]
        except ValueError:
            pass
        print(f"  Enter a number from 1 to {len(options)}.")


def get_input():
    locations = []
    for i in range(read_count("Number of storage locations: ")):
        loc_id = input(f"Location {i + 1} ID: ").strip() or f"L{i + 1}"
        category = read_choice("  Storage category: ", list(CATEGORY_ALLOWED))
        locations.append(Location(loc_id, category, read_float("  Maximum quantity (L): ")))
    chemicals = []
    for i in range(read_count("Number of chemical records: ")):
        rec_id = input(f"Record {i + 1} ID: ").strip() or f"R{i + 1}"
        name = input("  Chemical name: ").strip() or "Unnamed"
        hazard = read_choice("  Hazard class: ", HAZARD_CLASSES)
        qty = read_float("  Quantity (L): ")
        location = input("  Storage location ID: ").strip()
        chemicals.append(Chemical(rec_id, name, hazard, qty, location))
    return locations, chemicals


def sample_data():
    locations = [
        Location("F1", "Flammable", 20), Location("C1", "Corrosive", 15),
        Location("O1", "Oxidizer", 10),  Location("T1", "Toxic", 5),
        Location("G1", "General", 25),   Location("S1", "Open shelf", 10),
    ]
    C = Chemical
    chemicals = [
        C("R01", "Ethanol", "Flammable", 8, "F1"),
        C("R02", "Acetone", "Flammable", 10, "F1"),
        C("R03", "Hydrochloric acid", "Acid", 6, "C1"),
        C("R04", "Sodium hydroxide", "Base", 5, "C1"),
        C("R05", "Hydrogen peroxide", "Oxidizer", 4, "O1"),
        C("R06", "Potassium permanganate", "Oxidizer", 8, "O1"),
        C("R07", "Sodium cyanide", "Toxic", 1, "T1"),
        C("R08", "Toluene", "Flammable", 3, "G1"),
        C("R09", "Sodium chloride", "General", 12, "G1"),
        C("R10", "Nitric acid", "Acid", 2, "S1"),
        C("R11", "Methanol", "Flammable", 2, "S1"),
        C("R12", "Ammonium nitrate", "Oxidizer", 3, "S1"),
        C("R13", "Unknown dye", "Dye", 1, "G1"),
        C("R14", "Sulfuric acid", "Acid", 3, "X9"),
        C("R15", "Glycerol", "General", -2, "G1"),
    ]
    return locations, chemicals


if __name__ == "__main__":
    choice = input("Use sample data? (y/n): ").strip().lower()
    locations, chemicals = sample_data() if choice == "y" else get_input()
    print()
    results, summaries = validate(locations, chemicals)
    print_report(results, summaries)