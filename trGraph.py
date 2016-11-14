#!/usr/bin/env python
# This processes output of the TracerouteMover. 
# It expects only the JSON output with the complete traceroute record on a single line 

# To create a DOT file from an IDPL logfile that has TRACEROUTE records
# grep TRACEROUTE: logfile | awk -F TRACEROUTE: '{print $NF}' | trGraph.py
import json
import sys
def dotOutput(nodes,edges):
	graph = 'digraph Traceroute { \n'
	graph += '   label="IDPL Traceroute Display";\n'
	subgraph = 'subgraph v4 { \n '
	subgraph += '   label="IPv4 Traceroute Display";\n'
	subgraph6 = 'subgraph v6 { \n '
	subgraph6 += '   label="IPv6 Traceroute Display";\n'
	for (fr,to,v6) in edges:
		edge = '\"%s\"-> \"%s\"\n' % (fr,to)
		if v6:
			subgraph6 += edge
		else:
			subgraph += edge
	for (n,terminal,v6) in nodes:
		color = "green" if terminal else "lightblue"
		node = '\"%s\" [style=filled fillcolor=%s]\n' % (n,color)
		if v6:
			subgraph6 += node
		else:
			subgraph += node
	subgraph += "} \n"
	subgraph6 += "}\n"
	graph += subgraph6 + subgraph + "}"
	return graph


l = sys.stdin.readlines()
cleaninput=filter(lambda x: len(x) > 0, map(lambda x: x.strip()[0:-1],l))
records = []
for x in cleaninput:
	records.append(json.loads(x))
nodes = set()
edges = set()
for record in records:
	v6 = record['v6']
	fr = record['src'] if not v6 else "%s-v6" %  record['src'] 
	dst = record['dest'] if not v6 else "%s-v6" % record['dest'] 
	nodes.add((fr,True,v6))
	nodes.add((dst,True,v6))
	nrec = len(record['path'])
	n = 0
	for hop in record['path']:
		n += 1
		if len(hop) > 2:
			node = hop[1]
			if n != nrec:
				nodes.add((node,False,v6))
				edges.add((fr,node,v6))
			else:
				edges.add((fr,dst,v6))
			fr = node

print dotOutput(nodes,edges)
