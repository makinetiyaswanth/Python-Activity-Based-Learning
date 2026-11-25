"""
University Admission Decision Engine
------------------------------------
Evaluates candidates for the course they applied to and produces a ranked list.

Eligibility (all must hold)
  1. The candidate has marks for every subject the course requires.
  2. Each required subject meets that subject's minimum marks.
  3. The aggregate (average of the required subjects) meets the course's cutoff.

Ranking (eligible candidates only, best first)
  1. Higher aggregate
  2. Tie-break: higher marks in the course's required subjects, in the order they are listed
  3. Final tie-break: earlier application number
The top 'seats' candidates are ADMITTED; the rest of the eligible list is WAITLISTED.
"""

from dataclasses import dataclass, field


@dataclass
class Course:
    name: str
    seats: int
    min_aggregate: float
    required: dict            # subject -> minimum marks (order = tie-break order)


@dataclass
class Candidate:
    app_id: int
    name: str
    course: str
    marks: dict = field(default_factory=dict)   # subject -> marks (0-100)


def evaluate(cand: Candidate, course: Course) -> dict:
    """Check eligibility and compute the aggregate. 'reasons' lists every failed rule."""
    reasons = []
    scores = []
    for subject, minimum in course.required.items():
        mark = cand.marks.get(subject)
        if mark is None:
            reasons.append(f"missing subject {subject}")
        elif not 0 <= mark <= 100:
            reasons.append(f"invalid marks for {subject} ({mark})")
        else:
            scores.append(mark)
            if mark < minimum:
                reasons.append(f"{subject} {mark:g} < {minimum:g}")
    aggregate = sum(scores) / len(scores) if len(scores) == len(course.required) else None
    if aggregate is not None and aggregate < course.min_aggregate:
        reasons.append(f"aggregate {aggregate:.2f} < {course.min_aggregate:g}")
    return {"cand": cand, "aggregate": aggregate, "eligible": not reasons, "reasons": reasons}


def rank_key(result: dict, course: Course):
    """Sort key: aggregate (high first), then subject marks in order, then application number."""
    cand = result["cand"]
    subject_marks = [-cand.marks[s] for s in course.required]
    return (-result["aggregate"], *subject_marks, cand.app_id)


def decided_by(prev: dict, cur: dict, course: Course) -> str:
    """Which criterion separated 'cur' from the candidate ranked just above it."""
    if prev["aggregate"] != cur["aggregate"]:
        return "aggregate"
    for s in course.required:
        if prev["cand"].marks[s] != cur["cand"].marks[s]:
            return f"{s} marks"
    return "application no."


def process(course: Course, candidates: list):
    """Return (ranked eligible results, rejected results) for one course."""
    results = [evaluate(c, course) for c in candidates if c.course == course.name]
    eligible = sorted((r for r in results if r["eligible"]), key=lambda r: rank_key(r, course))
    rejected = [r for r in results if not r["eligible"]]
    return eligible, rejected


def print_course(course: Course, eligible: list, rejected: list):
    print(f"=== {course.name}  (seats: {course.seats}, min aggregate: {course.min_aggregate:g}) ===")
    req = ", ".join(f"{s} >= {m:g}" for s, m in course.required.items())
    print(f"Required subjects: {req}\n")
    if eligible:
        head = f"{'Rank':<5}{'App':<5}{'Name':<12}{'Aggregate':>10}  {'Status':<11}Ranked above next by"
        print(head)
        print("-" * (len(head) + 8))
        for i, r in enumerate(eligible, 1):
            status = "ADMITTED" if i <= course.seats else "WAITLISTED"
            note = decided_by(r, eligible[i], course) if i < len(eligible) else "-"
            print(f"{i:<5}{r['cand'].app_id:<5}{r['cand'].name:<12}{r['aggregate']:>10.2f}  {status:<11}{note}")
    else:
        print("No eligible applicants.")
    if rejected:
        print("\nNot eligible:")
        for r in rejected:
            print(f"  {r['cand'].app_id:<4}{r['cand'].name:<12}{'; '.join(r['reasons'])}")
    print()


