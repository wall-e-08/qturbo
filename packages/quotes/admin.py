from __future__ import print_function, unicode_literals

from django.contrib import admin

from .models import (StmEnroll, Dependent, #EverestStm, PremierStm, HealtheflexStm, HealthemedStm, SageStm,
                                #PrincipleAdvantage, UnifiedHealthOne, Lead,
                                AddonPlan, Carrier)


class DependentInline(admin.StackedInline):
    model = Dependent
    extra = 0


# class PrincipleAdvantageInline(admin.StackedInline):
#     model = PrincipleAdvantage
#     extra = 0
#
#
# class SageStmInline(admin.StackedInline):
#     model = SageStm
#     extra = 0
#
#
# class HealthemedStmInline(admin.StackedInline):
#     model = HealthemedStm
#     extra = 0
#
#
# class HealtheflexStmInline(admin.StackedInline):
#     model = HealtheflexStm
    extra = 0
#
#
# class EverestStmInline(admin.StackedInline):
#     model = EverestStm
#     extra = 0
#
#
# class PremierStmInline(admin.StackedInline):
#     model = PremierStm
#     extra = 0


class AddonPlanInline(admin.StackedInline):
    model = AddonPlan
    extra = 0


@admin.register(StmEnroll)
class StmEnrollAdmin(admin.ModelAdmin):
    inlines = [DependentInline,
               #PrincipleAdvantageInline, SageStmInline,
               AddonPlanInline]
    list_display = ['applicant_name', 'stm_name', 'created', 'enrolled']


# admin.site.register(EverestStm)
#
# admin.site.register(HealtheflexStm)
#
# admin.site.register(HealthemedStm)
#
# admin.site.register(PremierStm)

# admin.site.register(UnifiedHealthOne)


# @admin.register(Lead)
# class LeadAdmin(admin.ModelAdmin):
#     list_display = ['Email', 'Phone', 'State', 'created']


@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_id', 'ins_type', 'is_active', 'created_at']
