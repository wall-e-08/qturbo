"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 2.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os, dj_database_url

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from typing import Dict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ru1$(0ptd!dc^g8t=qk%$*)y6%af+jw-1&&9jgdyk(kwd*h$&&'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", False)

ALLOWED_HOSTS = ['*']

IS_DEV = False


# Application definition

INSTALLED_APPS = [
    'about',
    'quotes',
    'writing',
    'distinct_pages',
    'que_ans',
    'dashboard',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    'djrichtextfield',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

CUSTOM_TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [CUSTOM_TEMPLATE_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',

                'quotes.context_processors.hp_context',
                'quotes.context_processors.menu_context',
                'quotes.context_processors.general_topic_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(default=DATABASE_URL)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('PG_DB', 'postgres'),
            'USER': os.environ.get('PG_USER', 'postgres'),
            'PASSWORD': os.environ.get('PG_PASSWORD', 'postgres'),
            'HOST': os.environ.get('PG_HOST', '127.0.0.1'),
            'PORT': 5432,
        }
    }


###################
# CELERY SETTINGS #
###################

CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

CELERY_TASK_ROUTES = {
    'quotes.tasks.StmPlanTask': {'queue': 'stm'},
    'quotes.tasks.LimPlanTask': {'queue': 'lim'},
    'quotes.tasks.AncPlanTask': {'queue': 'anc'},
    'quotes.tasks.EsignCheckBeat': {'queue': 'esign_check'},
    'quotes.tasks.EsignCheckWorker': {'queue': 'esign_check'},

}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "global_static_libs"),
    os.path.join(BASE_DIR, "app_static"),
]

STATIC_ROOT = os.path.join(BASE_DIR, "static")

# media folder
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# login
LOGIN_URL = '/login'
LOGOUT_URL = '/logout'
LOGIN_REDIRECT_URL = '/dashboard/'


# django rich text field configurations
DJRICHTEXTFIELD_CONFIG = {
    'js': ['//tinymce.cachefly.net/4.1/tinymce.min.js'],
    'init_template': 'djrichtextfield/init/tinymce.js',
    'settings': {
        'menubar': False,
        'plugins': 'link image',
        'toolbar': 'bold italic | link image | removeformat',
        'width': 700
    }
}

# post (blog & article) configs
BLOG_SENIOR_CATEGORY_SLUG = 'medicare'
BLOG_FOR_ALL_CATEGORY_SLUG = 'health-insurance'

LOGGING = {
    'version': 1,

    'disable_existing_loggers': False,

    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },

    'formatters': {
        'simple': {
            'format': ('%(asctime)s - %(name)s - '
                       '%(levelname)s - %(message)s'),
        },
        'file': {
            'format': '%(name)s::%(asctime)s - %(levelname)s: %(message)s',
        },
        'sysfmt': {
            'format': '%(hostname)s %(name)s - %(levelname)s: %(message)s',
        },
    },


    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level': ('DEBUG' if DEBUG else 'WARNING'),
            'class': 'logging.FileHandler',
            'filename': '/tmp/quote_turbo.log',
            'formatter': 'file',
        },
        'syslog': {
          'level': 'DEBUG',
          'class': 'logging.handlers.SysLogHandler',
          'formatter': 'sysfmt',
          'address': ('localhost', 514)
        }
    },

    'loggers': {
        'django': {
            'handlers': ['console', 'mail_admins'],
            'level': 'INFO',
        },
        'py.warnings': {
            'handlers': ['console'],
        },
        'main': {
            'handlers': ['file'],
            'level': ('INFO' if DEBUG else 'WARNING'),
            'propagate': True,
        },
        'quote_turbo': {
            'handlers': ['syslog', 'console'],
            'level': ('INFO' if DEBUG else 'WARNING'),
            'propagate': True,
        },
    }
}


SALES_ADMIN = [
    # 'tutul.barua@eagentdirect.com',
    'ahsanhabibme@gmail.com'
]


# ------------------------+
# Server webservice urls |
# ------------------------+

