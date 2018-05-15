
# IMPORTIES!
import sys, pickle, itertools, time, json, warnings, os
import networkx as nx
import matplotlib.pyplot as plt
from networkx.readwrite import json_graph
warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')

# load data
def load_nodes_and_edge_data(all_oros_path, object_data_path):

	print('** Fetching Data...')
	start_time = time.time()

	# load oro files
	with open(all_oros_path, 'rb') as handle:
		all_oros = pickle.load(handle)

	# load object data
	with open(object_data_path, 'rb') as handle:
		object_data = pickle.load(handle)

	print('		Takes', "-- %.2f seconds --" % (time.time() - start_time),
		'to load', len(all_oros), 'OROs')
	print()

	# return oro pairs and object data
	return all_oros, object_data

# if we have to find all Rs to an O
def find_relations(oro_pairs, word):

		incoming_relations = []
		outgoing_relations = []
		for each_pair in oro_pairs:
			if word == each_pair['ORO'][2]:
				incoming_relations += [each_pair]
			if word == each_pair['ORO'][0]:
				outgoing_relations += [each_pair]

		return incoming_relations, outgoing_relations

# build the graph
def build_graph(oro_pairs, object_data, file_name):
	#
	# create empty graph
	# digraph to represent flow
	print('** Building the Graph...')
	start_time = time.time()
	#
	G = nx.MultiDiGraph()
	#
	# get all occurences of ORO pairs as a count
	# all_relations = incoming_relations + outgoing_relations
	pair_and_occurences = {}
	for each_pair in oro_pairs:
		if " ".join(each_pair['ORO']) in pair_and_occurences.keys():
			pair_and_occurences[" ".join(each_pair['ORO'])] += 1
		else:
			pair_and_occurences[" ".join(each_pair['ORO'])] = 1
	#
	# arrange graph bits
	graph_bits = []
	for each_pair in oro_pairs:
		graph_bits += [{'node_pairs' : [each_pair['ORO'][0], each_pair['ORO'][2]],
						'relationship' : each_pair['ORO'][1],
						'sentiment' : each_pair['R-Sentiment'],
						'truth_value' : pair_and_occurences[" ".join(each_pair['ORO'])]}]
	#
	#
	for each_bit in graph_bits:
		#
		# add nodes & properties
		property_1 = ['null'] if len(object_data[each_bit['node_pairs'][0]]['properties']) == 0 else object_data[each_bit['node_pairs'][0]]['properties']
		G.add_node(each_bit['node_pairs'][0],
			property = property_1,
			sentiment = object_data[each_bit['node_pairs'][0]]['sentiment'],
			occurences = object_data[each_bit['node_pairs'][0]]['occurences'])
		#
		# add more nodes & properties
		property_2 = ['null'] if len(object_data[each_bit['node_pairs'][1]]['properties']) == 0 else object_data[each_bit['node_pairs'][1]]['properties']
		G.add_node(each_bit['node_pairs'][1], 
			property = property_2,
			sentiment = object_data[each_bit['node_pairs'][1]]['sentiment'],
			occurences = object_data[each_bit['node_pairs'][0]]['occurences'])
		#
		# add edges & details
		G.add_edge(each_bit['node_pairs'][0], each_bit['node_pairs'][1], 
					relationship=each_bit['relationship'], 
					sentiment=each_bit['sentiment'],
					truth=each_bit['truth_value'])
	# 
	#
	nx.write_gml(G, file_name)
	#
	print('		Takes', "-- %.2f seconds --" % (time.time() - start_time),
		'to build graph for', len(oro_pairs), 'OROs.')
	print()

# build graph including all OROs
if __name__ == "__main__":
	#
	# load the oro-pairs
	# and object details
	oro_pairs, object_data = load_nodes_and_edge_data('facebook_OROs.pkl', 'facebook_object_data.pkl')
	#	
	# compile the graph now
	build_graph(oro_pairs, object_data, 'facebook.gml')