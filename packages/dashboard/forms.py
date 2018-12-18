from django import forms
from distinct_pages.models import Page
from writing.models import Article, Blog
from djrichtextfield.widgets import RichTextWidget
from .utils import get_distinct_page_template_file_list


class PageForm(forms.ModelForm):
    content = forms.CharField(widget=RichTextWidget())  # RichTextWidget(field_settings='basic')
    template_file = forms.ChoiceField(
        choices=get_distinct_page_template_file_list
    )

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
