from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class Course:
    code: str
    name: str
    credits: int
    min_pass_marks: float          # Minimum marks required to pass (out of 100)
    min_attendance_pct: float      # Minimum attendance % required for eligibility
    prerequisites: List[str] = field(default_factory=list)


@dataclass
class CourseAttempt:
    course_code: str
    semester: int
    marks_obtained: float          # Out of 100
    attendance_pct: float          # 0.0 to 100.0
    grade_points: float            # e.g., 10-point scale (10, 9, 8, ..., 0)


@dataclass
class StudentRecord:
    student_id: str
    name: str
    current_semester: int
    overall_min_attendance_pct: float = 75.0
    min_cgpa_for_progression: float = 5.0
    max_allowed_backlogs: int = 2
    attempts: List[CourseAttempt] = field(default_factory=list)


class AcademicProgressionAuditor:
    def __init__(
        self,
        curriculum: List[Course],
        required_courses_by_semester: Optional[Dict[int, List[str]]] = None,
    ):
        self.curriculum: Dict[str, Course] = {c.code: c for c in curriculum}
        # Optional map of semester -> list of course codes expected up to/by that semester
        self.required_courses_by_semester: Dict[int, List[str]] = (
            required_courses_by_semester if required_courses_by_semester else {}
        )

    def _get_passed_courses(self, student: StudentRecord) -> Dict[str, CourseAttempt]:
        """Returns the best passing attempt for each course where marks and attendance meet thresholds."""
        passed: Dict[str, CourseAttempt] = {}
        for att in student.attempts:
            course = self.curriculum.get(att.course_code)
            if not course:
                continue
            meets_marks = att.marks_obtained >= course.min_pass_marks
            meets_attendance = (
                att.attendance_pct >= course.min_attendance_pct
                and att.attendance_pct >= student.overall_min_attendance_pct
            )
            if meets_marks and meets_attendance:
                if att.course_code not in passed or att.marks_obtained > passed[att.course_code].marks_obtained:
                    passed[att.course_code] = att
        return passed

    def _calculate_cgpa(self, student: StudentRecord) -> float:
        """Calculates credit-weighted CGPA across all attempted courses (using latest/best attempt per course)."""
        latest_by_course: Dict[str, CourseAttempt] = {}
        for att in student.attempts:
            if att.course_code not in latest_by_course or att.semester >= latest_by_course[att.course_code].semester:
                latest_by_course[att.course_code] = att

        total_credits = 0
        weighted_points = 0.0
        for code, att in latest_by_course.items():
            course = self.curriculum.get(code)
            if course:
                total_credits += course.credits
                weighted_points += att.grade_points * course.credits

        return round(weighted_points / total_credits, 2) if total_credits > 0 else 0.0

    def audit_student(self, student: StudentRecord) -> Dict[str, object]:
        """Runs a full progression audit for a student and returns eligibility and outstanding items."""
        passed_courses = self._get_passed_courses(student)
        passed_codes: Set[str] = set(passed_courses.keys())
        cgpa = self._calculate_cgpa(student)

        subject_evaluations: List[Dict[str, object]] = []
        failed_or_ineligible_courses: List[str] = []
        outstanding_requirements: List[str] = []

        # 1. Evaluate all recorded attempts (marks, attendance, and prerequisites)
        for att in student.attempts:
            course = self.curriculum.get(att.course_code)
            if not course:
                outstanding_requirements.append(f"Unknown course code '{att.course_code}' in semester {att.semester}.")
                continue

            missing_prereqs = [p for p in course.prerequisites if p not in passed_codes]
            marks_ok = att.marks_obtained >= course.min_pass_marks
            course_att_ok = att.attendance_pct >= course.min_attendance_pct
            overall_att_ok = att.attendance_pct >= student.overall_min_attendance_pct
            attendance_ok = course_att_ok and overall_att_ok
            prereqs_ok = len(missing_prereqs) == 0

            passed = marks_ok and attendance_ok and prereqs_ok
            reasons: List[str] = []

            if not marks_ok:
                reasons.append(f"Marks {att.marks_obtained} < required {course.min_pass_marks}")
            if not course_att_ok:
                reasons.append(f"Course attendance {att.attendance_pct}% < {course.min_attendance_pct}%")
            if not overall_att_ok:
                reasons.append(f"Attendance {att.attendance_pct}% < student min {student.overall_min_attendance_pct}%")
            if not prereqs_ok:
                reasons.append(f"Missing prerequisites: {', '.join(missing_prereqs)}")

            subject_evaluations.append({
                "semester": att.semester,
                "course_code": course.code,
                "course_name": course.name,
                "marks": att.marks_obtained,
                "attendance_pct": att.attendance_pct,
                "passed": passed,
                "issues": reasons,
            })

            if not passed and course.code not in passed_codes:
                failed_or_ineligible_courses.append(course.code)
                detail = "; ".join(reasons) if reasons else "Requirement not met"
                outstanding_requirements.append(
                    f"[Sem {att.semester}] {course.code} ({course.name}): {detail}"
                )

        # Deduplicate failed/backlog courses
        unique_backlogs = sorted(set(failed_or_ineligible_courses))

        # 2. Check required curriculum courses up to current semester
        for sem, req_codes in sorted(self.required_courses_by_semester.items()):
            if sem <= student.current_semester:
                for code in req_codes:
                    course = self.curriculum.get(code)
                    label = f"{code} ({course.name})" if course else code
                    if code not in passed_codes:
                        req_msg = f"Uncompleted required course from Sem {sem}: {label}"
                        if req_msg not in outstanding_requirements:
                            outstanding_requirements.append(req_msg)
                        if course:
                            for prereq in course.prerequisites:
                                if prereq not in passed_codes:
                                    prereq_msg = f"Prerequisite '{prereq}' not passed for {code}"
                                    if prereq_msg not in outstanding_requirements:
                                        outstanding_requirements.append(prereq_msg)

        # 3. Check CGPA & backlog limits for progression
        cgpa_ok = cgpa >= student.min_cgpa_for_progression
        backlog_limit_ok = len(unique_backlogs) <= student.max_allowed_backlogs

        if not cgpa_ok:
            outstanding_requirements.append(
                f"CGPA {cgpa:.2f} is below minimum required {student.min_cgpa_for_progression:.2f}"
            )
        if not backlog_limit_ok:
            outstanding_requirements.append(
                f"Backlog count ({len(unique_backlogs)}) exceeds maximum allowed ({student.max_allowed_backlogs})"
            )

        eligible = cgpa_ok and backlog_limit_ok and len(unique_backlogs) == 0

        return {
            "student_id": student.student_id,
            "name": student.name,
            "current_semester": student.current_semester,
            "cgpa": cgpa,
            "passed_courses": sorted(passed_codes),
            "backlog_courses": unique_backlogs,
            "eligible_for_next_semester": eligible,
            "subject_evaluations": subject_evaluations,
            "outstanding_requirements": outstanding_requirements,
        }

    def print_audit_report(self, student: StudentRecord) -> None:
        """Prints a formatted academic progression audit report."""
        result = self.audit_student(student)
        status_label = "ELIGIBLE FOR PROGRESSION" if result["eligible_for_next_semester"] else "NOT ELIGIBLE / HOLD"

        print("=" * 72)
        print(f"ACADEMIC PROGRESSION AUDIT — {result['name']} ({result['student_id']})")
        print("=" * 72)
        print(f"Current Semester : {result['current_semester']}")
        print(f"Calculated CGPA  : {result['cgpa']:.2f} (Min Required: {student.min_cgpa_for_progression:.2f})")
        print(f"Passed Courses   : {', '.join(result['passed_courses']) or 'None'}")
        print(f"Backlog Courses  : {', '.join(result['backlog_courses']) or 'None'}")
        print(f"Progression Status: {status_label}")

        print("\n[Subject-Wise Evaluation]")
        for item in result["subject_evaluations"]:
            verdict = "PASS" if item["passed"] else "FAIL"
            line = (
                f"  Sem {item['semester']} | {item['course_code']} ({item['course_name']}): "
                f"Marks={item['marks']}, Att={item['attendance_pct']}% -> {verdict}"
            )
            print(line)
            for issue in item["issues"]:
                print(f"      * {issue}")

        print(f"\n[Outstanding Requirements ({len(result['outstanding_requirements'])})]")
        if not result["outstanding_requirements"]:
            print("  None — All progression requirements satisfied.")
        else:
            for idx, req in enumerate(result["outstanding_requirements"], 1):
                print(f"  {idx}. {req}")
        print("=" * 72 + "\n")


