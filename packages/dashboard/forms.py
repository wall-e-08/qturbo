from django import forms
from distinct_pages.models import Page, ItemList
from writing.models import Article, Blog
from djrichtextfield.widgets import RichTextWidget
from .utils import get_distinct_page_template_file_list


class EditorMediaForm(forms.Form):
    media_file = forms.FileField()


class PageForm(forms.ModelForm):
    content = forms.CharField(widget=RichTextWidget())  # RichTextWidget(field_settings='basic')
    template_file = forms.ChoiceField(
        choices=get_distinct_page_template_file_list
    )

    # content.widget.field_settings = {'your': 'custom', 'settings': True}
    class Meta:
        model = Page
        exclude = ['status', ]


class ArticleForm(forms.ModelForm):
    content = forms.CharField(widget=RichTextWidget())

    class Meta:
        model = Article
        exclude = ['status', ]


class BlogForm(forms.ModelForm):
    content = forms.CharField(widget=RichTextWidget())

    class Meta:
        model = Blog
        exclude = ['status', ]


class ItemListForm(forms.ModelForm):
    content = forms.CharField(
        widget=RichTextWidget(),
        required=False,
    )

    class Meta:
        model = ItemList
        fields = '__all__'


