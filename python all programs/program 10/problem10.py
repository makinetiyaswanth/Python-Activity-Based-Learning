from typing import Dict, List, Tuple

# Type aliases for clarity using lists and tuples
# Schedule tuple: (event_id, sport, venue, day, start_hour, end_hour, team_a, team_b)
EventSchedule = Tuple[str, str, str, str, int, int, str, str]

# Score tuple: (event_id, team_name, points_earned, score_diff)
ScoreRecord = Tuple[str, str, int, int]


def detect_scheduling_conflicts(schedules: List[EventSchedule]) -> List[Tuple[str, str, str]]:
    """
    Identifies overlapping matches on the same day where either:
      1. The same venue is double-booked, OR
      2. A team is scheduled to play in two matches simultaneously.
    Returns a list of conflict tuples: (event_id_1, event_id_2, reason)
    """
    conflicts: List[Tuple[str, str, str]] = []
    n = len(schedules)

    for i in range(n):
        id1, sport1, venue1, day1, start1, end1, t1_a, t1_b = schedules[i]
        for j in range(i + 1, n):
            id2, sport2, venue2, day2, start2, end2, t2_a, t2_b = schedules[j]

            # Check if on the same day and time intervals overlap: max(start) < min(end)
            if day1 == day2 and max(start1, start2) < min(end1, end2):
                if venue1 == venue2:
                    conflicts.append((
                        id1,
                        id2,
                        f"Venue conflict at '{venue1}' on {day1} ({start1}:00-{end1}:00 vs {start2}:00-{end2}:00)",
                    ))

                overlapping_teams = {t1_a, t1_b}.intersection({t2_a, t2_b})
                for team in sorted(overlapping_teams):
                    conflicts.append((
                        id1,
                        id2,
                        f"Team conflict for '{team}' on {day1} ({sport1} vs {sport2})",
                    ))

    return conflicts


def aggregate_and_rank(
    schedules: List[EventSchedule],
    scores: List[ScoreRecord],
    conflict_event_ids: List[str],
) -> List[Tuple[int, str, int, int, int]]:
    """
    Aggregates valid match scores per team (excluding conflicted/voided matches),
    sorts teams by total points (descending) then score differential (descending),
    and returns ranked tuples: (rank, team_name, matches_played, total_points, total_diff)
    """
    valid_event_ids = {ev[0] for ev in schedules if ev[0] not in conflict_event_ids}

    # Initialize stats for all participating teams from the schedule
    # Stats stored temporarily as [matches_played, total_points, total_diff]
    team_stats: Dict[str, List[int]] = {}
    for ev in schedules:
        for team in (ev[6], ev[7]):
            if team not in team_stats:
                team_stats[team] = [0, 0, 0]

    # Aggregate scores from non-conflicted matches
    for event_id, team, pts, diff in scores:
        if event_id not in valid_event_ids:
            continue
        if team not in team_stats:
            team_stats[team] = [0, 0, 0]
        team_stats[team][0] += 1      # matches_played
        team_stats[team][1] += pts    # total_points
        team_stats[team][2] += diff   # total_diff

    # Convert to list of tuples and sort by (-total_points, -total_diff, team_name)
    unsorted_standings: List[Tuple[str, int, int, int]] = [
        (team, stats[0], stats[1], stats[2]) for team, stats in team_stats.items()
    ]
    sorted_standings = sorted(
        unsorted_standings,
        key=lambda item: (-item[2], -item[3], item[0]),
    )

    # Assign final ranks (handling ties cleanly)
    rankings: List[Tuple[int, str, int, int, int]] = []
    current_rank = 1
    for idx, (team, played, pts, diff) in enumerate(sorted_standings):
        if idx > 0:
            prev_pts, prev_diff = sorted_standings[idx - 1][2], sorted_standings[idx - 1][3]
            if (pts, diff) != (prev_pts, prev_diff):
                current_rank = idx + 1
        rankings.append((current_rank, team, played, pts, diff))

    return rankings


