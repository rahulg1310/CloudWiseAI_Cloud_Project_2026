def money(value):
    return round(float(value or 0), 2)


def latest_date(cur):
    """Newest date in cost_records (None if the table is empty)."""
    cur.execute("SELECT MAX(date) AS d FROM cost_records")
    return cur.fetchone()["d"]
