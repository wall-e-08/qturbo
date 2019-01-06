import re
from django.apps import apps
from django.conf import settings

SHORT_CODE_FORMAT = "{prefix} {obj_str} id={ids} {others} {postfix}"


class Encoder:
    def __init__(self, model_name, id_list, **kwargs):
        """
        :param model_name: model name from distinct_pages app
        :param id_list: list of id of the model
        :param kwargs: other kwargs (will be updated later) 
        """
        self.id_list = id_list
        self.kwargs = kwargs
        # for k, v in kwargs.items():
        #     setattr(self, k, v)

        self.model = is_model_exists(model_name)
        self.model_name = self.model.__name__

    def generate(self):
        """
        :return: sample return: "[% Page id=1,2,4,5 GG=wp n1=ok %]"
        """
        id_list2 = self.id_list.copy()
        for _id in id_list2:
            if not self.model.objects.filter(id=_id).exists():
                self.id_list.remove(_id)
        id_str = ",".join(map(str, self.id_list))
        return SHORT_CODE_FORMAT.format(
            prefix=settings.SHORTCODE_PREFIX,
            obj_str=self.model_name,
            ids=id_str,
            others=' '.join("{}={}".format(x[0], x[1]) for x in self.kwargs.items()),
            postfix=settings.SHORTCODE_POSTFIX,
        )


class Decoder:
    def __init__(self, short_code):
        self.short_code = short_code
        self.items = re.search('^{prefix} (.*) {postfix}'.format(
            prefix=settings.SHORTCODE_PREFIX.replace('[','\[').replace('{', '\{').replace('(', '\('),
            postfix=settings.SHORTCODE_POSTFIX.replace(']','\]').replace('}', '\}').replace(')', '\)')
        ), self.short_code).group(1).split()
        self.model = is_model_exists(self.items[0])
        self.model_name = self.model.__name__

    def decode(self):
        kwargs_dict = {}
        for item in self.items[1:]:
            key = re.search('^(.*?)=', item).group(1)
            val = re.search('=(.*?)$', item).group(1)
            if key == 'id':
                available_id = []
                for v in val.split(','):
                    # check if instance with this id is exists
                    if v:
                        if self.model.objects.filter(id=v).exists():
                            available_id.append(self.model.objects.get(id=v))
                        else:
                            print("DoesNotExists: model: {}, id: {}".format(self.model_name, v))
                val = available_id  # returned existed instances
                key = self.model_name
            kwargs_dict.update({key: val})
        return kwargs_dict


def is_model_exists(model_name):
    model_name = model_name if isinstance(model_name, str) else model_name.__name__
    try:
        return apps.get_model(app_label='distinct_pages', model_name=model_name)
    except LookupError as err:
        print("Model not found. Err: {}".format(err))
    return None
