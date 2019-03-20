import yaml
import json


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

    all_edges = [{"from": a, "to": b, "arrows": "to",
                  "id": a + "-to-" + b}
                 for a in service_dict['services']
                 for b in service_dict['services']
                 if a is not b]

    edges_to_public = [{"from": d["from"],
                        "to": "public", "arrows": "to",
                        "id": d["from"] + "-to-public"}
                       for d in all_edges]

    edges_from_public = [{"from": "public",
                          "to": d["from"], "arrows": "to",
                          "id": "public-to-" + d["from"]}
                         for d in all_edges]

    return nodes, edges, all_edges + edges_to_public + edges_from_public
