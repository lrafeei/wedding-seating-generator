#!/usr/local/bin

import copy
import argparse
import pathlib
import networkx as nx
import numpy as np
import math
import sys
import csv
import logging

"""
This program uses simulated annealing to determine
the best seating chart arrangement for a wedding.
(Simulated annealing works well for "escaping" local maxima)
"""

# Globals:
GRANULARITY = 1
TABLE_SIZE = None
GUEST_COUNT = None
DEBUG_MODE = False

_logger = logging.getLogger(__name__)


def parse(matrix_file):
    """
    Parse the relationship matrix file.
    
    Args:
        matrix_file (CSV): Relationship matrix file.

    Returns:
        dict: Relationship matrix dict, formatted: {("Lalleh Rafeei", "Lalleh's First Husband"): -50}
        list: guest list
    """
    relationship_matrix_dict = dict()
    with open(matrix_file) as file:
        reader = csv.DictReader(file)
        #breakpoint()
        for row in reader:
            # This will filter entries that have a specified relationship value and no
            # duplicates.  In this case, ("Lalleh Rafeei", "Lalleh's First Husband")
            # and ("Lalleh's First Husband", "Lalleh Rafeei") are duplicates.
            try:
                entry = {(row[""], guest): int(relationship) for guest, relationship in row.items() if (guest and relationship and ((guest, row[""]) not in relationship_matrix_dict))}
            except ValueError:
                raise ValueError(f"Non-integer value found in {[x for x in row.values() if not isinstance(x, int)]}")

            if DEBUG_MODE:
                duplicate_entries = {(row[""], guest): int(relationship) for guest, relationship in row.items() if (guest and relationship and ((guest, row[""]) in relationship_matrix_dict))}
                for guest_relationship, relationship_weight in duplicate_entries.items():
                    if relationship_matrix_dict[(guest_relationship[1], guest_relationship[0])] == relationship_weight:
                        _logger.warning("Duplicate in relationship matrix found.  Ignoring one of the two values")
                    else:
                        _logger.warning(
                            "Duplicate relationships found with different relationship values. "
                            "%s and %s have weights %d and %d.  %d will be used.",
                            guest_relationship[0],
                            guest_relationship[1],
                            relationship_matrix_dict[(guest_relationship[1], guest_relationship[0])],
                            relationship_weight,
                            relationship_matrix_dict[(guest_relationship[1], guest_relationship[0])],
                        )
            relationship_matrix_dict.update(entry)

        if reader.fieldnames[0] != "":
            # The format of this is incorrect.  Exit program
            raise ValueError("Unable to parse file.  Exiting Program.")
        # The first item in the list is a blank value, so we need to trim this.
        guest_list = reader.fieldnames[1:]

    return relationship_matrix_dict, guest_list


def random_initial_table_generator():
    """
    Create function that will create an initial table arrangement to “swap” throughout.
    Table must be [GUEST_COUNT] wide and [number of tables] in height
    Table must contain [guests per table] 1s and the rest 0s
    """
    number_of_tables = math.ceil(GUEST_COUNT / TABLE_SIZE)
    number_of_seats = number_of_tables * TABLE_SIZE     # This will yield a value that includes "fillers"

    initialized_guest_tables = np.zeros(
        (number_of_tables, number_of_seats), dtype=int
    )

    # Go through first row, replace first TABLE_SIZE values with 1,
    # then go to second row, resume from current index, et cetera.
    row = -1  # index % TABLE_SIZE == 0 when index == 0
    for index in range(number_of_seats):
        if index % TABLE_SIZE == 0:
            row += 1
        initialized_guest_tables[row][index] = 1

    return initialized_guest_tables


def anneal(
    pos_current,
    guest_list,
    table_count,
    relationship_matrix,
    queue=None,
    temperature=1.0,
    temperature_min=0.00001,
    alpha=0.99,
    n_iter=10,
):
    def reshape_to_table_seats(position):
        table_seats = position.reshape(table_count, len(guest_list))
        return table_seats


    def cost(position):
        table_seats = reshape_to_table_seats(position)
        table_costs = table_seats.dot(relationship_matrix.dot(table_seats.T))
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
    # At the beginning of the program's operation, the
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

    top_10_seating_arrangements = queue if isinstance(queue, list) else [] 
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
    """
    This will sort by the cost (second element of tuple)
    placing the most optimal seating arrangement first
    """

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


def readability(result, guest_list):
    """
    Print out names instead of 0/1
    to make results human readable
    """

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


