from django.contrib import admin
from django.contrib.auth.models import Group

from territories_dashboard_lib.website_lib.forms import (
    GlossaryItemAdminForm,
    LandingPageAdminForm,
    MainConfAdminForm,
    StaticPageAdminForm,
)
from territories_dashboard_lib.website_lib.models import (
    GlossaryItem,
    LandingPage,
    MainConf,
    NoticeBanner,
    StaticPage,
)


@admin.register(MainConf)
class MainConfAdmin(admin.ModelAdmin):
    form = MainConfAdminForm


@admin.register(GlossaryItem)
class GlossaryItemAdmin(admin.ModelAdmin):
    form = GlossaryItemAdminForm


@admin.register(LandingPage)
class LandingPageAdminForm(admin.ModelAdmin):
    form = LandingPageAdminForm


@admin.register(StaticPage)
class StaticPageAdminForm(admin.ModelAdmin):
    form = StaticPageAdminForm


@admin.register(NoticeBanner)
class NoticeBannerAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at")


admin.site.unregister(Group)