# ==========================================
# EXAMPLE EXECUTION
# ==========================================
if __name__ == "__main__":
    courses = [
        Course("CS101", "Programming Fundamentals", credits=4, min_pass_marks=40.0, min_attendance_pct=75.0),
        Course("MA102", "Discrete Mathematics", credits=4, min_pass_marks=40.0, min_attendance_pct=75.0),
        Course("CS201", "Data Structures", credits=4, min_pass_marks=45.0, min_attendance_pct=75.0, prerequisites=["CS101"]),
        Course("CS202", "Computer Organization", credits=3, min_pass_marks=40.0, min_attendance_pct=80.0, prerequisites=["MA102"]),
    ]

    required_by_sem = {
        1: ["CS101", "MA102"],
        2: ["CS201", "CS202"],
    }

    auditor = AcademicProgressionAuditor(courses, required_by_sem)

    # Student 1: Meets marks and attendance, eligible to progress
    s1 = StudentRecord(
        student_id="STU-001",
        name="Aarav Sharma",
        current_semester=2,
        attempts=[
            CourseAttempt("CS101", semester=1, marks_obtained=78.0, attendance_pct=88.0, grade_points=8.0),
            CourseAttempt("MA102", semester=1, marks_obtained=72.0, attendance_pct=82.0, grade_points=7.5),
            CourseAttempt("CS201", semester=2, marks_obtained=81.0, attendance_pct=90.0, grade_points=8.5),
            CourseAttempt("CS202", semester=2, marks_obtained=76.0, attendance_pct=85.0, grade_points=8.0),
        ],
    )

    # Student 2: Low attendance on CS202, failed marks on CS201, missing prerequisite check
    s2 = StudentRecord(
        student_id="STU-002",
        name="Meera Nair",
        current_semester=2,
        attempts=[
            CourseAttempt("CS101", semester=1, marks_obtained=65.0, attendance_pct=84.0, grade_points=7.0),
            CourseAttempt("MA102", semester=1, marks_obtained=35.0, attendance_pct=80.0, grade_points=0.0),  # Failed marks
            CourseAttempt("CS201", semester=2, marks_obtained=42.0, attendance_pct=78.0, grade_points=5.0),  # Below 45 pass mark
            CourseAttempt("CS202", semester=2, marks_obtained=74.0, attendance_pct=72.0, grade_points=7.5),  # Below 80% course att & 75% overall
        ],
    )

    auditor.print_audit_report(s1)
    auditor.print_audit_report(s2)