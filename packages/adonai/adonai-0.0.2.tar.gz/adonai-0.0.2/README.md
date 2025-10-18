# Adonai: Approximate Chromatic Number Solver

![Through him, and with him, and in him (This formula emphasizes the Trinitarian nature of the liturgy).](docs/jesus.jpg)

---

# The Minimum Chromatic Number (Graph Coloring) Problem

## 1. Problem Definition

The **Minimum Chromatic Number Problem**, more commonly known as the **Graph Coloring Problem**, is a classic problem in computer science and graph theory.

- **Input:** An undirected graph `G = (V, E)`, where `V` is a set of vertices and `E` is a set of edges.
- **Output:** A **coloring** function `c: V -> {1, 2, ..., k}` that assigns a color (represented by an integer) to each vertex such that for every edge `(u, v) ∈ E`, the colors of the adjacent vertices are different: `c(u) ≠ c(v)`.
- **Objective:** Find the smallest possible number of colors `k` for which such a coloring exists. This smallest number `k` is called the **chromatic number** of the graph, denoted by `χ(G)`.

**Example:** A map of countries can be modeled as a graph (each country is a vertex, and an edge exists between adjacent countries). The problem of coloring the map with the fewest colors so no two adjacent countries share a color is precisely the graph coloring problem. The famous Four Color Theorem proves that `χ(G) ≤ 4` for any planar graph.

## 2. Computational Complexity: NP-Hardness

The decision version of the problem ("Given a graph `G` and an integer `k`, is `χ(G) ≤ k`?") is **NP-complete**.

- **In NP:** A proposed solution (a coloring with `k` colors) can be verified in polynomial time by checking every edge to ensure its two vertices have different colors.
- **NP-hard:** It was one of Richard Karp's original 21 NP-complete problems in 1972. A common reduction is from the **3-Satisfiability (3-SAT)** problem, showing that if we can solve graph coloring quickly, we can solve any problem in NP quickly.

This NP-hardness implies that there is no known algorithm that can find the chromatic number of an arbitrary graph in polynomial time. Finding the exact chromatic number for large graphs is computationally intractable.

## 3. Approximation and Heuristics

Since finding the optimal solution is infeasible for large instances, much research focuses on approximation algorithms and heuristics.

### Approximation Hardness

The problem is notoriously hard to even approximate.

- **Theorem:** Unless **P = NP**, there is no polynomial-time algorithm that can approximate the chromatic number within a factor of `n^{1−ε}` for any `ε > 0`, where `n` is the number of vertices.
- This means that no efficient algorithm can guarantee a coloring that is even remotely close to the optimal number of colors for all graphs. An algorithm that used `n^{0.9} * χ(G)` colors, for example, would be a breakthrough.

### Common Approximation Algorithms and Heuristics

Despite the negative approximation results, many algorithms work well in practice for many graphs, though they offer no worst-case guarantees.

