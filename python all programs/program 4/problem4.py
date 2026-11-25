"""
Traffic Violation Penalty Calculator
------------------------------------
Processes the violations recorded against one vehicle (challan).

For every violation
  base fine   = fine from the rule table for (offence, vehicle category)
  final fine  = base fine x repeat multiplier   (multiplier applies only if it is a repeat offence)
  points      = penalty points for the offence

For the whole challan
  total fine   = sum of the final fines
  total points = sum of the points
  disqualification (the most severe applies):
     - offence rule : e.g. drunk driving -> licence suspended (first) / cancelled (repeat)
     - points rule  : total points >= POINTS_SUSPEND_AT -> licence suspended for POINTS_SUSPEND_MONTHS
Offences that do not apply to the vehicle category (e.g. helmet for a car) are rejected, not charged.
All fines are illustrative; edit RULES to match the official fine schedule.
"""

from dataclasses import dataclass

CATEGORIES = ["Two-wheeler", "Car", "Heavy Vehicle"]

# fines: base fine per category (a category that is missing = offence not applicable)
# repeat_mult: multiplier on the fine for a repeat offence
# first / repeat: disqualification action -> None, ("SUSPEND", months) or ("CANCEL",)
RULES = {
    "Speeding":         {"fines": {"Two-wheeler": 1000, "Car": 2000, "Heavy Vehicle": 4000},
                         "repeat_mult": 2, "points": 3, "first": None, "repeat": None},
    "Red light":        {"fines": {"Two-wheeler": 1000, "Car": 1000, "Heavy Vehicle": 1000},
                         "repeat_mult": 2, "points": 3, "first": None, "repeat": ("SUSPEND", 3)},
    "No helmet":        {"fines": {"Two-wheeler": 1000},
                         "repeat_mult": 2, "points": 1, "first": None, "repeat": None},
    "No seat belt":     {"fines": {"Car": 1000, "Heavy Vehicle": 1000},
                         "repeat_mult": 2, "points": 1, "first": None, "repeat": None},
    "Mobile phone":     {"fines": {"Two-wheeler": 5000, "Car": 5000, "Heavy Vehicle": 5000},
                         "repeat_mult": 2, "points": 2, "first": None, "repeat": None},
    "Drunk driving":    {"fines": {"Two-wheeler": 10000, "Car": 10000, "Heavy Vehicle": 10000},
                         "repeat_mult": 2, "points": 6, "first": ("SUSPEND", 6), "repeat": ("CANCEL",)},
    "No licence":       {"fines": {"Two-wheeler": 5000, "Car": 5000, "Heavy Vehicle": 5000},
                         "repeat_mult": 2, "points": 4, "first": None, "repeat": None},
    "Overloading":      {"fines": {"Heavy Vehicle": 20000},
                         "repeat_mult": 2, "points": 3, "first": None, "repeat": None},
}
POINTS_SUSPEND_AT = 8       # total points on one challan that trigger a suspension
POINTS_SUSPEND_MONTHS = 3


@dataclass
class Violation:
    offence: str
    repeat: bool = False


def describe(action):
    if action is None:
        return "-"
    return "Licence CANCELLED" if action[0] == "CANCEL" else f"Licence suspended {action[1]} months"


def severity(action):
    """Higher number = more severe (cancel > longer suspension > none)."""
    if action is None:
        return 0
    return 10**6 if action[0] == "CANCEL" else action[1]


def assess(violation: Violation, category: str) -> dict:
    """Price one violation. 'valid' is False if the offence is unknown or not applicable."""
    rule = RULES.get(violation.offence)
    if rule is None:
        return {"v": violation, "valid": False, "note": "unknown offence"}
    base = rule["fines"].get(category)
    if base is None:
        return {"v": violation, "valid": False, "note": f"not applicable to {category}"}
    mult = rule["repeat_mult"] if violation.repeat else 1
    action = rule["repeat"] if violation.repeat else rule["first"]
    return {"v": violation, "valid": True, "base": base, "mult": mult, "fine": base * mult,
            "points": rule["points"], "action": action}


