from datetime import datetime

TOTAL_SLOTS = 10

def get_available_slots(occupied_slots):
    return [i for i in range(1, TOTAL_SLOTS + 1) if i not in occupied_slots]

def calculate_fee(entry_time, exit_time):
    fmt = "%Y-%m-%d %H:%M:%S"
    entry = datetime.strptime(entry_time, fmt)
    exit = datetime.strptime(exit_time, fmt)

    duration = (exit - entry).total_seconds() / 3600  # hours
    fee = max(10, duration * 20)  # ₹20/hour, min ₹10

    return round(fee, 2)