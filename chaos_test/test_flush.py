import pytest
from chaos import ChaosOpt
from milvus import IndexType, MetricType
from utils import *
import time, threading
import logging
import pdb

nb = 200000
dim = 128
index_file_size = 1024
vectors = gen_vectors(nb, dim)


# @pytest.fixture(scope="class")
# def connect(request):
#     host = '192.168.1.238'
#     port = 19530
#     try:
#         milvus = Milvus(host=host, port=port, try_connect=False)
#     except Exception as e:
#         logging.getLogger().error(str(e))
#         pytest.exit("Milvus server can not connected, exit pytest ...")
#     def fin():
#         try:
#             milvus.close()
#             pass
#         except Exception as e:
#             logging.getLogger().info(str(e))
#     request.addfinalizer(fin)
#     return milvus


class TestFlushBase:
    """
    ******************************************************************
      The following cases are used to test `flush` function
    ******************************************************************
    """

    @pytest.fixture(scope='function')
    def setup_function(self, request, connect):
        vectors = gen_vectors(nb, dim)
        collection = gen_unique_str()
        logging.getLogger().info(collection)
        param = {'collection_name': collection,
                 'dimension': dim,
                 'index_file_size': index_file_size,
                 'metric_type': MetricType.L2}
        disable_flush(connect)
        status = connect.create_collection(param)
        assert status.OK()
        ids = [i for i in range(nb)]
        for i in range(4):
            status, ids = connect.insert(collection, vectors, ids)
            logging.getLogger().info(status)
            assert status.OK()

        def teardown_function():
            for name in connect.list_collections()[1]:
                connect.drop_collection(name)

        # request.addfinalizer(teardown_function)
        return collection, len(ids)

    def _test_flush_kill_pod(self, connect, setup_function):
        """
        exist problem,
        :param connect:
        :param setup_function:
        :return:
        """
        chaosOpt = ChaosOpt(metadata_name="milvus-pod-kill", kind='PodChaos')
        action = "pod-kill"
        app_dict = {"app": "zong3-milvus-mysql"}
        cron = "@every 1s"
        collection, ids = setup_function
        future = connect.flush([collection], _async=True)
        chaosOpt.create_chaos_object(action, app_dict, cron=cron)
        try:
            status = future.result()
            logging.getLogger().info(status)
            status, count = connect.count_entities(collection)
            logging.getLogger().info(count)
            # assert not status.OK()
        except Exception as e:
            logging.getLogger().error(str(e))
            assert True
        finally:
            chaosOpt.delete_chaos_object()

    def test_flush_network_partition(self, connect, setup_function):
        chaosOpt = ChaosOpt(metadata_name="milvus-mysql-partition", kind='NetworkChaos')
        if len(chaosOpt.list_chaos_object()["items"]) != 0:
            chaosOpt.delete_chaos_object()
        spec_params = {
            "action": "partition",
            "direction": "to",
            "target": {
                "selector": {{"namespaces": ["milvus"]}, {"labelSelectors": {"app": "zong3-milvus-mysql"}},
                             {"mode": "one"}}
            },
            "duration": "10m",
            "scheduler": {
                "cron": "@every 12m"
            }
        }
        collection, ids = setup_function
        chaosOpt.create_chaos_object(spec_params)
        future = connect.flush([collection], _async=True)
        try:
            status = future.result()
            logging.getLogger().info(status)
            assert not status.OK()
        except Exception as e:
            logging.getLogger().error(str(e))
            assert True
        finally:
            chaosOpt.delete_chaos_object()
            chaosOpt.list_chaos_object()
            status, count = connect.count_entities(collection)
            logging.getLogger().info(count)
