#!/usr/bin/env python
# This processes output of the TracerouteMover. 
# It expects only the JSON output with the complete traceroute record on a single line 

# To create a DOT file from an IDPL logfile that has TRACEROUTE records
# grep TRACEROUTE: logfile | awk -F TRACEROUTE: '{print $NF}' | trGraph.py
import json
import sys
def dotOutput(nodes,edges):
	graph = 'digraph G { \n'
	for (fr,to) in edges:
		graph += '\"%s\"-> \"%s\"\n' % (fr,to)
	for (n,terminal) in nodes:
		color = "green" if terminal else "lightblue"
		graph += '\"%s\" [style=filled fillcolor=%s]\n' % (n,color)
	graph += "}"
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
	nodes.add((fr,True))
	nodes.add((dst,True))
	nrec = len(record['path'])
	n = 0
	for hop in record['path']:
		n += 1
		if len(hop) > 2:
			node = hop[1]
			if n != nrec:
				nodes.add((node,False))
				edges.add((fr,node))
			else:
				edges.add((fr,dst))
			fr = node

print dotOutput(nodes,edges)
