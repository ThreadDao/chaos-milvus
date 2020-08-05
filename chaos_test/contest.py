import pytest
import logging
import pathlib
from utils import gen_unique_str
from milvus import Milvus, IndexType, MetricType
from utils import *

index_file_size = 10
timeout = 60
delete_timeout = 60


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

