from django.contrib import admin
from .models import *
from django.utils.html import format_html

admin.site.register(Category)
admin.site.register(Categorize)
admin.site.register(Profile)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'svg_icon']

    def svg_icon(self, obj):
        return format_html(obj.icon)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_time'

    list_filter = ['post_type', 'status']

    list_display = ['title', 'post_type', 'status', 'user', 'created_time']

    actions = ['make_published', 'make_unpublished', 'make_archived']

    def make_published(self, request, queryset):
        self.row_update_msg(request=request, queryset=queryset, status=STATUS_CHOICES[0][0], desc=STATUS_CHOICES[0][1])

    make_published.short_description = STATUS_CHOICES[0][1]

    def make_unpublished(self, request, queryset):
        self.row_update_msg(request=request, queryset=queryset, status=STATUS_CHOICES[1][0], desc=STATUS_CHOICES[1][1])

    make_unpublished.short_description = STATUS_CHOICES[1][1]

    def make_archived(self, request, queryset):
        self.row_update_msg(request=request, queryset=queryset, status=STATUS_CHOICES[2][0], desc=STATUS_CHOICES[2][1])

    make_archived.short_description = STATUS_CHOICES[2][1]

    def row_update_msg(self, request, queryset, status, desc):
        rows_updated = queryset.update(status=status)
        if rows_updated == 1:
            message_bit = "One post was"
        else:
            message_bit = "{0} posts were".format(rows_updated)
        self.message_user(request, "{0} {1}".format(message_bit, desc))
