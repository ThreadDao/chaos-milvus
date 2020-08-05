from __future__ import print_function
import json
import logging
from utils import *
from pprint import pprint
from kubernetes import client, config
from kubernetes.client.rest import ApiException

config.load_kube_config()

api_instance = client.CustomObjectsApi()


class ChaosOpt(object):
    def __init__(self, metadata_name, kind, group='chaos-mesh.org', version='v1alpha1', namespace='milvus'):
        self.group = group
        self.version = version
        self.namespace = namespace
        self.plural = kind.lower()
        self.metadata_name = metadata_name

    def get_metadata_name(self):
        return self.metadata_name

    def create_chaos_object(self, spec_params):
        body = create_chaos_config(self.plural, self.metadata_name, spec_params)
        pprint(body)
        logging.getLogger().info(body)
        pretty = 'true'
        try:
            api_response = api_instance.create_namespaced_custom_object(self.group, self.version, self.namespace,
                                                                        self.plural, body, pretty=pretty)
            print(api_response)
            logging.getLogger().info(api_instance)
        except ApiException as e:
            logging.error("Exception when calling CustomObjectsApi->create_namespaced_custom_object: %s\n" % e)
            raise Exception(str(e))

    def delete_chaos_object(self, metadata_name=None):
        try:
            if metadata_name is None:
                metadata_name = self.metadata_name
            data = api_instance.delete_namespaced_custom_object(self.group, self.version, self.namespace, self.plural, metadata_name)
            pprint(data)
            logging.getLogger().info(data)
        except ApiException as e:
            logging.error("Exception when calling CustomObjectsApi->create_namespaced_custom_object: %s\n" % e)
            raise Exception(str(e))

    def list_chaos_object(self):
        try:
            data = api_instance.list_namespaced_custom_object(self.group, self.version, self.namespace, plural=self.plural)
            pprint(data)
            logging.getLogger().info(data)
        except ApiException as e:
            logging.error("Exception when calling CustomObjectsApi->create_namespaced_custom_object: %s\n" % e)
            raise Exception(str(e))
        return data


if __name__ == '__main__':
    # chaos = ChaosOpt(metadata_name='stress-memory', kind="StressChaos")
    # chaos = ChaosOpt(metadata_name='milvus-pod-kill', kind="PodChaos")
    # spec_params = {
    #         "action": "pod-kill",
    #         "mode": "one",
    #         "selector": {
    #             "namespaces": ["milvus"],
    #             "labelSelectors": {
    #                 "app.kubernetes.io/instance": "zong3-milvus"
    #             }
    #         },
    #         "scheduler": {
    #             "cron": "@every 20s"
    #         }
    #     }
    spec_params = {
        "mode": "one",
        "selector": {
            "labelSelectors": {
                "app.kubernetes.io/instance": "zong3-milvus"
            }
        },
        "stressors": {
            "memory": {
                "workers": 10,
                "size": "100%"
            }
        },
        "duration": "1m",
        "scheduler": {
            "cron": "@every 2m"
        }
    }
    # chaos.create_chaos_object(spec_params=spec_params)
    # chaos.list_chaos_object()
    # chaos.delete_chaos_object(metadata_name="stress-memory")
    # data = chaos.list_chaos_object()
    file_path = os.path.join(pathlib.Path().absolute(), "suites/default_config.yaml")
    print(file_path)