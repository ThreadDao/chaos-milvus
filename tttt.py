from milvus import Milvus
import time
from utils import *
nb = 100000
dim = 128
index_file_size = 10
if __name__ == '__main__':
    connect = Milvus(host='192.168.1.238', port=19530)
    # vectors = gen_vectors(nb, dim)
    # collection = gen_unique_str()
    # print(collection)
    # param = {'collection_name': collection,
    #          'dimension': dim,
    #          'index_file_size': index_file_size,
    #          'metric_type': MetricType.L2}
    # disable_flush(connect)
    # status = connect.create_collection(param)
    # assert status.OK()
    # ids = [i for i in range(nb)]
    # for i in range(4):
    #     status, ids = connect.insert(collection, vectors, ids)
    #     print(status)
    #     assert status.OK()
    # while(True):
    #     print(connect.count_entities("test_ySWalewK"), time.time())
    #     time.sleep(1)
    for cname in connect.list_collections()[1]:
        print(cname)
        print(connect.count_entities(cname))