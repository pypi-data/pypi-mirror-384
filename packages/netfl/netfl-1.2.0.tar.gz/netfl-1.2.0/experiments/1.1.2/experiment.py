import os

from netfl.core.experiment import NetflExperiment
from netfl.utils.resources import (
    Host,
    NetworkResource,
    Resource,
    ClusterResource,
    ClusterResourceType,
)

from task import MainTask


task = MainTask()
train_configs = task.train_configs()

host = Host(cpu_clock=2.25)

server_resource = Resource(
    name="server",
    cpu_cores=14,
    cpu_clock=2.0,
    memory=2048,
    network=NetworkResource(bw=1000),
    host=host,
)

pi4_resource = Resource(
    name="pi4",
    cpu_cores=4,
    cpu_clock=1.5,
    memory=4096,
    network=NetworkResource(bw=1000),
    host=host,
)

cloud_resource = ClusterResource(
    name="cloud", type=ClusterResourceType.CLOUD, resources=[server_resource]
)

edge_resource = ClusterResource(
    name="edge",
    type=ClusterResourceType.EDGE,
    resources=train_configs.num_devices * [pi4_resource],
)

exp = NetflExperiment(
    name="exp-1.1.2",
    task=task,
    resources=[cloud_resource, edge_resource],
    hugging_face_token=os.getenv("HUGGINGFACE_TOKEN"),
)

cloud = exp.create_cluster(cloud_resource)
edge = exp.create_cluster(edge_resource)

server = exp.create_server(server_resource)
devices = exp.create_devices(pi4_resource, edge_resource.num_resources)

exp.add_to_cluster(server, cloud)
for device in devices:
    exp.add_to_cluster(device, edge)

worker = exp.add_worker("127.0.0.1")
worker.add(cloud)
worker.add(edge)
worker.add_link(cloud, edge)

try:
    exp.start()
except Exception as ex:
    print(ex)
finally:
    exp.stop()
