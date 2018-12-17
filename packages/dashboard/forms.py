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


class ArticleForm(forms.ModelForm):
    content = forms.CharField(widget=RichTextWidget())

    class Meta:
        model = Article
        exclude = ['status',]


class BlogForm(forms.ModelForm):
    content = forms.CharField(widget=RichTextWidget())

    class Meta:
        model = Blog
        exclude = ['status',]