def run_engine(courses: list, candidates: list):
    known = {c.name for c in courses}
    for course in courses:
        eligible, rejected = process(course, candidates)
        print_course(course, eligible, rejected)
    unknown = [c for c in candidates if c.course not in known]
    if unknown:
        print("=== Applications to unknown courses ===")
        for c in unknown:
            print(f"  {c.app_id:<4}{c.name:<12}course '{c.course}' does not exist")


def read_float(prompt, lo, hi=None):
    while True:
        try:
            v = float(input(prompt))
            if v >= lo and (hi is None or v <= hi):
                return v
            print(f"  Enter a value from {lo:g}" + (f" to {hi:g}." if hi is not None else "."))
        except ValueError:
            print("  Invalid number, try again.")


def read_marks(prompt):
    """Read 'Maths=80, Physics=75' into a dict."""
    while True:
        try:
            pairs = [p.split("=") for p in input(prompt).split(",") if p.strip()]
            marks = {k.strip(): float(v) for k, v in pairs}
            if all(0 <= m <= 100 for m in marks.values()):
                return marks
            print("  Marks must be between 0 and 100.")
        except ValueError:
            print("  Use the format  Subject=marks, Subject=marks")


def get_input():
    courses = []
    for i in range(int(read_float("Number of courses: ", 1))):
        name = input(f"Course {i + 1} name: ").strip() or f"Course{i + 1}"
        seats = int(read_float("  Seats: ", 1))
        cutoff = read_float("  Minimum aggregate (0-100): ", 0, 100)
        required = {}
        for j in range(int(read_float("  Number of required subjects: ", 1))):
            sub = input(f"    Subject {j + 1} name: ").strip() or f"Subject{j + 1}"
            required[sub] = read_float(f"    Minimum marks in {sub}: ", 0, 100)
        courses.append(Course(name, seats, cutoff, required))
    candidates = []
    for i in range(int(read_float("Number of applicants: ", 1))):
        name = input(f"Applicant {i + 1} name: ").strip() or f"Applicant{i + 1}"
        course = input("  Applied course: ").strip()
        marks = read_marks("  Marks (Subject=marks, ...): ")
        candidates.append(Candidate(i + 1, name, course, marks))
    return courses, candidates


def sample_data():
    courses = [
        Course("B.Tech CSE", 3, 70, {"Maths": 60, "Physics": 60, "English": 40}),
        Course("B.Sc Biology", 2, 65, {"Biology": 60, "Chemistry": 55}),
    ]
    C = Candidate
    candidates = [
        C(1, "Arun",    "B.Tech CSE",   {"Maths": 90, "Physics": 85, "English": 70}),
        C(2, "Bhavana", "B.Tech CSE",   {"Maths": 88, "Physics": 90, "English": 66}),
        C(3, "Charan",  "B.Tech CSE",   {"Maths": 95, "Physics": 80, "English": 70}),
        C(4, "Divya",   "B.Tech CSE",   {"Maths": 70, "Physics": 58, "English": 80}),
        C(5, "Eswar",   "B.Tech CSE",   {"Maths": 65, "Physics": 70, "English": 60}),
        C(6, "Farah",   "B.Tech CSE",   {"Maths": 85, "Physics": 80, "English": 85}),
        C(7, "Gopi",    "B.Tech CSE",   {"Maths": 80, "Physics": 80}),
        C(8, "Hari",    "B.Tech CSE",   {"Maths": 90, "Physics": 85, "English": 70}),
        C(9, "Isha",    "B.Sc Biology", {"Biology": 80, "Chemistry": 70}),
        C(10, "Jaya",   "B.Sc Biology", {"Biology": 75, "Chemistry": 75}),
        C(11, "Kiran",  "B.Sc Biology", {"Biology": 90, "Chemistry": 50}),
        C(12, "Lata",   "B.Sc Biology", {"Biology": 62, "Chemistry": 60}),
        C(13, "Mani",   "B.Sc Biology", {"Biology": 70, "Chemistry": 70}),
        C(14, "Nila",   "MBA",          {"Maths": 80, "English": 80}),
    ]
    return courses, candidates


if __name__ == "__main__":
    choice = input("Use sample data? (y/n): ").strip().lower()
    courses, candidates = sample_data() if choice == "y" else get_input()
    print()
    run_engine(courses, candidates)
    