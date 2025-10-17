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

if train_configs.num_devices % 2 != 0:
    raise ValueError("Expected an even number of devices.")

host = Host(cpu_clock=2.25)

server_resource = Resource(
    name="server",
    cpu_cores=14,
    cpu_clock=2.0,
    memory=2048,
    network=NetworkResource(bw=1000),
    host=host,
)

pi3_0_resource = Resource(
    name="pi3_0",
    cpu_cores=4,
    cpu_clock=1.2,
    memory=1024,
    network=NetworkResource(bw=100),
    host=host,
)

pi3_1_resource = Resource(
    name="pi3_1",
    cpu_cores=4,
    cpu_clock=1.2,
    memory=1024,
    network=NetworkResource(bw=100),
    host=host,
)

cloud_resource = ClusterResource(
    name="cloud", type=ClusterResourceType.CLOUD, resources=[server_resource]
)

edge_0_resource = ClusterResource(
    name="edge_0",
    type=ClusterResourceType.EDGE,
    resources=(train_configs.num_devices // 2) * [pi3_0_resource],
)

edge_1_resource = ClusterResource(
    name="edge_1",
    type=ClusterResourceType.EDGE,
    resources=(train_configs.num_devices // 2) * [pi3_1_resource],
)

exp = NetflExperiment(
    name="exp-2.1.4",
    task=task,
    resources=[cloud_resource, edge_0_resource, edge_1_resource],
    hugging_face_token=os.getenv("HUGGINGFACE_TOKEN"),
)

cloud = exp.create_cluster(cloud_resource)
edge_0 = exp.create_cluster(edge_0_resource)
edge_1 = exp.create_cluster(edge_1_resource)

server = exp.create_server(server_resource)
edge_0_devices = exp.create_devices(pi3_0_resource, edge_0_resource.num_resources)
edge_1_devices = exp.create_devices(pi3_1_resource, edge_1_resource.num_resources)

exp.add_to_cluster(server, cloud)
for device in edge_0_devices:
    exp.add_to_cluster(device, edge_0)
for device in edge_1_devices:
    exp.add_to_cluster(device, edge_1)

worker = exp.add_worker("127.0.0.1")
worker.add(cloud)
worker.add(edge_0)
worker.add(edge_1)
worker.add_link(cloud, edge_0)
worker.add_link(cloud, edge_1)

try:
    exp.start()
except Exception as ex:
    print(ex)
finally:
    exp.stop()
