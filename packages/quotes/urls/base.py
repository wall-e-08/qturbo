from django.urls import path, include, re_path
from quotes import views

app_name = 'quotes'

urlpatterns = [
    path('', views.home, name='home'),
    path('health-insurance/', include('quotes.urls.survey')),
    path('get_plan_quote_data_ajax/', views.get_plan_quote_data_ajax, name='get_plan_quote_data_ajax'),

    re_path('health-insurance/quote(?:/(?P<zip_code>\d{5}))?/$', views.plans, name='plans'), # TODO
    
    re_path('health-insurance/quotes/(?P<ins_type>(stm|lim|anc))/$', views.plan_quote, name='plan_quote'),

    re_path('stm/plan/(?P<plan_url>(Principle_Advantage|Unified_Health_One|Cardinal_Choice)'
        r'-[a-z]{2}-Plan[A-Z0-9_]+-[0-9]+)/$',
        views.stm_plan, name='stm_plan'),

    re_path('stm/plan/(?P<plan_url>(Vitala_Care|Health_Choice|Legion_Limited_Medical)'
        r'-[a-z]{2}-Plan[A-Z0-9_]+(Plus)?-[0-9]+)/$',
        views.stm_plan, name='stm_plan'),

    re_path('stm/plan/(?P<plan_url>(USA_Dental|Foundation_Dental|Safeguard_Critical_Illness|Freedom_Spirit_Plus)'
        r'-[a-z]{2}-[a-zA-Z0-9_]+(Plus)?-[0-9]+)/$',
        views.stm_plan, name='stm_plan'),

    re_path('stm/plan/(?P<plan_url>(Everest_STM|HealtheFlex_STM|LifeShield_STM|Select_STM|'
        r'HealtheMed_STM|Premier_STM|Sage_STM)-[a-z]{2}-\d+-\d+-\d+-\d{1,2}-\d{1,2}(\*\d{1,1})?p?\d?)/$',
        views.stm_plan, name='stm_plan'),

    re_path('stm/apply/(?P<plan_url>(Principle_Advantage|Unified_Health_One|Cardinal_Choice)'
        r'-[a-z]{2}-Plan[A-Z0-9_]+(Plus)?-[0-9]+)/$',
        views.stm_apply, name='stm_apply'),

    re_path('stm/apply/(?P<plan_url>(Vitala_Care|Health_Choice|Legion_Limited_Medical)'
        r'-[a-z]{2}-Plan[A-Z0-9_]+(Plus)?-[0-9]+)/$',
        views.stm_apply, name='stm_apply'),

    re_path('stm/apply/(?P<plan_url>(Everest_STM|HealtheFlex_STM|LifeShield_STM|Select_STM|'
        r'HealtheMed_STM|Premier_STM|Sage_STM)-[a-z]{2}-\d+-\d+-\d+-\d{1,2}-\d{1,2}(\*\d{1,1})?p?\d?)/$',
        views.stm_apply, name='stm_apply'),

    re_path('stm/apply/(?P<plan_url>(USA_Dental|Foundation_Dental|Safeguard_Critical_Illness|Freedom_Spirit_Plus)'
        r'-[a-z]{2}-[a-zA-Z0-9_]+(Plus)?-[0-9]+)/$',
        views.stm_apply, name='stm_apply'),

    re_path('stm/plan/(?P<plan_url>(Principle_Advantage|Unified_Health_One|Cardinal_Choice)'
        r'-[a-z]{2}-Plan[A-Z0-9_]+-[0-9]+)/addon-(?P<action>(include|remove))/$',
        views.stm_plan_addon_action, name='stm_plan_addon_action'),

    re_path('stm/plan/(?P<plan_url>(Vitala_Care|Health_Choice|Legion_Limited_Medical)'
        r'-[a-z]{2}-Plan[A-Z0-9_]+(Plus)?-[0-9]+)/addon-(?P<action>(include|remove))/$',
        views.stm_plan_addon_action, name='stm_plan_addon_action'),

    re_path('stm/plan/(?P<plan_url>(Everest_STM|HealtheFlex_STM|LifeShield_STM|Select_STM|'
        r'HealtheMed_STM|Premier_STM|Sage_STM)-[a-z]{2}-\d+-\d+-\d+-\d{1,2}-\d{1,2}(\*\d{1,1})?p?\d?)/'
        r'addon-(?P<action>(include|remove))/$',
        views.stm_plan_addon_action, name='stm_plan_addon_action'),

    re_path('stm/application/(?P<plan_url>(Principle_Advantage|Unified_Health_One|Cardinal_Choice)'
        r'-[a-z]{2}-Plan[A-Z0-9_]+-[0-9]+)/$',
        views.stm_application, name='stm_application'),

    re_path('stm/application/(?P<plan_url>(Vitala_Care|Health_Choice|Legion_Limited_Medical)'
        r'-[a-z]{2}-Plan[A-Z0-9_]+(Plus)?-[0-9]+)/$',
        views.stm_application, name='stm_application'),

    re_path('stm/application/(?P<plan_url>(Everest_STM|HealtheFlex_STM|LifeShield_STM|Select_STM|'
        r'HealtheMed_STM|Premier_STM|Sage_STM)-[a-z]{2}-\d+-\d+-\d+-\d{1,2}-\d{1,2}(\*\d{1,1})?p?\d?)/$',
        views.stm_application, name='stm_application'),

    re_path('stm/application/(?P<plan_url>(USA_Dental|Foundation_Dental|Safeguard_Critical_Illness|Freedom_Spirit_Plus)'
        r'-[a-z]{2}-[a-zA-Z0-9_]+(Plus)?-[0-9]+)/$',
        views.stm_application, name='stm_application'),

    re_path('stm/enroll/(?P<plan_url>(Principle_Advantage|Unified_Health_One|Cardinal_Choice)'
        r'-[a-z]{2}-Plan[A-Z0-9_]+-[0-9]+-[0-9a-zA-Z]{12})(?:/(?P<stage>[1-5]{1}))?/$',
        views.stm_enroll, name='stm_enroll'),

    re_path(r'stm/enroll/(?P<plan_url>(Vitala_Care|Health_Choice|Legion_Limited_Medical)'
        r'-[a-z]{2}-Plan[A-Z0-9_]+(Plus)?-[0-9]+-[0-9a-zA-Z]{12})(?:/(?P<stage>[1-5]{1}))?/$',
        views.stm_enroll, name='stm_enroll'),

    re_path('stm/enroll/(?P<plan_url>(Everest_STM|HealtheFlex_STM|LifeShield_STM|Select_STM'
        r'HealtheMed_STM|Premier_STM|Sage_STM)-[a-z]{2}-\d+-\d+-\d+-\d{1,2}-\d{1,2}(\*\d{1,1})?p?\d?-[0-9a-zA-Z]{12})'
        r'(?:/(?P<stage>[1-5]{1}))?/$',
        views.stm_enroll, name='stm_enroll'),

    re_path('stm/enroll/(?P<plan_url>(USA_Dental|Foundation_Dental|Safeguard_Critical_Illness|Freedom_Spirit_Plus)'
        r'-[a-z]{2}-[a-zA-Z0-9_]+(Plus)?-[0-9]+-[0-9a-zA-Z]{12})(?:/(?P<stage>[1-5]{1}))?/$',
        views.stm_enroll, name='stm_enroll'),

    re_path('stm/e_signature_enrollment/(?P<vimm_enroll_id>[a-zA-Z0-9]+)/$',
        views.e_signature_enrollment,
        name='e_signature_enrollment'),

    re_path('stm/successfully_enrolled/(?P<vimm_enroll_id>[a-zA-Z0-9]+)/$', views.thank_you, name='thank_you'),

    re_path(r'^pages/legal/(?P<slug>[a-z\-]+)/$', views.legal, name='legal'),

]