import datetime

def split_date_range_into_intervals(start_date, end_date, interval_days):
    date_ranges = []

    current_date = start_date
    while current_date <= end_date:
        next_date = current_date + datetime.timedelta(days=interval_days)
        if next_date > end_date:
            next_date = end_date

        date_ranges.append((current_date, next_date))
        current_date = next_date + datetime.timedelta(days=1)

    return date_ranges