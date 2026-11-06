"""
Master aggregation of all troubleshooting cases.
"""
from src.cases_part1 import CASES_P1
from src.cases_part2 import CASES_P2
from src.cases_part3 import CASES_P3
from src.cases_part4 import CASES_P4

CASES = CASES_P1 + CASES_P2 + CASES_P3 + CASES_P4

if __name__ == "__main__":
    print(f"Total aggregated cases: {len(CASES)}")