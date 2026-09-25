from datetime import datetime


def refresh_batch_status(batch):
    """
    Recalculates a batch's status based on the current time and how many
    applicants have ACTUALLY CONFIRMED attendance (not just picked this
    batch and possibly abandoned the flow before verifying).

    Why attendances, not applicants: an applicant is linked to a batch
    the moment they select it, even if they never finish face
    verification. Counting that against capacity would let someone
    "take a slot" just by picking a batch and walking away.

    Logic:
    - If the current time is past end_time      -> closed
    - If the current time is within the window   -> ongoing
    - If confirmed attendance == capacity        -> full
    - Otherwise (still in the future, has room)  -> open
    """
    now = datetime.utcnow()
    confirmed_count = len(batch.attendances)

    if now > batch.end_time:
        batch.status = 'closed'
    elif now >= batch.start_time:
        batch.status = 'ongoing'
    elif confirmed_count >= batch.capacity:
        batch.status = 'full'
    else:
        batch.status = 'open'


def is_batch_editable(batch):
    """
    An admin cannot edit or delete a batch that is currently ongoing,
    or one that already has CONFIRMED attendees. Applicants who merely
    selected the batch but never completed verification don't count -
    they haven't actually used a slot yet.
    """
    return batch.status != 'ongoing' and len(batch.attendances) == 0