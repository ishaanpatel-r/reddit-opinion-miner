

import os, pickle, sys, slugify, itertools, nltk
from pprint import pprint
import numpy as np
from nltk.stem.lancaster import LancasterStemmer
st = LancasterStemmer()
from pattern3.en import conjugate
from pattern3.en import sentiment
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
analyzer = SentimentIntensityAnalyzer()
oro_counter = 0
import re
from itertools import groupby

def create_PORSPO_regexes():
	'''
	GROUPS:

	1. (tag as 'P') JJ Group <= 2	(can have JJ, JJR, JJS)
	2. (tag as 'O') NN Group <=3	(can have NN, NNS)
	3. (tag as 'R') VB Group <= 2	(can have VB, VBD, VBG, VBN, VBP, VBZ)
	4. (tag as 'S') IN/TO Group == 1	(can have IN, TO)
	'''	

	# # # # #
	# CATEGORIES OF OROs
	# # # # #
	#
	# 1. Basic ORO
	basic_oros = ['O', 'R', 'O']
	#
	# 2. Only Property Inclusion
	pi_poro = ['P', 'O', 'R', 'O']
	pi_orpo = ['O', 'R', 'P', 'O']
	pi_porpo = ['P', 'O', 'R', 'P', 'O']
	#
	# 3. Only Shifter Inclusion
	si_orso = ['O', 'R', 'S', 'O']
	#
	# 4. Property & Shifter Inclusion
	spi_orspo = ['O', 'R', 'S', 'P', 'O']
	spi_porso = ['P', 'O', 'R', 'S', 'O']
	spi_porspo = ['P', 'O', 'R', 'S', 'P', 'O']
	#
	# add all categories to basic PORSPOs
	BASIC_PORSPO = [basic_oros] + [pi_poro] + [pi_orpo] + [pi_porpo] + [si_orso] + [spi_orspo] + [spi_porso] + [spi_porspo]
	# (we'll be expanding these now)

	# generate expanded regexes
	ALL_PORSPO = []
	#
	# expand based on rules
	regexes = []
	for each_PORSPO in BASIC_PORSPO:
		pattern_in_string = "".join(each_PORSPO)
		regexes += [pattern_in_string.replace('O', 
					'O{1,3}').replace('R', 
					'R{1,2}').replace('S', 
					'S{1,1}').replace('P', 
					'P{1,2}')]
	#
	return regexes

# iterate through tagged sequence
# remove DT
# change 'I love you.' into:
# [[0, I, PRP], [1, love, VBG], [2, you, PRP], [3, ., .]]
def serialize_and_tag(sequence):

	# split sentence into words
	word_sentence = nltk.word_tokenize(sequence)

	# tag the sequence with POS tags
	tokenized_sequence = nltk.pos_tag(word_sentence)

	# make serials
	serialized_sequence = []
	adjusted_index = 0
	for i in range(len(word_sentence)):
		if tokenized_sequence[i][1] != 'DT':
			serialized_sequence += [(adjusted_index, word_sentence[i], tokenized_sequence[i][1])]
			adjusted_index += 1
	return serialized_sequence

