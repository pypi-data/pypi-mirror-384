from django import forms
from django.contrib import admin
from django.db import models
from django.utils.safestring import mark_safe

from territories_dashboard_lib.geo_lib.models import GeoElement, GeoFeature


class GeoColumnInLine(admin.TabularInline):
    model = GeoElement
    fields = ["name", "label", "filterable"]
    extra = 0
    formfield_overrides = {
        models.TextField: {"widget": forms.TextInput()},
    }


class GeoFeatureForm(forms.ModelForm):
    svg_file = forms.FileField(required=False, label="Charger un fichier SVG")

    class Meta:
        model = GeoFeature
        fields = [
            "indicator",
            "name",
            "title",
            "unite",
            "geo_type",
            "color",
            "show_on_fr_level",
            "point_icon_svg",
            "svg_file",
        ]

    def clean(self):
        cleaned_data = super().clean()
        svg_file = cleaned_data.get("svg_file")

        if svg_file:
            svg_content = svg_file.read().decode("utf-8")
            cleaned_data["point_icon_svg"] = svg_content

        return cleaned_data


class GeoTableAdmin(admin.ModelAdmin):
    form = GeoFeatureForm
    inlines = [GeoColumnInLine]
    formfield_overrides = {
        models.TextField: {"widget": forms.TextInput()},
    }
    list_display = ["__str__", "indicator"]
    list_filter = ["indicator"]
    readonly_fields = ["svg_preview"]

    def svg_preview(self, obj):
        if obj.point_icon_svg:
            return mark_safe(obj.point_icon_svg)
        return "-"

    svg_preview.short_description = "Prévisualisation du SVG"


admin.site.register(GeoFeature, GeoTableAdmin)