def granularity_conversion(granularity_input):
    return pow(GUEST_COUNT//2, 1+granularity_input)


def initialize(relationship_matrix_file, granularity_input):
    """
    relationship_matrix_file: "guest_matrix.csv"
    """
    global GUEST_COUNT, GRANULARITY

    relationship_edges, guest_list = parse(relationship_matrix_file)

    GUEST_COUNT = len(guest_list)
    if TABLE_SIZE >= GUEST_COUNT:
        # We can end the program right now. There
        # is only one option and that is to seat
        # everyone at the same table.
        print("There is no need for this program. There is room for everyone to sit at the same table.")
        return None, None

    GRANULARITY = granularity_conversion(granularity_input)

    # This program needs to have the same number of guests
    # as table seats, which will likely not happen. To
    # solve this issue, we need to create "filler" guests
    # who have no relationship established with anyone.
    extra_people = GUEST_COUNT % TABLE_SIZE
    fillers_needed = TABLE_SIZE - extra_people

    temp_graph = nx.Graph()

    # A relationship of weight=0 is added to the first guest so that
    # the filler spaces can function as regular spots.
    for i in range(fillers_needed):
        name = f"Empty Seat {i}"
        guest_list.append(name)
        temp_graph.add_edge(guest_list[0], name, weight=0)

    for guest, weight in relationship_edges.items():
        temp_graph.add_edge(guest[0], guest[1], weight=weight)

    relationship_matrix_raw = nx.to_numpy_array(
        temp_graph.to_undirected(), nodelist=guest_list
    )
    relationship_matrix = relationship_matrix_raw / 100

    return guest_list, relationship_matrix


def table_size_checker(table_size):
    """
    Tests the validity of the input for the 
    size of the table.  For now, our program
    assumes that all tables are the same size.
    Return table_size as int if valid.
    """
    try:
        int_table_size = int(table_size)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{table_size} is not a valid integer.")
    if int_table_size <= 0:
        raise argparse.ArgumentTypeError(f"{table_size} is not a positive integer.")
    return int_table_size


def csv_file_checker(csv_file):
    """
    Tests whether or not the CSV file exists
    and whether it is a valid CSV file.
    """
    try:
        with open(csv_file, newline='') as csvfile:
            # Just check to see if file is readable
            # by reading first line.
            csvfile.readline()
    except FileNotFoundError:
        raise argparse.ArgumentTypeError(f"{csv_file} not found.")
    except csv.Error as csv_exc:
        raise argparse.ArgumentTypeError(f"CSV file exception was found: {csv_exc}")
    except Exception as exc:
        raise argparse.ArgumentTypeError(f"Exception was found: {exc}")
    else:
        return csv_file


def argument_parser():
    global DEBUG_MODE

    parser = argparse.ArgumentParser(
            prog="seating_chart",
            description="Seating Chart Generator",
            usage="python %(prog)s.py -f/--csv-file -s/--table-size [-g/--granularity] [-d/--debug]",
    )
    parser.add_argument("-f", "--csv-file", type=csv_file_checker, help="CSV file", required=True)
    parser.add_argument("-s", "--table-size", type=table_size_checker, help="A positive integer", required=True)
    parser.add_argument("-g", "--granularity", type=int, choices=[0, 1, 2], default=0, help="0, 1 or 2 for coarse, medium, or fine granularity")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")

    parsed_args = parser.parse_args()
    csv_file = getattr(parsed_args, "csv_file")
    table_size = getattr(parsed_args, "table_size")
    granularity_input = getattr(parsed_args, "granularity")
    DEBUG_MODE = getattr(parsed_args, "debug", False)

    return csv_file, table_size, granularity_input


def main(matrix_file, table_size, granularity_input):
    global TABLE_SIZE

    TABLE_SIZE = table_size
    relationship_matrix_file = matrix_file

    top_10_result = []
    guest_list, relationship_matrix = initialize(relationship_matrix_file, granularity_input)
    table_count = math.ceil(GUEST_COUNT / TABLE_SIZE)

    if guest_list is None and relationship_matrix is None:
        # One table is large enough for all the guests.
        # Exit program now.
        return "Seat everyone at one table"

    # Logic for running annealing 10 times while extracting
    # top 10 results from those combined runs:

    for percent in range(10):
        # Generate a random array for this instead of manually filling in a
        # random array.  This gives us our starting point for our program.
        # The shuffling will happen from this point.
        table_seats_a = random_initial_table_generator()
        top_10_result = anneal(table_seats_a, guest_list, table_count, relationship_matrix, top_10_result, n_iter=GRANULARITY)
        print("%d Percent Complete" % ((percent+1)*10))

    with open("seating_options.txt", "w") as file:
        for result in top_10_result:
            position, cur_cost = result
            for index, tables in enumerate(
                readability(position, guest_list)
            ):
                file.write("Table " + str(index + 1))
                file.write("\n")
                file.write(", ".join(tables))
                file.write("\n")
            file.write(str(cur_cost))
            file.write("\n")
            file.write("="*50)
            file.write("\n\n")


if __name__ == "__main__":
    parsed_args = argument_parser()
    main(*parsed_args)




