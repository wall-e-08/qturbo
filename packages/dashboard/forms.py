from django import forms
from .models import Page
from writing.models import Article, Blog
from djrichtextfield.widgets import RichTextWidget


class PageForm(forms.ModelForm):
    content = forms.CharField(widget=RichTextWidget())  # RichTextWidget(field_settings='basic')

    # content.widget.field_settings = {'your': 'custom', 'settings': True}
    class Meta:
        model = Page
        fields = '__all__'


class BlogForm(forms.ModelForm):
    content = forms.CharField(widget=RichTextWidget())

    class Meta:
        model = Blog
        fields = '__all__'