# generate oro patterns
def find_all_oro_pairs(sequence, PORSPO_regexes):

	# get serialized sequence
	serialized_sequence = serialize_and_tag(sequence)
	#
	# now we combine groups
	grouped_serialized_sequnce = []
	pos_tree = [pos_tag for (index, word, pos_tag) in serialized_sequence]
	word_sequence = [word for (index, word, pos_tag) in serialized_sequence]

	# basically we take what we want
	# and 'E' the rest for faster extraction
	replacement_tag = {
		'JJ' : 'P',
		'JJR' : 'P',
		'JJS' : 'P',
		'NN' : 'O',
		'NNS' : 'O',
		'VB' : 'R',
		'VBD' : 'R',
		'VBG' : 'R',
		'VBN' : 'R',
		'VBP' : 'R',
		'VBZ' : 'R',
		'IN' : 'S',
		'TO' : 'S'
	}

	# create the 'take what we want' tree
	PORSE_tree = []
	for i in range(len(pos_tree)):
		try:
			PORSE_tree += [replacement_tag[pos_tree[i]]]
		except:
			PORSE_tree += ['E']
	
	# get all sequences from 'TWWW' tree
	# and form a list of tuples like
	# [('O', word), ('R', word), ...]
	indexes_to_fetch_from = []
	oro_tuples = []
	for each_PORSPO_regex in PORSPO_regexes:
		rex = re.compile(each_PORSPO_regex)
		PORSE_str = "".join(PORSE_tree)
		if len(rex.findall(PORSE_str)) > 0:
			for each_match in rex.findall(PORSE_str):
				oro_tuples += [list(zip(word_sequence[PORSE_str.index(each_match):PORSE_str.index(each_match)+len(each_match)], 
					[i for i in each_match]))]

	# this block creates OROs
	# from all sorts of PORSPOs
	all_oros_found = []
	for each_oro_tuple in oro_tuples:
		object_one = []
		object_two = []
		relationship = []
		is_first = True
		#
		# get 1st object data
		# 2nd object data
		# and R data
		for each_word_pos_pair in each_oro_tuple:
			if (((each_word_pos_pair[1] == 'P') or (each_word_pos_pair[1] == 'O')) and is_first == True):
				object_one += [each_word_pos_pair]
			elif ((each_word_pos_pair[1] == 'R') or (each_word_pos_pair[1] == 'S')):
				relationship += [each_word_pos_pair]
				is_first = False
			else:
				object_two += [each_word_pos_pair]
		#
		# purge PORSPOs into OROs now
		# (ignore this entire block!)
		# DO NOT TOUCH OR FIDDLE!
		O_one = []
		for each_word_pos_pair in object_one:
			if each_word_pos_pair[1] == 'O':
				O_one += [each_word_pos_pair[0]]
		O_two = []
		for each_word_pos_pair in object_two:
			if each_word_pos_pair[1] == 'O':
				O_two += [each_word_pos_pair[0]]
		altered_R = []
		for each_word_pos_pair in relationship:
			# separated since we might 
			# need conjugates for R	
			if each_word_pos_pair[1] == 'R':
				altered_R += [each_word_pos_pair[0]]
			if each_word_pos_pair[1] == 'S':
				altered_R += [each_word_pos_pair[0]]
		object_properties = {}
		for each_word_pos_pair in object_one:
			if each_word_pos_pair[1] == 'P':
				try:
					object_properties[slugify.slugify(" ".join(O_one))] += [each_word_pos_pair[0]]
				except:
					object_properties[slugify.slugify(" ".join(O_one))] = ['null']
					object_properties[slugify.slugify(" ".join(O_one))] = [each_word_pos_pair[0]]
		for each_word_pos_pair in object_two:
			if each_word_pos_pair[1] == 'P':
				try:
					object_properties[slugify.slugify(" ".join(O_two))] += [each_word_pos_pair[0]]
				except:
					object_properties[slugify.slugify(" ".join(O_two))] = ['null']
					object_properties[slugify.slugify(" ".join(O_two))] = [each_word_pos_pair[0]]
		#
		# gather all OROs accumulated
		all_oros_found += [([slugify.slugify(" ".join(O_one)), slugify.slugify(" ".join(altered_R)), slugify.slugify(" ".join(O_two))], object_properties)]

	# filter out duplicates caused
	# by iterating over tuples -___-
	OROs = []
	obj_props = {}
	for each_oro_found in all_oros_found:
		if each_oro_found[0] not in OROs:
			OROs += [each_oro_found[0]]
		for each_key in each_oro_found[1].keys():
			if each_key not in obj_props.keys():
				obj_props[each_key] = each_oro_found[1][each_key]

	return (OROs, obj_props)

if __name__ == '__main__' : 
	#
	# create OROs we need
	PORSPO_regexes = create_PORSPO_regexes()
	#
	# load pickle and show data gathered
	all_sentences = []
	with open('facebook_related_opinions.pkl', 'rb') as handle:
		all_sentences = pickle.load(handle)

	print(len(all_sentences))

	# iterate through each sentence
	# in this article
	all_oros = []
	object_data = {}
	for each_sentence in all_sentences:
		#
		oro_pairs, obj_props = find_all_oro_pairs(each_sentence, PORSPO_regexes)
		#
		# if any OROs found
		if len(oro_pairs) > 0:
			print(oro_pairs)
			#
			# add all OROs and R-sentiments
			# and object details
			for each_pair in oro_pairs:
				#
				O_1 = slugify.slugify(each_pair[0])
				O_2 = slugify.slugify(each_pair[2])
				R = slugify.slugify(each_pair[1])
				if ((O_1 != '') and (O_2 != '') and (R != '')):
					#
					# track how many pairs have 
					# been extracted
					print(oro_counter)
					oro_counter += 1
					#
					# get ORO sentiment
					vs = analyzer.polarity_scores(" ".join(each_pair).replace('-', ' ').strip())
					oro_sent = float("{0:.2f}".format(vs['compound'], 2))
					#
					# add to ORO list (containing dicts)
					all_oros += [{'ORO' : [O_1, R, O_2], 'R-Sentiment' : oro_sent,
					'Sequence' : each_sentence}]
					#
					# add to O-Data
					if O_1 not in object_data.keys():
						object_data[O_1] = {'sentiment' : 0,
										'properties' : [],
										'occurences' : 0}
					if O_2 not in object_data.keys():
						object_data[O_2] = {'sentiment' : 0,
										'properties' : [],
										'occurences' : 0}
					#
					# update O-sentiments
					object_data[O_1]['sentiment'] = float("{0:.2f}".format(np.mean([object_data[O_1]['sentiment'], oro_sent])))
					object_data[O_2]['sentiment'] = float("{0:.2f}".format(np.mean([object_data[O_2]['sentiment'], oro_sent])))
					#
					# add object counts
					object_data[O_1]['occurences'] += 1
					object_data[O_2]['occurences'] += 1
					#
					# add O-properties only if found
					# else ignore
					try:
						object_data[O_1]['properties'] += obj_props[O_1]
					except:
						pass
					try:
						object_data[O_2]['properties'] += obj_props[O_2]
					except:
						pass


	# save pickle
	with open('facebook_OROs.pkl', 'wb') as handle:
	    pickle.dump(all_oros, handle, protocol=pickle.HIGHEST_PROTOCOL)
	#
	# save all object-properties pickles
	with open('facebook_object_data.pkl', 'wb') as handle:
		pickle.dump(object_data, handle, protocol=pickle.HIGHEST_PROTOCOL)


	pprint(all_oros[:3])
	pprint(object_data)