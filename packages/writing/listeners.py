import os
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import User, Profile, Post
from django.db import IntegrityError
from django.core.exceptions import ValidationError


# creating Profile instance when a user created
@receiver(post_save, sender=User)
def save_profile(sender, **kwargs):
    try:
        profile = Profile.objects.create(user=kwargs['instance'])
        print("Profile has been created. User Id: {}".format(profile.user.id))
    except IntegrityError as err:
        print("Unexpected err when saving profile: {}".format(err))
    except ValidationError as err:
        print("Profile can't save for validation error: {}".format(err))


# removing file on post delete
@receiver(post_delete, sender=Post)
def delete_img(sender, **kwargs):
    post = kwargs['instance']
    try:
        img_path = post.feature_img.path
        print("IMG: {}".format(img_path))
        if os.path.exists(img_path):
            os.remove(img_path)
            parent_dir = os.path.abspath(os.path.join(img_path, os.pardir))
            if len(os.listdir(parent_dir)) == 0:
                # removing directory if empty
                os.rmdir(parent_dir)
        else:
            print("The file ({}) does not exist".format(img_path))
    except ValueError:
        # if no feat img attached, ignore it
        return None