# Live Server
QUOTE_ENROLL_URL = os.environ.get('QUOTE_ENROLL_URL', 'https://test1.hiiquote.com/webservice/process.php')
QUOTE_REQUEST_URL = os.environ.get('QUOTE_REQUEST_URL', 'https://test1.hiiquote.com/webservice/quote_service.php')
ESIGNATURE_VERIFICATION_URL = os.environ.get('ESIGNATURE_VERIFICATION_URL', 'https://test1.hiiquote.com/webservice/esign_payment.php')
QUOTE_REQUEST_USER_ID = os.environ.get('QUOTE_REQUEST_USER_ID', 'A157FF340027874696242C')  # CLH1251100 - $125 - live


# -----------------+
#  Celery Settings |
# -----------------+
CELERY_TASK_LOCK_EXPIRE = 2 * 60    # 2 min
CELERY_ESIGN_CHECK_TIME = 5 * 60    # 5 min
CELERY_NEXT_ESIGN_CHECK_TIME = 30 * 60    # 30 min


# ----------------------+
# E-Signature Variables |
# ----------------------+

ESIGN_SIGNATURE_COMPLETED_TXT = "Signature is Completed"

ESIGNATURE_VERIFICATION = 'Y'
ESIGN_SEND_METHOD = 'Email'  # 'Text'


# -----------------+
#   PLAN LIST      +
# -----------------+

# MAIN PLAN LIST

MAIN_PLANS = (
    # ('54', 'Principle Advantage'),
    # ('90', 'Unified Health One')
    # ('97', 'Select STM'),
    # ('104', 'Sage STM'),
    ('Freedom Spirit Plus', 'Freedom Spirit Plus'),
    ('Safeguard Critical Illness', 'Safeguard Critical Illness'),
    ('Foundation Dental', 'Foundation Dental'),
    ('USA Dental', 'USA Dental'),
    ('Everest STM', 'Everest STM'),
    ('LifeShield STM', 'LifeShield STM'),
    ('AdvantHealth STM', 'AdvantHealth STM'),
    ('Cardinal Choice', 'Cardinal Choice'),
    ('Health Choice', 'Health Choice'),
    ('Vitala Care', 'Vitala Care'),
    ('Legion Limited Medical', 'Legion Limited Medical'),
)


TYPEWISE_PLAN_LIST = {
    'stm': ['Everest STM', 'LifeShield STM', 'AdvantHealth STM'],
    'lim': ['Principle Advantage', 'Cardinal Choice', 'Vitala Care', 'Health Choice', 'Legion Limited Medical'],
    'anc': ['USA Dental', 'Freedom Spirit Plus', 'Safeguard Critical Illness', 'Foundation Dental']
}

# ---------------------+
#    Dashboard CMS     +
# ---------------------+

SHORTCODE_PREFIX = '{{'
SHORTCODE_POSTFIX = '}}'

PAGE_ITEM_MODEL_TEMPLATE = {
    'ItemList': 'distinct_pages/items/list.html',
    'ItemIcon': 'distinct_pages/items/icon.html',
    'ItemTwoColumn': 'distinct_pages/items/two_column.html',
    'ItemGuide': 'distinct_pages/items/guide.html',
}

# ------------------------------------+
#    State specific plan duration     +
# ------------------------------------+

# All these things will go to Database
STATE_SPECIFIC_PLAN_DURATION = {
    'LifeShield STM': {
        'AL': ['12*1', '12*3'],
        'AZ': ['6*2'],
        'CO': ['6*2'],
        'DE': ['12*1', '12*3'],
        'FL': ['12*1', '12*3'],
        'GA': ['12*1', '12*3'],
        'IL': ['12*1', '12*3'],
        'LA': ['6*6'],
        'MN': ['6*2'],
        'MS': ['12*1', '12*3'],
        'MO': ['6*6'],
        'NC': ['12*1', '12*3'],
        # 'OH': ['12*1', '12*3'], # Currently unavailable
        'OK': ['6*6'],
        'PA': ['12*1', '12*3'],
        'SD': ['6*6'],
        'TN': ['12*1', '12*3'],
        'TX': ['12*1', '12*3'],
        'VA': ['12*1', '12*3'],
        'WV': ['12*1', '6*1'],
    },
    'AdvantHealth STM': {
        'AL': ['6*1','6*6'],
        'AZ': ['6*1','6*2', '6*6'],
        "AR": ['6*1','6*6'],
        "KY": ['6*1','6*6'],
        'MS': ['6*1','6*6'],
        "NE": ['6*1','6*6'],
        "NV": ['6*1','6*6'],
        'OK': ['6*1','6*6'],
        'TX': ['6*1','6*6'],
        'VA': ['6*1','6*6'],
        "WI": ['6*1','6*6'],
    }
}

