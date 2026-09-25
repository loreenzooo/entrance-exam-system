import random
import string
from datetime import datetime


def generate_reference_number():
    """
    Produces something like: EXM-2026-4F82K1
    Not guaranteed unique on its own - the astronomically small
    collision chance is acceptable for a school project's scale.
    """
    year = datetime.utcnow().year
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"EXM-{year}-{random_part}"