def generate_tournament_report(
    schedules: List[EventSchedule],
    scores: List[ScoreRecord],
) -> None:
    """Runs conflict detection, aggregates points, and prints the tournament report."""
    conflicts = detect_scheduling_conflicts(schedules)
    conflicted_ids = sorted({c[0] for c in conflicts}.union({c[1] for c in conflicts}))
    rankings = aggregate_and_rank(schedules, scores, conflicted_ids)

    print("=" * 74)
    print("MULTI-EVENT SPORTS SCHEDULING & SCORING REPORT")
    print("=" * 74)

    print("\n[1] EVENT SCHEDULE")
    print(f"  {'ID':<8} {'Sport':<12} {'Venue':<14} {'Day':<10} {'Time':<12} {'Matchup'}")
    print("  " + "-" * 70)
    for ev_id, sport, venue, day, start, end, t_a, t_b in schedules:
        time_slot = f"{start:02d}:00-{end:02d}:00"
        print(f"  {ev_id:<8} {sport:<12} {venue:<14} {day:<10} {time_slot:<12} {t_a} vs {t_b}")

    print(f"\n[2] SCHEDULING CONFLICTS DETECTED ({len(conflicts)})")
    if not conflicts:
        print("  None — Schedule is conflict-free.")
    else:
        for idx, (id1, id2, reason) in enumerate(conflicts, 1):
            print(f"  {idx}. [{id1} <-> {id2}] {reason}")
        print(f"  * Voided/Excluded Event IDs from Scoring: {', '.join(conflicted_ids)}")

    print("\n[3] FINAL TEAM RANKINGS")
    print(f"  {'Rank':<6} {'Team':<18} {'Played':<8} {'Points':<8} {'Score Diff'}")
    print("  " + "-" * 54)
    for rank, team, played, pts, diff in rankings:
        print(f"  {rank:<6} {team:<18} {played:<8} {pts:<8} {diff:+d}")
    print("=" * 74)


# ==========================================
# EXAMPLE EXECUTION
# ==========================================
if __name__ == "__main__":
    # List of EventSchedule tuples:
    # (event_id, sport, venue, day, start_hour, end_hour, team_a, team_b)
    event_schedules: List[EventSchedule] = [
        ("EVT-01", "Basketball", "Indoor Arena", "Day 1", 9, 11, "Titans", "Falcons"),
        ("EVT-02", "Volleyball", "Court B", "Day 1", 9, 11, "Wolves", "Panthers"),
        ("EVT-03", "Badminton", "Indoor Arena", "Day 1", 10, 12, "Wolves", "Hawks"),      # Venue & Team conflict with EVT-01/EVT-02
        ("EVT-04", "Football", "Main Ground", "Day 1", 14, 16, "Titans", "Wolves"),
        ("EVT-05", "Basketball", "Indoor Arena", "Day 2", 10, 12, "Falcons", "Panthers"),
        ("EVT-06", "Football", "Main Ground", "Day 2", 14, 16, "Hawks", "Titans"),
    ]

    # List of ScoreRecord tuples:
    # (event_id, team_name, points_earned, score_diff)
    match_scores: List[ScoreRecord] = [
        ("EVT-01", "Titans", 3, +14),
        ("EVT-01", "Falcons", 0, -14),
        ("EVT-02", "Wolves", 3, +8),
        ("EVT-02", "Panthers", 0, -8),
        ("EVT-03", "Wolves", 3, +5),     # Excluded due to scheduling conflict
        ("EVT-03", "Hawks", 0, -5),      # Excluded due to scheduling conflict
        ("EVT-04", "Titans", 1, 0),
        ("EVT-04", "Wolves", 1, 0),
        ("EVT-05", "Panthers", 3, +11),
        ("EVT-05", "Falcons", 0, -11),
        ("EVT-06", "Titans", 3, +2),
        ("EVT-06", "Hawks", 0, -2),
    ]

    generate_tournament_report(event_schedules, match_scores)