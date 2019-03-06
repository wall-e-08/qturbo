from __future__ import print_function, unicode_literals

import time
import pytz
import json
import queue
import decimal
import datetime
import threading

from quotes.redisqueue import redis_connect
from quotes.quote_response import AddonPlan
from quotes.addon_properties import properties as add_on_properties

from core import settings

json_encoder = json.JSONEncoder()
json_decoder = json.JSONDecoder()


class Worker(threading.Thread):

    def __init__(self, task_queue, result_queue, number):
        super(Worker, self).__init__()
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.number = number

    def run(self):
        while True:
            try:
                task = self.task_queue.get()
                self.process(task)
            finally:
                self.task_queue.task_done()

    def process(self, task):
        task.process_response()
        self.result_queue.put(task, False)


def thread(tasks, n=20):
    task_queue = queue.Queue()
    result_queue = queue.Queue()
    for i in range(n):
        worker = Worker(task_queue, result_queue, i)
        worker.daemon = True
        worker.start()
    for task in tasks:
        task_queue.put(task)
    return result_queue


def addon_plans_from_dict(dict_data):
    plans = []
    for plan in dict_data:
        plans.append(AddonPlan(**plan))
    return set(plans)


def addon_plans_from_json_data(json_data):
    plans = []
    for plan in json_data:
        plans.append(AddonPlan(**json_decoder.decode(plan.decode())))
    return set(plans)


def new_addon_plan_to_add(previous_plans, new_plans):
    new_unique_plans = new_plans.difference(previous_plans)
    json_data = []
    for plan in new_unique_plans:
        if (plan.addon_id in add_on_properties and
                plan.Name in add_on_properties.get(plan.addon_id, {'plan': {}})['plan']):
            json_data.append(json_encoder.encode(plan.data_as_dict()))
    return json_data


# def threaded_request(form_data, session_key, selection_data=None) -> int:
#     """For only stm plans, there will be selection data(sel_dat).
#
#     :param selection_data: Selection data. This data will dictate, which xml requests will
#     be created and then sent. If this is None, the default will be sent. The default
#     has already been selected in quote_request.py according to settings.
#     :type selection_data: dict
#     :param form_data: Quote request form data
#     :param session_key: session key
#     :param alt_cov_flag: alternative coverage flag; If this is set we'll get a different request for stm.
#     :type alt_cov_flag: bool
#     :return: 0
#     """
#     redis = redis_connect()
#     redis_key = "{0}:{1}".format(session_key, form_data['quote_store_key'])
#     print('redis_key: ', redis_key)
#
#     print(f'Creating threaded requests. Quote Request URL is {settings.QUOTE_REQUEST_URL}')
#
#     print(f'Selection data is: {selection_data}.')
#     tasks = get_xml_requests(form_data, selection_data)
#     print('--------------->>tasks: ', len(tasks))
#     # import time
#     # time.sleep(15)
#     results = thread(tasks, n=36)
#     num_of_tasks = len(tasks)
#     # time1 = datetime.datetime.now(tz=pytz.timezone('Asia/Dhaka'))
#     # print(f'==============> Start time is {time1}')
#     addon_plans = []
#     print('num_of_tasks: ', num_of_tasks)
#     while num_of_tasks > 0:
#         r = results.get()
#         res = r.get_formatted_response()
#
#         if res is None:
#             num_of_tasks -= 1
#             continue
#
#         for monthly_plan in res.monthly:
#             monthly_plan_data = monthly_plan.get_data_as_dict()
#             if redis is not None:
#                 if redis.lrange(redis_key, -1, -1)[0].decode() == '"END"':
#                     redis.rpop(redis_key)
#                 redis.rpush(redis_key, *[json_encoder.encode(monthly_plan_data)])
#
#         # addon_plans += res.addon_plans
#         if res.addon_plans and redis_key:
#             addon_plan_redis_key = "{0}:{1}".format(redis_key, r.Name.lower().replace(" ", '-'))
#             new_addon_plans = new_addon_plan_to_add(
#                 addon_plans_from_json_data(redis.lrange(addon_plan_redis_key, 0, -1)),
#                 set(res.addon_plans)
#             )
#             for new_addon_plan in new_addon_plans:
#                 redis.rpush(addon_plan_redis_key, new_addon_plan)
#
#         results.task_done()
#         num_of_tasks -= 1
#         print('remaining num_of_tasks: ', num_of_tasks)
#
#     # time2 = datetime.datetime.now(tz=pytz.timezone('Asia/Dhaka'))
#     # print(f'==============> End time is {time2}')
#     #
#     # print(f'Total time required {(time2-time1).seconds} seconds')
#
#
#     if form_data['Ins_Type'] == 'stm':
#         redis_key_done_data = f'{redis_key}:done_data'
#
#         try:
#             done_data = json.loads(redis.get(redis_key_done_data))
#             for i in selection_data:
#                 for j in done_data[i]:
#                     done_data[i][j].extend(selection_data[i][j])
#
#
#         except KeyError as k:
#             print(f'{k} is in selection_data but not in done_data')
#             pass
#
#         redis.set(redis_key_done_data, json.dumps(done_data))
#
#     if redis is not None and redis.exists(redis_key):
#         redis.rpush(redis_key, *[json_encoder.encode('END')])
#         if len(redis.lrange(redis_key, 0, -1)) <= 2:
#             redis.expire(redis_key, 30)
#         else:
#             now = datetime.datetime.now(tz=pytz.UTC)
#             day_end = datetime.datetime(now.year, now.month, now.day, hour=23,
#                                         minute=59, second=59, microsecond=999999, tzinfo=pytz.UTC)
#             redis.expire(redis_key, int((day_end - now).seconds))
#
#     return 0
