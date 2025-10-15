import nested_admin
from django.contrib import admin
from django.db.models import TextField
from django.forms import TextInput
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html

from territories_dashboard_lib.indicators_lib.methodo_pdf import reset_methodo_file
from territories_dashboard_lib.indicators_lib.models import (
    Dimension,
    Filter,
    Indicator,
    SubTheme,
    Theme,
)
from territories_dashboard_lib.indicators_lib.refresh_filters import refresh_filters


class FilterInline(nested_admin.NestedTabularInline):  # type: ignore
    model = Filter
    extra = 0
    formfield_overrides = {TextField: {"widget": TextInput(attrs={"size": "32"})}}


class DimensionInline(nested_admin.NestedTabularInline):  # type: ignore
    model = Dimension
    extra = 0
    inlines = [FilterInline]
    formfield_overrides = {TextField: {"widget": TextInput(attrs={"size": "32"})}}


class IndicatorAdmin(nested_admin.NestedModelAdmin):
    model = Indicator
    inlines = [DimensionInline]
    list_display = [
        "name",
        "title",
        "sub_theme",
        "index_in_theme",
        "is_active",
    ]

    def save_model(self, request, indicator, form, change):
        super().save_model(request, indicator, form, change)
        if "methodo" in form.changed_data:
            reset_methodo_file(indicator)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["refresh_url"] = f"../../{object_id}/refresh_filters/"
        return super().change_view(request, object_id, form_url, extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/refresh_filters/",
                self.admin_site.admin_view(self.refresh_filters_view),
                name="refresh_filters",
            ),
        ]
        return custom_urls + urls

    def refresh_filters_view(self, request, object_id):
        indicator = Indicator.objects.get(pk=object_id)
        try:
            for dimension in indicator.dimensions.all():
                refresh_filters(dimension)
            self.message_user(request, "Les filtres ont été actualisés.")
        except Exception as e:
            print(e)
            self.message_user(
                request,
                f"Erreur lors de l'actualisation des filtres: {str(e)}",
                level="error",
            )

        return redirect("../")


class IndicatorInline(admin.TabularInline):
    model = Indicator
    extra = 0
    fields = ["name", "index_in_theme", "link"]
    readonly_fields = ["link"]
    ordering = ["index_in_theme"]

    def link(self, obj):
        url = reverse("admin:indicators_lib_indicator_change", args=[obj.id])
        return format_html(f'<a href="{url}">Edit</a>')


class SubThemesInline(admin.TabularInline):
    model = SubTheme
    extra = 0
    fields = [
        "name",
        "index_in_theme",
        "indicators_count",
        "is_displayed_on_app",
        "link",
    ]
    ordering = ["index_in_theme"]
    readonly_fields = ["indicators_count", "is_displayed_on_app", "link"]

    def link(self, obj):
        url = reverse("admin:indicators_lib_subtheme_change", args=[obj.id])
        return format_html(f'<a href="{url}">Edit</a>')

    link.short_description = "Link"


class ThemeAdmin(admin.ModelAdmin):
    model = Theme
    inlines = [SubThemesInline]
    list_display = [
        "title",
        "ordering",
        "subthemes_count",
        "indicators_count",
        "is_displayed_on_app",
    ]


class SubThemeAdmin(admin.ModelAdmin):
    model = SubTheme
    inlines = [IndicatorInline]
    list_display = [
        "title",
        "theme",
        "index_in_theme",
        "indicators_count",
        "is_displayed_on_app",
    ]


admin.site.register(Theme, ThemeAdmin)
admin.site.register(SubTheme, SubThemeAdmin)
admin.site.register(Indicator, IndicatorAdmin)