# TODO: CREATE SEPARATE DEFAULTS FOR SEPARATE STATES
STATE_SPECIFIC_PLAN_DURATION_DEFAULT = {
    'LifeShield STM': ['12*1'],
    'AdvantHealth STM': ['6*6']
}

# -----------------------------------+
# Carrier specific plan attributes   +
# -----------------------------------+

# TODO: Quote request should use these values OR initial quote should be fully hardcoded
CARRIER_SPECIFIC_PLAN_BENEFIT_AMOUNT = {
    'LifeShield STM': ['0', '2000', '3000', '4000', '5000'],
    'AdvantHealth STM': ['2000', '4000']
}

CARRIER_SPECIFIC_PLAN_COINSURACE_PERCENTAGE_FOR_QUOTE = {
    'LifeShield STM': ['80/20', '50/50', '70/30', '100/0'],
    'AdvantHealth STM': ['80/20']
}


CARRIER_SPECIFIC_PLAN_COINSURACE_PERCENTAGE_FOR_VIEW = {
    'LifeShield STM': ['0', '20', '30', '50'],
    'AdvantHealth STM': ['20']
}

CARRIER_SPECIFIC_PLAN_COVERAGE_MAX = {
    'AdvantHealth STM': ['250000', '500000', '1000000'],
    'LifeShield STM': ['250000', '750000', '1000000', '1500000']
}

# --------------+
#    Income     +
# --------------+

CARRIER_SPECIFIC_INCOME_VS_POLICY_MAXIMUM = {
    'LifeShield STM': {
        'low': '250000',
        'medium': '750000',
        'high': '1000000'
    },

    'AdvantHealth STM': {
        'low': '250000',
        'medium': '500000',
        'high': '1000000'
    }
}

# -----------------+
# User Preference  +
# -----------------+

USER_INITIAL_PREFERENCE_DATA = {
    # The general_url_chosen flag will be true when user goes into stm_plan page.
    # It will be again set false when the user gets back to quote list page.
    'LifeShield STM': {
        'Duration_Coverage': ['12*1'],
        'Coverage_Max': [''],
        'Coinsurance_Percentage': ['0', '20'],
        'Benefit_Amount': ['0', '2000']
    },

    'AdvantHealth STM': {
        'Duration_Coverage': ['6*6'],
        'Coverage_Max': [''],
        'Coinsurance_Percentage': ['20'],
        'Benefit_Amount': ['2000']
    }
}

# -----------------------+
#   Homepage Properties  +
# -----------------------+

USER_PROPERTIES: Dict[str, int] = {
    'min_age': 18,
    'max_age': 99,

    'dependents_min_age': 6,
    'dependents_max_age': 25,

}

# ----------------------------+
#  Featured Plan Properties   +
#-----------------------------+




FEATURED_PLAN_DICT = {
    'LifeShield STM': {
        'option': '5000',
        'Coinsurance_Percentage': '20',
        'Benefit_Amount': '3000',
    },

    'AdvantHealth STM': {
        'option': '2500',
        'Coinsurance_Percentage': '20',
        'Benefit_Amount': '2000',
    },

    'Health Choice':{
        'Plan_Name': 'Plan_100'
    },

    'Vitala Care':{
        'Plan_Name': 'Plan_100'
    },

    'Legion Limited Medical': {
        'Plan_Name': 'Plan_3'
    },

    'USA Dental': {
        'Plan_Name': 'Access_III'
    },

    'Safeguard Critical Illness': {
        'Plan_Name': 'Option5000',
    },

    'Freedom Spirit Plus':{
        'Plan_Name': 'SPIRITPLUS_100000',
    }
}

FEATURED_PLAN_PREMIUM_DICT = {
    'stm': 100.0,
    'lim': 100.0,
    'anc': 25.0
}


# ------------------#
#    Payment        #
# ------------------#

TEST_CARD_ALLOWED = True



try:
    from .local_settings import *
except ImportError:
    pass
