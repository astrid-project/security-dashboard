import yaml
import json
import uuid

from more_itertools import collapse, unique_everseen

def generate_visjs_graph(service_file):
    # service_dict = yaml.safe_load_all(service_file)

    # services = []
    # for service in service_dict: 
    #   services.append(service)

    services = service_file

    nodes = []
    edges = []
    all_edges = []

    nodes.append({"id": "public", "label": "public", "group": "public"})

    for service in services:    
      if 'version' in service.keys(): 
          #print("Docker Compose")
          for compose_service in service["services"]:
            nodes.append({"id": compose_service, "label": compose_service,
                          "group": "docker"})
            all_edges.append({"from": "public", "to": compose_service,
                              "id": "public-to-" + compose_service})
      elif 'apiVersion' in service.keys(): 
          #print("Kubernetes")
          if service["kind"] == "Service":
            name = "{}-service".format(service["metadata"]["name"])
            try:
              labels = service["metadata"]["labels"]
            except:
              labels = {}
            selector = service["spec"]["selector"]
            nodes.append({"id": name, "label": name, "group": "k8_svc",
                          "labels": labels, "selector": selector,
                          "kind": "Service"})
            all_edges.append({"from": "public", "to": name,
                              "id": "public-to-" + name})
            edges.append({"from": "public", "to": name,
                          "id": "public-to-" + name})
          if service["kind"] == "StatefulSet":
            name = "{}-statefulset".format(service["metadata"]["name"])
            try:
              labels = service["metadata"]["labels"]
            except:
              labels = {}
            selector = service["spec"]["selector"]
            nodes.append({"id": name, "label": name, "group": "k8_sts",
                          "labels": labels, "selector": selector,
                          "kind": "StatefulSet"})

            labels = service["spec"]["template"]["metadata"]["labels"]
            containers = service["spec"]["template"]["spec"]["containers"]
            for container in containers:
              container_name = container["name"]
              container_id = str(uuid.uuid4())
              nodes.append({"id": container_id, "label": container_name,
                            "group": "k8_pod",
                            "labels": labels, "selector": selector,
                            "kind": "Pod"})
              edges.append({"from": name ,"to": container_id})

          if service["kind"] == "Deployment":
            name = "{}-deployment".format(service["metadata"]["name"])
            try:
              labels = service["metadata"]["labels"]
            except:
              labels = {}
            selector = service["spec"]["selector"]
            nodes.append({"id": name, "label": name, "group": "k8_dep",
                          "labels": labels, "selector": selector,
                          "kind": "Deployment"})

            labels = service["spec"]["template"]["metadata"]["labels"]
            containers = service["spec"]["template"]["spec"]["containers"]
            for container in containers:
              container_name = container["name"]
              container_id = str(uuid.uuid4())
              nodes.append({"id": container_id, "label": container_name,
                            "group": "k8_pod",
                            "labels": labels, "selector": selector,
                            "kind": "Pod"})
              edges.append({"from": name ,"to": container_id})
      else: 
          print("unknowm")

    for nodeA in nodes:
      for nodeB in nodes:
        if nodeA["id"] == nodeB["id"]:
          continue
        if "-service" in nodeA["id"]:
          if "-deployment" in nodeB["id"]:
            if nodeA["selector"] == nodeB["labels"]:
              edges.append({"from": nodeA["id"], "to": nodeB["id"]})
          if "-statefulset" in nodeB["id"]:
            if nodeA["selector"] == nodeB["labels"]:
              edges.append({"from": nodeA["id"], "to": nodeB["id"]})
        if nodeA["group"] == "docker":
          if nodeB["group"] == "docker":
            edges.append({"from": nodeA["id"], "to": nodeB["id"]})

    # edges = [{"from": a, "to": b, "arrows": "to",
    #           "label": "depends on", "color": {"color": "#ff0000",
    #                                            "opacity": 0.3}}
    #          for a in service_dict['services']
    #          for b in service_dict['services']
    #          if b in service_dict['services'][a].get('depends_on',[])]

    # all_edges = [[{"from": a, "to": b, "arrows": "to",
    #                "id": a + "-to-" + b},
    #               {"from": a, "to": "public", "arrows": "to",
    #                "id": a + "-to-public"},
    #               {"from": "public", "to": a, "arrows": "to",
    #                 "id": "public-to-" + a}]
    #              for a in service_dict['services']
    #              for b in service_dict['services']
    #              if a is not b]

    # all_edges = list(unique_everseen(collapse(all_edges, base_type=dict)))

    return nodes, edges, all_edges
