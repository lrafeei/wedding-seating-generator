# Wedding Seating Chart Generator

This program takes in a csv generated Relationship Matrix and outputs the top ten seating arrangements.  This program uses the concept of annealing to traverse a number of combinations, dictated by the granularity setting.

## To Run:
`python seating_chart.py -f/--csv-file CSV_FILE -s/--table-size TABLE_SIZE [-g/--granularity GRANULARITY]`

where:
    * `CSV_FILE`: the name of the relationship matrix, in CSV form
    * `TABLE_SIZE`: (int>0) the number of people that can be seated at a table
    * `GRANULARITY`: 0 for coarse, 1 for medium, or 2 for fine granularity.  CAUTION: The fine granularity setting may crash on your machine.  See Future Iterations section for more details

## Inputs:
A CSV generated Relationship Matrix.  Relationship values range from -50 to 50:
  * -50 represents a pair that **MUST** be seated together.
  * 50 represents a pair that **MUST NOT** be seated together.
  
Suggested usage for values:
  * -50: couples
  * -40: best friends
  * -30: friends/close family
  * -20: family
  * -10: aquaintances
  * -1: People who know the same people (ex: Guest1 and Guest2 both know the bride but have never met)
  * 30: people who do not like each other/will not get along
  * 50: exes/must not be together

[Example matrix can be found here](https://docs.google.com/spreadsheets/d/1PBkLAMQLiPJGh8No_cHEtPoOYK-vn1FRRrIRAhMqr20/edit?usp=sharing)
  * Note that only the "bottom" half of the matrix is populated (the "top" half is greyed out).  It is not necessary to duplicate data by filling out both sides.  One side is sufficient.  
  * To save this as a .csv, File > Download > Comma Separated Values (.csv)

## Outputs:
Top ten seating arrangement options for all guests per table.  This will be in a file `seating_options.txt` generated in the same directory this program was executed.

## Caveats/ Assumptions Made:
  * This program assumes (for now) that tables are the same size/hold the same number of people.
  * This program does not dictate the seating arrangements within the table (only assigns people to a specific table).

## To do for future iterations:
  * Add non-mutable settings.  This would make it so that certain pairings (i.e. couples) cannot be separated under any circumstances.
  * Feature: Implement multiprocessing for annealing iterations
  * Feature: Add option to assign individual seats within table.
  * Feature: Add tables of different sizes
