#!/usr/local/bin

import networkx as nx
import numpy as np
import math
import sys

# This program uses simulated annealing to determine the best
# seating chart arrangement for a wedding.
# (Simulated annealing works well for "escaping" local maxima)
# inputs : table size, guest matrix (which also has # of guests)
# outputs : table arrangement with lowest cost


def parse(matrix):
	relationship_matrix_dict = dict()
	# Format: {("Lalleh Rafeei", "Rob Wheaton"): -50}
	with open(matrix) as file:
		lines = file.readlines()

	for line_num, line in enumerate(lines):
		line_array = line.strip().split(",")
		if line_num == 0:
			guest_list = line_array
		else:
			for index, relationship in enumerate(line_array):
				if index > 0 and relationship:
					entry = {(line_array[0], guest_list[index]): int(relationship)}
					relationship_matrix_dict.update(entry)

	return relationship_matrix_dict, guest_list


def random_initial_table_generator(guest_count, guests_per_table):
	"""
	Create function that will create an initial table arrangement to “swap” throughout.
	Table must be [guest_count] wide and [number of tables] in height
	Table must contain [guests per table] 1s and the rest 0s
	"""
	extra_people = guest_count % guests_per_table
	fillers_needed = (
		guests_per_table - extra_people
	)  # This is needed to have each spot available
	number_of_tables = math.ceil(guest_count / guests_per_table)
	initialized_guest_tables = np.zeros(
		(number_of_tables, guest_count + fillers_needed), dtype=int
	)

	# Go through first row, replace first 8 values with 1, then go to second row, continue on same index
	row = -1  # index % guests_per_table == 0 when index == 0
	for index in range(guest_count + fillers_needed):
		# if index % 8, move down to the next row
		if index % guests_per_table == 0:
			row += 1
		initialized_guest_tables[row][index] = 1

	return initialized_guest_tables


def anneal(
	pos_current,
	queue=None,
	temperature=1.0,
	temperature_min=0.00001,
	alpha=0.95,
	n_iter=100,
):
	def reshape_to_table_seats(position):
		table_seats = position.reshape(table_count, len(guest_list))
		return table_seats


	def cost(position):
		table_seats = reshape_to_table_seats(position)
		table_costs = table_seats * relationship_matrix * table_seats.T
		table_cost = np.trace(table_costs)
		return table_cost


	def take_step(cur_arrangement):
		table_seats = reshape_to_table_seats(np.array(cur_arrangement, copy=True))
		table_from, table_to = np.random.choice(table_count, 2, replace=False)

		table_from_guests = np.where(table_seats[table_from] == 1)[0]
		table_to_guests = np.where(table_seats[table_to] == 1)[0]

		table_from_guest = np.random.choice(table_from_guests)
		table_to_guest = np.random.choice(table_to_guests)

		table_seats[table_from, table_from_guest] = 0
		table_seats[table_from, table_to_guest] = 1
		table_seats[table_to, table_to_guest] = 0
		table_seats[table_to, table_from_guest] = 1
		return table_seats


	# The nuts and bolts of the annealing algorithm:
	# If at the beginning of the program's operation, the
	# algorithm is more likely to escape its local maxima
	# by not always accepting the (perceived) maximum
	# value and to try other options anyway.
	# This is compared to a random number (from 0 to 1)
	# to make that decision
	def probability_of_acceptance(cost_old, cost_new, temperature):
		if cost_new < cost_old:
			a = 1
		else:
			a = np.exp((cost_old - cost_new) / temperature)
		return a

	top_10_seating_arrangements = queue if queue else []
	cost_old = cost(pos_current)
	cost_max = cost_old
	pos_max = pos_current

	while temperature > temperature_min:
		for _ in range(n_iter):
			pos_new = take_step(pos_current)
			cost_new = cost(pos_new)
			if cost_new < cost_max:
				pos_max = pos_new
				cost_max = cost_new
				# Collect for top 10:
				top_10_seating_arrangements = top_10_queue(
					pos_max, cost_max, top_10_seating_arrangements
				)
			prob_accept = probability_of_acceptance(cost_old, cost_new, temperature)
			if prob_accept > np.random.random():
				pos_current = pos_new
				cost_old = cost_new
		temperature *= alpha
	return top_10_seating_arrangements


