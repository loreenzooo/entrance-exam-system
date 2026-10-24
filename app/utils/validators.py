"""Validation helpers shared by the kiosk forms."""
import re

# 09XXXXXXXXX - the 11-digit mobile format the entrance forms ask for.
_CONTACT_RE = re.compile(r'^09\d{9}$')

# Deliberately permissive: this only has to reject obvious typos, not
# implement RFC 5322. The browser also validates type="email".
_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]{2,}$')


def is_valid_contact_number(value):
    """True for an 11-digit number that starts with 09."""
    return bool(value) and bool(_CONTACT_RE.match(value.strip()))


def is_valid_email(value):
    """True for something that looks like name@example.com."""
    return bool(value) and bool(_EMAIL_RE.match(value.strip()))
