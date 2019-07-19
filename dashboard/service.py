import yaml
import json

from more_itertools import collapse, unique_everseen

def generate_visjs_graph(service_file):
    service_dict = yaml.safe_load(service_file)

    nodes = [{"id": service, "label": service, "group": "service"}
             for service in service_dict['services']]

    nodes.append({"id": "public", "label": "public", "group": "public"})

    edges = [{"from": a, "to": b, "arrows": "to",
              "label": "depends on", "color": {"color": "#ff0000",
                                               "opacity": 0.3}}
             for a in service_dict['services']
             for b in service_dict['services']
             if b in service_dict['services'][a].get('depends_on',[])]

    all_edges = [[{"from": a, "to": b, "arrows": "to",
                   "id": a + "-to-" + b},
                  {"from": a, "to": "public", "arrows": "to",
                   "id": a + "-to-public"},
                  {"from": "public", "to": a, "arrows": "to",
                    "id": "public-to-" + a}]
                 for a in service_dict['services']
                 for b in service_dict['services']
                 if a is not b]

    all_edges = list(unique_everseen(collapse(all_edges, base_type=dict)))
    return nodes, edges, all_edges
