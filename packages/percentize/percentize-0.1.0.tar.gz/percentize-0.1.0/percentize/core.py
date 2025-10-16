import math

def sdm(part, whole):
    """Single decimal mode: returns percentage rounded to 1 decimal"""
    return round((part / whole) * 100, 1)

def w(part, whole):
    """Whole mode: returns percentage as an integer"""
    return math.floor((part / whole) * 100)

def um(part, whole):
    """Use math module for exact percentage calculation"""
    return (part / whole) * 100

def main(part, whole):
    """Main: percentize with max 100.XXXXXXXXXX%"""
    percent = (part / whole) * 100
    return min(percent, 100.0)
