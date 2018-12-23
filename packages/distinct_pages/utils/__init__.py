import os
import datetime


def get_img_path(instance, filename):
    file_extension = os.path.splitext(filename)[1]
    return os.path.join(
        "pages",
        datetime.datetime.now().strftime("%Y-%m-%d"),
        str("{}-{}".format(instance.title, instance.id) + file_extension)
    )