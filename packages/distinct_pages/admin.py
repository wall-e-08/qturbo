from django.contrib import admin
from .models import Page, ItemIcon, ItemList, ItemGuide, ItemTwoColumn

# Register your models here.
admin.site.register(Page)
admin.site.register(ItemList)
admin.site.register(ItemGuide)
admin.site.register(ItemTwoColumn)
admin.site.register(ItemIcon)