from org_analyze.ParserOrg import ParserOrg, OrgHeader, OrgClock
import os
from collections import defaultdict

def time_str_to_hours(time_str):
    parts = time_str.split(":")
    if len(parts) == 2:
        hours = int(parts[0])
        minutes = int(parts[1])
        return hours + minutes / 60.0
    return 0.0

def read_org_clocks(directory, group_top_level=False):
    """Reads all .org files in the given directory and extracts clock entries.
    Returns a list of rows: [date, hours, task]
    """
    rows = []
    for fname in os.listdir(directory):
        if not fname.endswith(".org"):
            continue
        headers = [None, None, None, None]
        header_level = 0
        with ParserOrg(directory + "/" + fname) as p:
            for item in p.parse():
                if isinstance(item, OrgHeader):
                    headers[item.level - 1] = item.name
                    header_level = item.level
                if isinstance(item, OrgClock):
                    task = ": ".join(headers[:header_level])
                    if group_top_level:
                        task = headers[0]
                    rows.append([item.start, time_str_to_hours(item.duration), task])
    return rows

def group_daily_tasks(rows):
    """
    Groups rows by date and returns a list of daily summaries.
    Each summary is a string: "<date>\t<total_hours>\t<task1, task2, ...>"
    """

    # daily = defaultdict(list)
    for date, time, header in rows:
        # Group by date and task, summing times for same task on same day
        task_times = defaultdict(lambda: defaultdict(float))
        for date, time, header in rows:
            task_times[date][header] += time

        daily = defaultdict(list)
        for date, tasks in task_times.items():
            for header, time in tasks.items():
                daily[date].append((time, header))

    daily_summaries = []
    for date in sorted(daily.keys()):
        date_sum = sum(t for t, _ in daily[date])
        tasks = [h for _, h in daily[date]]
        summary = f"{date}\t{date_sum:.2f}\t{', '.join(tasks)}"
        daily_summaries.append(summary)
    return daily_summaries
