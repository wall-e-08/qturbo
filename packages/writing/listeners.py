from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile
from django.db import IntegrityError
from django.core.exceptions import ValidationError


@receiver(post_save, sender=User)
def save_profile(sender, **kwargs):
    try:
        profile = Profile.objects.create(user=kwargs['instance'])
        print("Profile has been created. User Id: {}".format(profile.user.id))
    except IntegrityError as err:
        print("Unexpected err when saving profile: {}".format(err))
    except ValidationError as err:
        print("Profile can't save for validation error: {}".format(err))

