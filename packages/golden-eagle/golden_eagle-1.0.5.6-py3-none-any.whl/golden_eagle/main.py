import gc
import os
import traceback
from typing import Optional

import cv2
import face_recognition


# face compare to myself_(before and after and evaluation)
def compare_before_after(before, after, evaluation):

    # This is myself before and after picture.
    before_enc = cv2.cvtColor(before, cv2.COLOR_BGR2RGB)
    after_enc = cv2.cvtColor(after, cv2.COLOR_BGR2RGB)

    # A list of 128-dimensional face recognition before encode
    # Which face detection model to use.
    # “hog” is less accurate but faster on CPUs.
    # “cnn” is a more accurate deep-learning model,
    # which is GPU/CUDA accelerated (if available).
    en_loc_before = face_recognition.face_locations(before_enc, model='cnn')[0]
    en_before = face_recognition.face_encodings(before_enc)[0]

    cv2.rectangle(before, (en_loc_before[3], en_loc_before[0]), (en_loc_before[1], en_loc_before[2]), (0, 255, 0), 3)

    # A list of 128-dimensional face recognition after encode
    # The default is “hog”.
    # https://face-recognition.readthedocs.io/en/latest/face_recognition.html
    en_loc_after = face_recognition.face_locations(after_enc, model='cnn')[0]
    en_after = face_recognition.face_encodings(after_enc)[0]

    cv2.rectangle(after, (en_loc_after[3], en_loc_after[0]), (en_loc_after[1], en_loc_after[2]), (0, 255, 0), 3)

    # https://face-recognition.readthedocs.io/en/latest/readme.html
    # You can do that with the --tolerance parameter. The default tolerance
    # [np.True_] | [np.Flase]

    results: Optional[list] = face_recognition.compare_faces([en_before], en_after, tolerance=evaluation)

    # Add exception handling.
    try:
        # A return value of 0.31 or less is expected.
        if results[0]:
            # return code, before and after.
            return *before, *after

        # Values of 0.32 or higher are expected.
        elif not results[0]:
            # Unique exception occurrence.
            raise ValueError("Use a recent photo of your face.")

        # Usually not reached.
        else:
            # Unique exception occurrence.
            raise ValueError("Please check the passcode for your face photo.")

    # TraceBack.
    except Exception:
        # Specify the folder to record the exception log.
        except_folder: Optional[str] = os.path.expanduser('~/golden_eagle/')
        # Specify the file to log exception occurrences.
        except_f: Optional[str] = os.path.expanduser('~/golden_eagle/d.log')

        # Load the dictionary.
        if os.path.isdir(os.path.expanduser(except_folder)):
            # Log writing process.
            with open(os.path.expanduser(except_f), 'a') as log_py:
                traceback.print_exc(file=log_py)

                # throw except.
                raise RuntimeError from None

        # Current directory Not Found.
        else:
            # Unique exception occurrence.
            raise ValueError("None, Please Check the Current directory.")

    # Once Exec.
    finally:
        # GC collection.
        gc.collect()
