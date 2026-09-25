"""
Real face recognition logic using the face_recognition library.

These functions work on raw image bytes (decoded from the base64
photo sent by the kiosk's camera capture). Kept independent of Flask
so they can be tested directly with sample images later, if needed.
"""
import base64
import io
import numpy as np
from PIL import Image
import face_recognition


def _decode_image(image_data):
    """
    The kiosk sends the photo as a base64 data URL, like:
    'data:image/jpeg;base64,/9j/4AAQSkZJRg...'
    This strips the header and turns it into a NumPy array
    (the format face_recognition expects).
    """
    header, encoded = image_data.split(',', 1)
    image_bytes = base64.b64decode(encoded)
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    return np.array(image)


def check_face_quality(image_data):
    """
    Checks that exactly one face is visible and detectable.
    Returns: (is_valid: bool, reason: str)
    """
    image_array = _decode_image(image_data)
    face_locations = face_recognition.face_locations(image_array)

    if len(face_locations) == 0:
        return False, "No face detected. Please make sure your face is clearly visible."
    if len(face_locations) > 1:
        return False, "Multiple faces detected. Please make sure only you are in frame."

    return True, "OK"


def encode_face(image_data):
    """
    Converts the photo into a 128-number face encoding.
    Returns: list[float] if a face was found, otherwise None.
    """
    image_array = _decode_image(image_data)
    encodings = face_recognition.face_encodings(image_array)

    if len(encodings) == 0:
        return None

    # face_recognition returns a NumPy array - convert to a plain
    # Python list so it can be stored as JSON in the database.
    return encodings[0].tolist()


def find_duplicate(new_encoding, all_applicants, threshold=0.6):
    """
    Compares new_encoding against every applicant who already has a
    stored face_encoding. Returns the matching Applicant if one is
    found within the threshold, otherwise None.

    threshold: lower = stricter matching. 0.6 is face_recognition's
    own recommended default for "same person."
    """
    new_encoding_array = np.array(new_encoding)

    for applicant in all_applicants:
        if not applicant.face_encoding:
            continue  # this applicant hasn't captured a face yet

        stored_encoding_array = np.array(applicant.face_encoding)
        distance = face_recognition.face_distance([stored_encoding_array], new_encoding_array)[0]

        if distance <= threshold:
            return applicant

    return None


def verify_identity(applicant, live_image_data, threshold=0.6):
    """
    Confirms the live photo matches the applicant's stored encoding.
    Returns: True if it's a match, False otherwise.
    """
    if not applicant.face_encoding:
        return False

    live_encoding = encode_face(live_image_data)
    if live_encoding is None:
        return False

    stored_encoding_array = np.array(applicant.face_encoding)
    live_encoding_array = np.array(live_encoding)

    distance = face_recognition.face_distance([stored_encoding_array], live_encoding_array)[0]
    return distance <= threshold