from django.contrib import admin
from django.db import models
from django.forms import TextInput

from .models import Dashboard, Filter


class FilterInLine(admin.TabularInline):
    model = Filter
    extra = 0
    formfield_overrides = {
        models.TextField: {"widget": TextInput(attrs={"size": "32"})},
    }


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {"widget": TextInput(attrs={"size": "32"})},
    }
    inlines = [FilterInLine]
    list_display = ["short_name", "order"]
