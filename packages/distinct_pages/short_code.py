import re
from django.apps import apps
from django.conf import settings
from django.template.loader import render_to_string

SHORT_CODE_FORMAT = "{prefix} {obj_str}__{ids} {postfix}"


class Encoder:
    def __init__(self, model_name, id_list, **kwargs):
        """
        :param model_name: model name from distinct_pages app
        :param id_list: list of id of the model
        :param kwargs: other kwargs (will be updated later)
        """
        self.id_list = id_list
        self.model = is_model_exists(model_name)
        self.model_name = self.model.__name__ if self.model else ''

    def generate(self):
        """
        :return: sample return: "{{ ItemIcon__11_12_13_14 }}"
        """
        if not self.model:
            return None
        id_list2 = self.id_list.copy()
        for _id in id_list2:
            if not self.model.objects.filter(id=_id).exists():
                self.id_list.remove(_id)
        id_str = "_".join(map(str, self.id_list))
        return SHORT_CODE_FORMAT.format(
            prefix=settings.SHORTCODE_PREFIX,
            obj_str=self.model_name,
            ids=id_str,
            postfix=settings.SHORTCODE_POSTFIX,
        )


class Decoder:
    def __init__(self, short_code):
        self.short_code = short_code
        self.code = re.search('^{prefix} (.*) {postfix}'.format(
            prefix=settings.SHORTCODE_PREFIX.replace('[', '\[').replace('{', '\{').replace('(', '\('),
            postfix=settings.SHORTCODE_POSTFIX.replace(']', '\]').replace('}', '\}').replace(')', '\)')
        ), self.short_code).group(1)
        self.__instances = []  # private variable
        self.__decoded_items = self.code.split('__')

        self.model = is_model_exists(self.__decoded_items[0])
        self.model_name = self.model.__name__ if self.model else ''
        self.template_file = ''

    def decode(self):
        if not self.model:
            return
        for id in self.__decoded_items[1].split('_'):  # get the ids
            if id:
                if self.model.objects.filter(id=id).exists():
                    self.__instances.append(self.model.objects.get(id=id))
                else:
                    print("DoesNotExists: model: {}, id: {}".format(self.model_name, id))
            # key = re.search('^(.*?)=', item).group(1)
            # val = re.search('=(.*?)$', item).group(1)
            # if key == 'id':
            #     for v in val.split(','):
            #         # check if instance with this id is exists
            #         if v:
            #             if self.model.objects.filter(id=v).exists():
            #                 self.instances.append(self.model.objects.get(id=v))
            #             else:
            #                 print("DoesNotExists: model: {}, id: {}".format(self.model_name, v))
            #     continue
            # self.__args_dict.update({key: val})
        if settings.PAGE_ITEM_MODEL_TEMPLATE.get(self.model_name, ''):
            self.template_file = settings.PAGE_ITEM_MODEL_TEMPLATE[self.model_name]
        else:
            raise Exception("Model is not included in dict")

    # def get_args_dict(self):
    #     self.decode()
    #     return self.__args_dict

    def get_html_as_str(self):
        self.decode()
        # rendered_html = ''
        # for item in self.__instances:
        #     rendered_html += render_to_string(self.template_file, {'item': item})
        return render_to_string(self.template_file, {'items': self.__instances})


def is_model_exists(model_name):
    model_name = model_name if isinstance(model_name, str) else model_name.__name__
    try:
        return apps.get_model(app_label='distinct_pages', model_name=model_name)
    except LookupError as err:
        print("Model not found. Err: {}".format(err))
    return None


def get_short_code_list(_str):
    matches = re.finditer("{} (.*?) {}".format(
        settings.SHORTCODE_PREFIX.replace('[', '\[').replace('{', '\{').replace('(', '\('),
        settings.SHORTCODE_POSTFIX.replace(']', '\]').replace('}', '\}').replace(')', '\)')
    ), _str)
    match_list = []
    for matchNum, match in enumerate(matches, start=1):
        if not _str:
            print("Showing test results. No str is given in parameter.......................")
        # print("Match found: {}".format(match.group()))
        match_list.append(match.group())
    return match_list
