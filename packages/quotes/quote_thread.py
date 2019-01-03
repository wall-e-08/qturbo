from __future__ import print_function, unicode_literals

import time
import pytz
import json
import queue
import decimal
import datetime
import threading

from quotes.redisqueue import redis_connect
from quotes.quote_request import get_xml_requests
from quotes.quote_response import AddonPlan
from quotes.addon_properties import properties as add_on_properties

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


def threaded_request(data, session_key, alt_cov_flag=False) -> 0:
    """TODO: docstring for threaded_request.

    :param data: Quote request form data
    :param session_key: session key
    :param alt_cov_flag: alternative coverage flag; If this is set we'll get a different request for stm.
    :type alt_cov_flag: bool
    :return: 0
    """
    print("Creating threaded request")
    redis = redis_connect()
    redis_key = "{0}:{1}".format(session_key, data['quote_store_key'])
    print('redis_key: ', redis_key)

    # We have created a flag. We just pass around the flag and
    # Change coverage duration.
    if alt_cov_flag is True:
        tasks = get_xml_requests(data, alt_cov_flag=True)
        print(f'Creating alternative coverage threaded requests')
    else:
        tasks = get_xml_requests(data, alt_cov_flag=False)
        print(f'Creating normal coverage threaded requests')
    print('--------------->>tasks: ', len(tasks))
    # import time
    # time.sleep(15)
    results = thread(tasks, n=36)
    num_of_tasks = len(tasks)
    addon_plans = []
    print('num_of_tasks: ', num_of_tasks)
    while num_of_tasks > 0:
        r = results.get()
        res = r.get_formatted_response()

        if res is None:
            num_of_tasks -= 1
            continue

        for monthly_plan in res.monthly:
            data = monthly_plan.get_data_as_dict()
            if redis is not None:
                redis.rpush(redis_key, *[json_encoder.encode(data)])

        # addon_plans += res.addon_plans
        if res.addon_plans and redis_key:
            addon_plan_redis_key = "{0}:{1}".format(redis_key, r.Name.lower().replace(" ", '-'))
            new_addon_plans = new_addon_plan_to_add(
                addon_plans_from_json_data(redis.lrange(addon_plan_redis_key, 0, -1)),
                set(res.addon_plans)
            )
            for new_addon_plan in new_addon_plans:
                redis.rpush(addon_plan_redis_key, new_addon_plan)

        results.task_done()
        num_of_tasks -= 1
        print('remaining num_of_tasks: ', num_of_tasks)

    if redis is not None and redis.exists(redis_key):
        redis.rpush(redis_key, *[json_encoder.encode('END')])
        if len(redis.lrange(redis_key, 0, -1)) <= 2:
            redis.expire(redis_key, 30)
        else:
            now = datetime.datetime.now(tz=pytz.UTC)
            day_end = datetime.datetime(now.year, now.month, now.day, hour=23,
                                        minute=59, second=59, microsecond=999999, tzinfo=pytz.UTC)
            redis.expire(redis_key, int((day_end - now).seconds))

    return 0
