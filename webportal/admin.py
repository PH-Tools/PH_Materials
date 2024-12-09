from django.contrib import admin

from webportal.models import Material, MaterialCategory, User

admin.site.register(User)
admin.site.register(MaterialCategory)
admin.site.register(Material)
