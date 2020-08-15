import pytest
from utils import *
import logging
from chaos import ChaosOpt
from milvus import Milvus, IndexType
import datetime
import time

nb = 200000
nq = 500
dim = 128
index_file_size = 1024
vectors = gen_vectors(nb, dim)
top_k = 200
index_type = IndexType.IVFLAT
index_param = {"nlist": 1024}
search_param = {"nprobe": 128}


@pytest.fixture(scope="class")
def connect(request):
    host = '192.168.1.238'
    port = 19530
    try:
        milvus = Milvus(host=host, port=port)
    except Exception as e:
        logging.getLogger().error(str(e))
        pytest.exit("Milvus server can not connected, exit pytest ...")

    def fin():
        try:
            milvus.close()
            pass
        except Exception as e:
            logging.getLogger().info(str(e))

    request.addfinalizer(fin)
    return milvus


class TestSearchBase:
    @pytest.fixture(scope='class')
    def setup_function(self, request, connect):
        # collection = gen_unique_str()
        collection = 'test_kh0Hud95'
        logging.getLogger().info(collection)
        param = {'collection_name': collection,
                 'dimension': dim,
                 'index_file_size': index_file_size,
                 'metric_type': MetricType.L2}
        disable_flush(connect)
        status = connect.create_collection(param)
        assert status.OK()
        ids_ = [i for i in range(nb)]
        status, ids = connect.insert(collection, vectors, ids_)
        assert status.OK()

        def teardown_function():
            for name in connect.list_collections()[1]:
                connect.drop_collection(name)

        request.addfinalizer(teardown_function)
        return collection, ids_

    def test_search_burn_cpu(self, connect, setup_function):
        collection, ids = setup_function
        chaosOpt = ChaosOpt(metadata_name='milvus-burn-cpu', kind='StressChaos')
        if len(chaosOpt.list_chaos_object()["items"]) != 0:
            chaosOpt.delete_chaos_object()
        spec_params = {
            "containerName": "milvus",
            "stressors": {
                "cpu": {
                    "workers": 12,
                    "load": 50
                }
            },
            "duration": "10m",
            "scheduler": {
                "cron": "@every 12m"
            }
        }
        # do search before burn-cpu created
        connect.load_collection(collection)
        get_search_avg_time(connect, collection, search_times=2)
        avg_time_before = get_search_avg_time(connect, collection)
        # do search after burn-cpu created
        chaosOpt.create_chaos_object(spec_params=spec_params)
        avg_time_created = get_search_avg_time(connect, collection)

        # do search after burn-cpu deleted
        chaosOpt.delete_chaos_object()
        data = chaosOpt.list_chaos_object()
        avg_time_deleted = get_search_avg_time(connect, collection)

        assert avg_time_before < avg_time_created
        assert avg_time_deleted < avg_time_created

    def test_search_network_partition(self, connect, setup_function):
        chaosOpt = ChaosOpt(metadata_name="milvus-mysql-network-partition", kind='NetworkChaos')
        if len(chaosOpt.list_chaos_object()["items"]) != 0:
            chaosOpt.delete_chaos_object()
        spec_params = {
            "action": "partition",
            "direction": "to",
            "target": {
               "selector": {
                   "namespaces": ["milvus"],
                   "labelSelectors": {"app": "zong3-milvus-mysql"}
               },
                "mode": "one"
               },
            "duration": "10m",
            "scheduler": {
                "cron": "@every 12m"
            }
        }
        collection, ids = setup_function
        chaosOpt.create_chaos_object(spec_params)
        status, result = connect.search(collection, top_k, vectors[:nq], params=search_param, _async=True)
        try:
            logging.getLogger().info(status)
            assert not status.OK()
        except Exception as e:
            logging.getLogger().error(str(e))
            assert True
        finally:
            chaosOpt.delete_chaos_object()
            chaosOpt.list_chaos_object()


def cal_avg_time(times):
    # total_seconds = sum(map(lambda f: int(f[0]) * 3600 + int(f[1]) * 60 + int(f[2]), map(lambda f: f.split(":"),
    # times)))
    total_seconds = sum(map(lambda time: time, times))
    avg_seconds = total_seconds / len(times)
    return str(datetime.timedelta(seconds=avg_seconds))


def get_search_avg_time(connect, collection, search_times=2):
    times = []
    query_vec = vectors[:nq]
    for i in range(search_times):
        start_time = time.time()
        status, result = connect.search(collection, top_k, query_vec, params=search_param)
        times.append(time.time() - start_time)
        logging.getLogger().info(status)
        assert status.OK()
    avg_time = cal_avg_time(times)
    logging.getLogger().info(avg_time)
    return avg_time