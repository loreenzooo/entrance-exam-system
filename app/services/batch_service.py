from datetime import datetime


def refresh_batch_status(batch):
    """
    Recalculates a batch's status based on the current time and how many
    applicants have picked it. Call this every time before displaying
    batches, so the status shown is always accurate - never manually set
    by an admin.

    Logic:
    - If the current time is past end_time      -> closed
    - If the current time is within the window   -> ongoing
    - If capacity is already reached             -> full
    - Otherwise (still in the future, has room)  -> open
    """
    now = datetime.utcnow()
    applicant_count = len(batch.applicants)

    if now > batch.end_time:
        batch.status = 'closed'
    elif now >= batch.start_time:
        batch.status = 'ongoing'
    elif applicant_count >= batch.capacity:
        batch.status = 'full'
    else:
        batch.status = 'open'


def is_batch_editable(batch):
    """
    Per the project rules: an admin cannot edit or delete a batch that is
    currently ongoing, or one that already has applicants registered to it.
    """
    return batch.status != 'ongoing' and len(batch.applicants) == 0