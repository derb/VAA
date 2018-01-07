import random
import sys


def save_graph(edges):
    graph_str = "graph generated_Graph {\n"
    for i in range(len(edges)):
        current_edge = edges[i]
        graph_str += str(current_edge[0]) + " -- " + str(current_edge[1]) + ";\n"
    graph_str += "}"

    graph_file = open("gen_graph.dot", "w")
    graph_file.write(graph_str)
    graph_file.close()


def generate_random_edge(n):
    i = random.randint(1, n)
    j = random.randint(1, n)
    if i < j:
        return i, j
    elif i > j:
        return j, i
    else:
        return generate_random_edge(n)


def remove_duplicates(edge_list):
    edge_list.sort(key=lambda x: x[0])
    tmp_list = []
    for i in range(len(edge_list)):
        found = False
        current_element = edge_list[i]
        for j in range(len(tmp_list)):
            tmp_element = tmp_list[j]
            if current_element == tmp_element:
                found = True
        if not found:
            tmp_list.append(current_element)
    return tmp_list


def generate_graph(n, m):
    edges = []
    for i in range(1, n + 1):
        j = random.randint(1, n)
        while i == j:
            j = random.randint(1, n)
        if i < j:
            edges.append((i, j))
        if i > j:
            edges.append((j,i))

    edges = remove_duplicates(edges)

    while len(edges) < m:
        possible_edge = generate_random_edge(n)
        is_edge = False
        for i in range(len(edges)):
            if edges[i] == possible_edge:
                is_edge = True
                break
        if not is_edge:
            edges.append(possible_edge)

    edges.sort(key=lambda x: x[0])
    print edges
    save_graph(edges)


def main(argv):
    if len(argv) < 3:
        print "missing arguments\n Input:  n m"
        sys.exit(1)
    n = int(sys.argv[1])
    m = int(sys.argv[2])
    if n >= m:
        print "required: n < m"
        sys.exit(1)
    generate_graph(n, m)


if __name__ == "__main__":
    main(sys.argv)
