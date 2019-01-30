from django import forms
from distinct_pages.models import Page, ItemList, ItemIcon, ItemTwoColumn, ItemGuide
from writing.models import Article, Blog
from djrichtextfield.widgets import RichTextWidget
from .utils import get_distinct_page_template_file_list, get_all_urls
from .models import Menu, GeneralTopic


class GeneralTopicForm(forms.ModelForm):
    class Meta:
        model = GeneralTopic
        fields = ['top_quote_heading', 'top_quote_sub_heading', 'top_text']


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
    # TODO: need to make url drop-down from pages
    content = forms.CharField(
        widget=RichTextWidget(),
        required=False,
    )

    url = forms.ChoiceField(
        choices=get_all_urls
    )

    def __init__(self, *args, **kwargs):
        super(ItemListForm, self).__init__(*args, **kwargs)
        self.fields['icon'].empty_label = None

    class Meta:
        model = ItemList
        fields = '__all__'


class ItemIconForm(forms.ModelForm):
    # TODO: need svg format validation
    class Meta:
        model = ItemIcon
        fields = '__all__'


class ItemTwoColumnForm(forms.ModelForm):
    content = forms.CharField(widget=RichTextWidget())

    url = forms.ChoiceField(
        choices=get_all_urls
    )

    class Meta:
        model = ItemTwoColumn
        fields = '__all__'


class ItemGuideForm(forms.ModelForm):
    url = forms.ChoiceField(
        choices=get_all_urls
    )

    class Meta:
        model = ItemGuide
        exclude = '__all__'


class MenuForm(forms.ModelForm):
    parent_menu = forms.ModelChoiceField(
        queryset=Menu.objects.all(),
        empty_label=None,
        required=False,
    )

    url = forms.ChoiceField(
        choices=get_all_urls
    )

    position = forms.ChoiceField(
        choices=(
            ('top', 'Header'),
            ('btm', 'Footer'),
        ),
    )

    class Meta:
        model = Menu
        exclude = '__all__'