def top_10_queue(position, cur_cost, queue):
	# This will sort by the cost (second element of tuple)
	# and therefore, the most optimal seating arrangement
	# will be the first element

	if not len(queue):
		queue.append((position, cur_cost))
		return queue

	queue.sort(key=lambda x: x[1])

	# Last element will be the max cost
	if len(queue) and cur_cost < queue[-1][1]:
		# if queue is already at 10, we need to pop the entry with the
		# highest value (least optimized in our case):
		if len(queue) == 10:
			# Pop the least optimal seating arrangement
			del queue[-1]
		queue.append((position, cur_cost))

	return queue


def readability(result, guest_list, TABLE_SIZE):
	# Print out names instead of 0/1

	tables = []
	for table in result:
		guest_index = 0
		guests = [None] * TABLE_SIZE
		for guest in range(len(table)):
			if table[guest] == 1:
				guests[guest_index] = guest_list[guest]
				guest_index += 1
		tables.append(guests)
	return tables


def initialize(relationship_matrix_file, table_size):
	"""
	relationship_matrix_file: "guest_matrix.csv"
	table_size: number of people per table
	"""

	relationship_edges, guest_list = parse(relationship_matrix_file)
	guest_list = guest_list[1:]

	TABLE_SIZE = table_size
	GUEST_COUNT = len(guest_list)
	table_count = math.ceil(GUEST_COUNT / TABLE_SIZE)

	# This does not work with uneven guest counts, so we need to make filler guests
	# who have no relationship established with anyone.
	extra_people = GUEST_COUNT % TABLE_SIZE
	fillers_needed = TABLE_SIZE - extra_people

	temp_graph = nx.Graph()

	# Add Empty Seats because the algorithm cannot handle blank spaces
	# A relationship of weight=0 is added to the first guest so that
	# the filler spaces can function as regular spots.
	for i in range(fillers_needed):
		name = f"Empty Seat {i}"
		guest_list.append(name)
		temp_graph.add_edge(guest_list[0], name, weight=0)

	for guest, weight in relationship_edges.items():
		temp_graph.add_edge(guest[0], guest[1], weight=weight)

	# Does not like "Empty Seat" guest, so they must be numbered
	relationship_matrix_raw = nx.to_numpy_matrix(
		temp_graph.to_undirected(), nodelist=guest_list
	)
	relationship_matrix = relationship_matrix_raw / 100

	return GUEST_COUNT, guest_list, relationship_matrix, table_count



if __name__ == "__main__":
	# Input is guest matrix, additional input prompts ask for table size
	relationship_matrix_file = sys.argv[1]
	print("Enter the number of people per table: ")
	TABLE_SIZE = int(input())
	print("Enter the desired granularity.  Leave blank for default.  Options: 1=fine, 2=super fine: ")
	granularity_input = input()
	GRANULARITY = 100 if not granularity_input else pow(10,2+int(granularity_input))
	print("Calculating now.  Results will be available in seating_options.txt")

	top_10_result = []
	GUEST_COUNT, guest_list, relationship_matrix, table_count = initialize(relationship_matrix_file, TABLE_SIZE)

	# Logic for running annealing 10 times while extracting
	# top 10 results from those combined runs:

	for percent in range(10):
		# Generate a random array for this instead of manually filling in a
		# random array.  This gives us our starting point for our program.
		# The shuffling will happen from this point.
		table_seats_a = random_initial_table_generator(GUEST_COUNT, TABLE_SIZE)  		
		top_10_result = anneal(table_seats_a, top_10_result, alpha=0.99, n_iter=GRANULARITY)
		print("%d %% Percent Complete" % ((percent+1)*10))

	with open("seating_options.txt", "a") as file:
		for result in top_10_result:
			position, cur_cost = result
			for index, tables in enumerate(
				readability(position, guest_list, TABLE_SIZE)
			):
				file.write("Table " + str(index + 1))
				file.write("\n")
				file.write(", ".join(tables))
				file.write("\n")
			file.write(str(cur_cost))
			file.write("\n\n")