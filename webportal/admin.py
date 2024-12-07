from django.contrib import admin

from webportal.models import MaterialCategory, Material, User

admin.site.register(User)
admin.site.register(MaterialCategory)
admin.site.register(Material)
