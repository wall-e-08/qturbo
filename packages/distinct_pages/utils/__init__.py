import os
import string
import random
import datetime


def get_img_path(instance, filename):
    file_extension = os.path.splitext(filename)[1]
    return os.path.join(
        "pages",
        datetime.datetime.now().strftime("%Y-%m-%d"),
        str("{}-{}".format(instance.title, ''.join(random.choices(string.ascii_letters + string.digits, k=8))) + file_extension)
    )
