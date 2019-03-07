from __future__ import print_function, unicode_literals

from django.contrib import admin
from django.utils.html import format_html
from .models import (StmEnroll, Dependent, AddonPlan, Carrier, BenefitsAndCoverage, RestrictionsAndOmissions, MainPlan)


admin.site.register(RestrictionsAndOmissions)

@admin.register(MainPlan)
class MainPlanAdmin(admin.ModelAdmin):
    list_display = ['vimm_enroll_id', 'Name', 'Plan_Name']
    list_filter = ['Name']


@admin.register(BenefitsAndCoverage)
class BenefitsAndCoverageAdmin(admin.ModelAdmin):
    list_display = ['_title', 'plan', 'plan_number', '_img']
    list_filter = ['plan']

    def _title(self, obj):
        return obj.self_fk.title if obj.self_fk else obj.title
    _title.short_description = 'Title'

    def _img(self, obj):
        return format_html('<img height="20" src="{}">'.format(obj.image.url)) if obj.image else '-'
    _img.short_description = "Image"


class DependentInline(admin.StackedInline):
    model = Dependent
    extra = 0


class AddonPlanInline(admin.StackedInline):
    model = AddonPlan
    extra = 0


@admin.register(StmEnroll)
class StmEnrollAdmin(admin.ModelAdmin):
    inlines = [DependentInline, AddonPlanInline]
    list_display = ['applicant_name', 'stm_name', 'created', 'enrolled']


@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_id', 'ins_type', 'is_active', 'created_at']
