from django.urls import path, include, re_path
from quotes import views
from quotes.views import sitemap

app_name = 'quotes'

import quotes.sitemap

'''
top_pages are homepage(priority 1.0), plans(priority 0.7)
'''

sitemaps = {
    'top_pages': quotes.sitemap.Sitemap,
}


urlpatterns = [
    path('', views.home, name='home'),
    path('health-insurance/', include('quotes.urls.survey')),
    path('get_plan_quote_data_ajax/', views.get_plan_quote_data_ajax, name='get_plan_quote_data_ajax'),

    re_path('health-insurance/quote(?:/(?P<zip_code>\d{5}))?/$', views.plans, name='plans'),  # TODO zip code from url

    re_path('health-insurance/quotes/(?P<ins_type>(stm|lim|anc))/$', views.plan_quote, name='plan_quote'),

    path('health-insurance/validate_quote_form/', views.validate_quote_form, name='validate_quote_form'),

    path('health-insurance/set_ins_type/', views.set_ins_type_and_start_celery, name='set_ins_type'),

    path('health-insurance/redirect_to_plans/', views.set_annual_income_and_redirect_to_plans, name='redirect_to_plans'),

    path('li-demo/', views.life_insurance, name='life_insurance'),

    path('ins-avail-state/', views.check_ins_availability_in_state, name='check_ins_availability_in_state'),

    re_path(r'^sitemap\.xml/$', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

    re_path(r'^robots\.txt/$', views.robots, name='robots'),

    re_path(r'^pages/legal/(?P<slug>[a-z\-]+)/$', views.legal, name='legal'),

    # Limited Plans

    re_path('stm/plan/(?P<plan_url>(Principle_Advantage|Unified_Health_One|Cardinal_Choice)'
            r'-[a-z]{2}-Plan[A-Z0-9_]+-[0-9]+)/$',
            views.stm_plan, name='stm_plan'),

    re_path('stm/plan/(?P<plan_url>(Vitala_Care|Health_Choice|Legion_Limited_Medical)'
            r'-[a-z]{2}-Plan[A-Z0-9_]+(Plus)?-[0-9]+)/$',
            views.stm_plan, name='stm_plan'),

    re_path('stm/plan/(?P<plan_url>(USA_Dental|Foundation_Dental|Safeguard_Critical_Illness|Freedom_Spirit_Plus)'
            r'-[a-z]{2}-[a-zA-Z0-9_]+(Plus)?-[0-9]+)/$',
            views.stm_plan, name='stm_plan'),

    re_path('stm/plan/(?P<plan_url>(Everest_STM|HealtheFlex_STM|LifeShield_STM|AdvantHealth_STM|Select_STM|'
            r'HealtheMed_STM|Premier_STM|Sage_STM)-[a-z]{2}-\d+-\d{1,2}(\*\d{1,1})?p?\d?)/$',
            views.stm_plan, name='stm_plan'),


    re_path('stm/alternate_duration_coverage/(?P<plan_url>(Everest_STM|HealtheFlex_STM|LifeShield_STM|AdvantHealth_STM|Select_STM|'
            r'HealtheMed_STM|Premier_STM|Sage_STM)-[a-z]{2}-\d+-\d+-\d+-\d{1,2}-\d{1,2}'
            r'(\*\d{1,1})?p?\d?)/$',
            views.alternate_duration_coverage, name='alternate_duration_coverage'),

    re_path('stm/select_from_quoted_plans_ajax/(?P<plan_url>(Everest_STM|HealtheFlex_STM|LifeShield_STM|AdvantHealth_STM|Select_STM|'
            r'HealtheMed_STM|Premier_STM|Sage_STM)-[a-z]{2}-\d+-\d+-\d+-\d{1,2}-\d{1,2}'
            r'(\*\d{1,1})?p?\d?)/$',
            views.select_from_quoted_plans_ajax, name='select_from_quoted_plans_ajax'),

    re_path('stm/apply/(?P<plan_url>(Principle_Advantage|Unified_Health_One|Cardinal_Choice)'
            r'-[a-z]{2}-Plan[A-Z0-9_]+(Plus)?-[0-9]+)/$',
            views.stm_apply, name='stm_apply'),

    re_path('stm/apply/(?P<plan_url>(Vitala_Care|Health_Choice|Legion_Limited_Medical)'
            r'-[a-z]{2}-Plan[A-Z0-9_]+(Plus)?-[0-9]+)/$',
            views.stm_apply, name='stm_apply'),

    re_path('stm/apply/(?P<plan_url>(Everest_STM|HealtheFlex_STM|LifeShield_STM|AdvantHealth_STM|Select_STM|'
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

    re_path('stm/plan/(?P<plan_url>(Everest_STM|HealtheFlex_STM|LifeShield_STM|AdvantHealth_STM|Select_STM|'
            r'HealtheMed_STM|Premier_STM|Sage_STM)-[a-z]{2}-\d+-\d+-\d+-\d{1,2}-\d{1,2}(\*\d{1,1})?p?\d?)/'
            r'addon-(?P<action>(include|remove))/$',
            views.stm_plan_addon_action, name='stm_plan_addon_action'),

    re_path('stm/application/(?P<plan_url>(Principle_Advantage|Unified_Health_One|Cardinal_Choice)'
            r'-[a-z]{2}-Plan[A-Z0-9_]+-[0-9]+)/$',
            views.stm_application, name='stm_application'),

    re_path('stm/application/(?P<plan_url>(Vitala_Care|Health_Choice|Legion_Limited_Medical)'
            r'-[a-z]{2}-Plan[A-Z0-9_]+(Plus)?-[0-9]+)/$',
            views.stm_application, name='stm_application'),

    re_path('stm/application/(?P<plan_url>(Everest_STM|HealtheFlex_STM|LifeShield_STM|AdvantHealth_STM|Select_STM|'
            r'HealtheMed_STM|Premier_STM|Sage_STM)-[a-z]{2}-\d+-\d+-\d+-\d{1,2}-\d{1,2}(\*\d{1,1})?p?\d?)/$',
            views.stm_application, name='stm_application'),

    re_path('stm/application/(?P<plan_url>(USA_Dental|Foundation_Dental|Safeguard_Critical_Illness|Freedom_Spirit_Plus)'
            r'-[a-z]{2}-[a-zA-Z0-9_]+(Plus)?-[0-9]+)/$',
            views.stm_application, name='stm_application'),

    re_path('stm/enroll/(?P<vimm_enroll_id>[0-9a-zA-Z]{20})(?:/(?P<stage>[1-5]{1}))?/$',
            views.stm_enroll, name='stm_enroll'),

    re_path('stm/e_signature_enrollment/(?P<vimm_enroll_id>[a-zA-Z0-9]+)/$',
            views.e_signature_enrollment,
            name='e_signature_enrollment'),

    re_path('stm/e_sign_verification_payment/(?P<vimm_enroll_id>[a-zA-Z0-9]+)/$',
            views.esign_verification_payment,
            name='esign_verification_payment'),

    re_path('stm/successfully_enrolled/(?P<vimm_enroll_id>[a-zA-Z0-9]+)/$', views.thank_you, name='thank_you'),


]