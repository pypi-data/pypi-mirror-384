from django import forms
from django.forms import Textarea

from territories_dashboard_lib.website_lib.models import (
    GlossaryItem,
    LandingPage,
    MainConf,
    StaticPage,
)


class MainConfAdminForm(forms.ModelForm):
    class Meta:
        model = MainConf
        fields = "__all__"
        widgets = {
            "title": Textarea(attrs={"rows": 1, "cols": 30}),
        }


class GlossaryItemAdminForm(forms.ModelForm):
    class Meta:
        model = GlossaryItem
        fields = "__all__"
        widgets = {
            "word": Textarea(attrs={"rows": 1, "cols": 30}),
        }


class LandingPageAdminForm(forms.ModelForm):
    class Meta:
        model = LandingPage
        fields = "__all__"
        widgets = {
            "title": Textarea(attrs={"rows": 1, "cols": 30}),
            "button_link": Textarea(attrs={"rows": 1, "cols": 30}),
        }


class StaticPageAdminForm(forms.ModelForm):
    class Meta:
        model = StaticPage
        fields = "__all__"
        widgets = {
            "name": Textarea(attrs={"rows": 1, "cols": 30}),
            "url": Textarea(attrs={"rows": 1, "cols": 30}),
        }
