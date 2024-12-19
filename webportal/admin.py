from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from webportal.models import (
    Material,
    MaterialCategory,
    User,
    Assembly,
    Layer,
    LayerSegment,
    Team,
    Project,
)

admin.site.register(MaterialCategory)
admin.site.register(Material)
admin.site.register(Assembly)
admin.site.register(Layer)
admin.site.register(LayerSegment)
admin.site.register(Project)


class UserAdmin(BaseUserAdmin):
    actions = ["make_paid_user", "make_free_user"]
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "team",
        "is_paid_user",
    )
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("Team and Subscription", {"fields": ("team", "is_paid_user")}),
        ("Team Invitations", {"fields": ("team_invite",)}),
    )

    def make_paid_user(self, request, queryset):
        for user in queryset:
            user.change_user_status(is_paid_user=True)
        self.message_user(request, "Selected users have been marked as paid users.")

    def make_free_user(self, request, queryset):
        for user in queryset:
            user.change_user_status(is_paid_user=False)
        self.message_user(request, "Selected users have been marked as free users.")

    make_paid_user.short_description = "Mark selected users as paid users"
    make_free_user.short_description = "Mark selected users as free users"


admin.site.register(User, UserAdmin)
admin.site.register(Team)
