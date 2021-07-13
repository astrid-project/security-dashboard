import uuid


def generate_visjs_graph(service_file):
  services = []
  deployments = []
  pods = []
  containers = []

  edges = []

  for y in service_file: 
      if y['kind'] == 'Service':
          if 'annotations' in y['metadata']:
              if 'graphId' in y['metadata']['annotations']:
                  graphId = y['metadata']['annotations']['graphId']
          else:
              graphId = str(uuid.uuid4())
              y['metadata']['annotations'] = {'graphId': graphId}
          selector = y['spec']['selector']
          services.append({
              'id': graphId,
              'label': y['metadata']['name'],
              'group': "k8_svc",
              'selector': selector
          })
      if y['kind'] == 'Deployment':
          if 'annotations' in y['metadata']:
              if 'graphId' in y['metadata']['annotations']:
                  graphId = y['metadata']['annotations']['graphId']
          else:
              graphId = str(uuid.uuid4())
              y['metadata']['annotations'] = {'graphId': graphId}
          selector = y['metadata']['labels']
          deployments.append({
              'id': graphId,
              'label': y['metadata']['name'],
              'group': "k8_dep",
              'selector': selector
          })
          for c in y['spec']['template']['spec']['containers']:
              if c['name'] in y['metadata']['annotations']:
                  containerId = y['metadata']['annotations'][c['name']]
              else:
                  containerId = str(uuid.uuid4())
                  y['metadata']['annotations'][c['name']] = containerId

              containers.append({
                  'id': containerId,
                  'label': c['name'],
                  'group': "k8_pod"
              })

              edges.append({"from": graphId, "to": containerId})

  for s in services:
      for d in deployments:
          if s['selector'] == d['selector']:
              edges.append({"from": s['id'], "to": d['id']})

  nodes = services + deployments + pods + containers

  return service_file, nodes, edges