def process_challan(category: str, violations: list) -> dict:
    items = [assess(v, category) for v in violations]
    valid = [i for i in items if i["valid"]]
    total_fine = sum(i["fine"] for i in valid)
    total_points = sum(i["points"] for i in valid)

    reasons = []   # (action, why)
    for i in valid:
        if i["action"] is not None:
            reasons.append((i["action"], f"{i['v'].offence}{' (repeat)' if i['v'].repeat else ''}"))
    if total_points >= POINTS_SUSPEND_AT:
        reasons.append((("SUSPEND", POINTS_SUSPEND_MONTHS), f"{total_points} penalty points (limit {POINTS_SUSPEND_AT})"))
    final_action, why = max(reasons, key=lambda r: severity(r[0]), default=(None, ""))
    return {"category": category, "items": items, "total_fine": total_fine,
            "total_points": total_points, "action": final_action, "why": why}


def print_challan(no: int, result: dict):
    print(f"--- Challan {no}: {result['category']} ---")
    head = f"{'Offence':<15}{'Repeat':<8}{'Base':>8}{'Mult':>6}{'Fine':>9}{'Pts':>5}  Result"
    print(head)
    print("-" * len(head))
    for i in result["items"]:
        v = i["v"]
        if i["valid"]:
            print(f"{v.offence:<15}{'Yes' if v.repeat else 'No':<8}{i['base']:>8}{'x' + str(i['mult']):>6}"
                  f"{i['fine']:>9}{i['points']:>5}  {describe(i['action'])}")
        else:
            print(f"{v.offence:<15}{'Yes' if v.repeat else 'No':<8}{'-':>8}{'-':>6}{'-':>9}{'-':>5}  REJECTED: {i['note']}")
    print("-" * len(head))
    print(f"Total fine   : Rs. {result['total_fine']}")
    print(f"Total points : {result['total_points']}")
    if result["action"] is None:
        print("Disqualification: none")
    else:
        print(f"Disqualification: {describe(result['action'])}  (reason: {result['why']})")
    print()


def read_choice(prompt, options):
    for n, o in enumerate(options, 1):
        print(f"  {n}. {o}")
    while True:
        try:
            k = int(input(prompt))
            if 1 <= k <= len(options):
                return options[k - 1]
        except ValueError:
            pass
        print(f"  Enter a number from 1 to {len(options)}.")


def read_yes_no(prompt):
    while True:
        a = input(prompt).strip().lower()
        if a in ("y", "yes"):
            return True
        if a in ("n", "no"):
            return False
        print("  Enter y or n.")


def read_count(prompt):
    while True:
        try:
            n = int(input(prompt))
            if n >= 0:
                return n
        except ValueError:
            pass
        print("  Enter a whole number (0 or more).")


def get_input():
    challans = []
    for c in range(1, read_count("Number of vehicles / challans: ") + 1):
        print(f"Challan {c} - vehicle category:")
        category = read_choice("  Choose: ", CATEGORIES)
        violations = []
        for v in range(1, read_count("  Number of violations: ") + 1):
            print(f"  Violation {v} - offence:")
            offence = read_choice("    Choose: ", list(RULES))
            violations.append(Violation(offence, read_yes_no("    Repeat offence? (y/n): ")))
        challans.append((category, violations))
    return challans


def sample_data():
    V = Violation
    return [
        ("Two-wheeler",   [V("No helmet"), V("Red light"), V("Speeding", True), V("Mobile phone")]),
        ("Car",           [V("Drunk driving", True), V("No licence")]),
        ("Heavy Vehicle", [V("Overloading"), V("Speeding")]),
        ("Car",           [V("No seat belt")]),
        ("Car",           [V("No helmet"), V("Parking")]),
    ]


if __name__ == "__main__":
    choice = input("Use sample data? (y/n): ").strip().lower()
    challans = sample_data() if choice == "y" else get_input()
    print()
    for n, (category, violations) in enumerate(challans, 1):
        print_challan(n, process_challan(category, violations))