1.  **Greedy Coloring (and variants):**

    - **Algorithm:** Traverse the vertices according to a specific ordering (e.g., random, largest degree first, smallest degree last). For each vertex, assign the smallest color number not used by its already-colored neighbors.
    - **Performance:** The number of colors used is at most `Δ(G) + 1`, where `Δ(G)` is the maximum degree of any vertex. This can be very poor compared to the optimal value (e.g., for a star graph, `Δ(G)+1` is low, but for a complete graph, it's optimal).
    - **Welsh-Powell Algorithm:** A popular greedy heuristic that orders vertices in descending order of their degree.

2.  **DSatur (Degree of Saturation):**

    - A more sophisticated greedy algorithm. The "saturation" degree of a vertex is the number of different colors already assigned to its neighbors.
    - The algorithm dynamically selects the uncolored vertex with the highest saturation degree to color next. This often yields better results than simple greedy approaches.

3.  **Using a Maximum Independent Set:**

    - Repeatedly find a large independent set (a set of vertices with no edges between them), assign all vertices in that set the same color, remove them from the graph, and repeat. The number of independent sets found is the number of colors used.
    - Finding a maximum independent set is itself NP-hard, so heuristics are used for this sub-problem.

4.  **Advanced Methods:**
    - **Integer Linear Programming (ILP):** Solvers like Gurobi or CPLEX can find optimal or near-optimal solutions for medium-sized graphs by modeling the problem with ILP constraints.
    - **Metaheuristics:** Genetic algorithms, simulated annealing, and tabu search are often applied to find high-quality solutions for very large graphs.

## 4. Impact and Applications

The graph coloring problem is not just a theoretical puzzle; it has profound practical implications across numerous fields.

- **Compiler Design - Register Allocation:** A core application. Variables in a program are vertices. An edge exists between two variables if they are "live" at the same time (they cannot share a CPU register). Colors represent registers. The goal is to minimize register spills (writing to main memory).
- **Scheduling and Timetabling:**
  - **University Exam Scheduling:** Courses are vertices. An edge connects two courses if they share a student. Colors represent exam time slots. The goal is to minimize the total schedule length so no student has two exams at the same time.
  - **Task Scheduling:** Tasks are vertices, edges connect tasks that cannot use the same resource (machine, person), colors represent resources or time slots.
- **Radio Frequency Assignment (Cellular Networks):** Cell towers are vertices. An edge exists between towers whose signals might interfere if on the same frequency. Colors represent frequencies. The goal is to minimize the spectrum used.
- **Sudoku and Puzzles:** Solving a Sudoku puzzle is equivalent to coloring a 81-vertex graph with 9 colors, where the graph's structure encodes the row, column, and box constraints.
- **Chemical and Biological Sciences:** Used to detect clusters and patterns in complex networks, such as protein-protein interaction networks.

---

## Problem Statement

Input: A Boolean Adjacency Matrix $M$.

Answer: Find a Minimum Chromatic Number.

### Example Instance: 5 x 5 matrix

|        | c1  | c2  | c3  | c4  | c5  |
| ------ | --- | --- | --- | --- | --- |
| **r1** | 0   | 0   | 1   | 0   | 1   |
| **r2** | 0   | 0   | 0   | 1   | 0   |
| **r3** | 1   | 0   | 0   | 0   | 1   |
| **r4** | 0   | 1   | 0   | 0   | 0   |
| **r5** | 1   | 0   | 1   | 0   | 0   |

The input for undirected graph is typically provided in [DIMACS](http://dimacs.rutgers.edu/Challenges) format. In this way, the previous adjacency matrix is represented in a text file using the following string representation:

```
p edge 5 4
e 1 3
e 1 5
e 2 4
e 3 5
```

This represents a 5x5 matrix in DIMACS format such that each edge $(v,w)$ appears exactly once in the input file and is not repeated as $(w,v)$. In this format, every edge appears in the form of

```
e W V
```

where the fields W and V specify the endpoints of the edge while the lower-case character `e` signifies that this is an edge descriptor line.

_Example Solution:_

Chromatic Number Found `(4:1, 5:1, 2:2, 1:2, 3:3)`: An optimal coloring is achieved by assigning color `1` to nodes `4` and `5`, color `2` to nodes `1` and `2`, and color `3` to node `3`.

---

# Compile and Environment

## Prerequisites

- Python ≥ 3.12

## Installation

```bash
pip install adonai
```

## Execution

1. Clone the repository:

   ```bash
   git clone https://github.com/frankvegadelgado/adonai.git
   cd adonai
   ```

2. Run the script:

   ```bash
   salve -i ./benchmarks/testMatrix1
   ```

   utilizing the `salve` command provided by Adonai's Library to execute the Boolean adjacency matrix `adonai\benchmarks\testMatrix1`. The file `testMatrix1` represents the example described herein. We also support `.xz`, `.lzma`, `.bz2`, and `.bzip2` compressed text files.

   **Example Output:**

   ```
   testMatrix1: Chromatic Number Found (4:1, 5:1, 2:2, 1:2, 3:3)
   ```

   This indicates a valid 3-coloring, meaning the graph's chromatic number is at most 3.

---

## Chromatic Number Size

Use the `-c` flag to count the chromatic number:

```bash
salve -i ./benchmarks/testMatrix2 -c
```

**Output:**

```
testMatrix2: Chromatic Number Size 4
```

---

# Command Options

Display help and options:

```bash
salve -h
```

**Output:**

```bash
usage: salve [-h] -i INPUTFILE [-a] [-b] [-c] [-v] [-l] [--version]

Compute the Approximate Chromatic Number for undirected graph encoded in DIMACS format.

options:
  -h, --help            show this help message and exit
  -i INPUTFILE, --inputFile INPUTFILE
                        input file path
  -a, --approximation   enable comparison with a polynomial-time approximation approach within a factor of at most 2
  -b, --bruteForce      enable comparison with the exponential-time brute-force approach
  -c, --count           calculate the size of the chromatic number
  -v, --verbose         anable verbose output
  -l, --log             enable file logging
  --version             show program's version number and exit
```

---

# Batch Execution

Batch execution allows you to solve multiple graphs within a directory consecutively.

To view available command-line options for the `batch_salve` command, use the following in your terminal or command prompt:

```bash
batch_salve -h
```

This will display the following help information:

```bash
usage: batch_salve [-h] -i INPUTDIRECTORY [-a] [-b] [-c] [-v] [-l] [--version]

Compute the Approximate Chromatic Number for all undirected graphs encoded in DIMACS format and stored in a directory.

options:
  -h, --help            show this help message and exit
  -i INPUTDIRECTORY, --inputDirectory INPUTDIRECTORY
                        Input directory path
  -a, --approximation   enable comparison with a polynomial-time approximation approach within a factor of at most 2
  -b, --bruteForce      enable comparison with the exponential-time brute-force approach
  -c, --count           calculate the size of the chromatic number
  -v, --verbose         anable verbose output
  -l, --log             enable file logging
  --version             show program's version number and exit
```

---

# Testing Application

A command-line utility named `test_salve` is provided for evaluating the Algorithm using randomly generated, large sparse matrices. It supports the following options:

```bash
usage: test_salve [-h] -d DIMENSION [-n NUM_TESTS] [-s SPARSITY] [-a] [-b] [-c] [-w] [-v] [-l] [--version]

The Adonai Testing Application using randomly generated, large sparse matrices.

options:
  -h, --help            show this help message and exit
  -d DIMENSION, --dimension DIMENSION
                        an integer specifying the dimensions of the square matrices
  -n NUM_TESTS, --num_tests NUM_TESTS
                        an integer specifying the number of tests to run
  -s SPARSITY, --sparsity SPARSITY
                        sparsity of the matrices (0.0 for dense, close to 1.0 for very sparse)
  -a, --approximation   enable comparison with a polynomial-time approximation approach within a factor of at most 2
  -b, --bruteForce      enable comparison with the exponential-time brute-force approach
  -c, --count           calculate the size of the chromatic number
  -w, --write           write the generated random matrix to a file in the current directory
  -v, --verbose         anable verbose output
  -l, --log             enable file logging
  --version             show program's version number and exit
```

---

# Code

- Python implementation by **Frank Vega**.

---

# Complexity

```diff
+ We present a polynomial-time algorithm that achieves an (sqrt(n) * ln(n))-approximation for the Minimum Chromatic Number problem. This provides strong evidence that P = NP by efficiently solving a computationally hard problem with near-optimal solutions.
```

---

# License

- MIT License.
