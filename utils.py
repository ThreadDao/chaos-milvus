from __future__ import print_function
import os
import pathlib
import yaml
import random
import string
import datetime
import logging
import time
import pprint
import pdb
from milvus import Milvus, IndexType, MetricType, DataType
from sklearn import preprocessing

segment_size = 10
dimension = 128
default_yaml = os.path.join(pathlib.Path().parent.absolute(), "../suites/default_config.yaml")


def create_chaos_config(plural, metadata_name, extra_spec_params, group='chaos-mesh.org', version='v1alpha1', namespace="milvus",
                        file_path=default_yaml):
    """
    modify default_config.yaml to create specific chaos-mesh yaml
    :param plural:
    :param metadata_name:
    :param extra_spec_params: default spec params: action, mode=one, scheduler,selector.
        You should consider this param according to default_config.yaml's spec.
        >>> extra_spec_params = {"action": "pod-kill", "loss":{"loss": "25", "correlation": "25"}}
    :param group:
    :param version:
    :param namespace:
    :param file_path:
    :return:
    """
    # pdb.set_trace()
    logging.getLogger().info(file_path)
    if not os.path.isfile(file_path):
        raise Exception('File: %s not found' % file_path)
    with open(file_path, 'r') as f:
        config_dict = yaml.full_load(f)
        f.close()
    config_dict["apiVersion"] = group + "/" + version
    config_dict["kind"] = plural
    config_dict["metadata"]["name"] = metadata_name
    config_dict["metadata"]["namespace"] = namespace
    config_dict["spec"].update(extra_spec_params)
    print(type(config_dict))
    # with open(file_path, 'w') as f:
    #    f.write(yaml.dump(config_dict))
    #    f.close()
    return config_dict


def gen_unique_str(str_value=None):
    prefix = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
    return "test_" + prefix if str_value is None else str_value + "_" + prefix


def gen_vectors(num, dim):
    return [[random.random() for _ in range(dim)] for _ in range(num)]


def disable_flush(connect):
    status, reply = connect.set_config("storage", "auto_flush_interval", 0)
    assert status.OK()


def get_avg_costs(times):
    # times = ['00:59:00', '01:01:00']
    total_seconds = sum(map(lambda f: int(f[0])*3600+int(f[1])*60+int(f[2]), map(lambda f: f.split(":"), times)))
    avg_seconds = total_seconds/len(times)
    return str(datetime.timedelta(seconds=avg_seconds))



