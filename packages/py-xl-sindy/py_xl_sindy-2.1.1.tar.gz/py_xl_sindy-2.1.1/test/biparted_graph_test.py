import xlsindy

# Example usage.
if __name__ == "__main__":
    x_names = ["Variable_X1", "Variable_X2", "Variable_X3", "Variable_X4", "Variable_X5"]
    b_names = ["B_Group_A", "B_Group_B", "B_Group_C"]
    
    edges = [
        ("Variable_X3", "B_Group_A"),
        ("Variable_X4", "B_Group_A"),
        ("Variable_X2", "B_Group_B"),
        ("Variable_X5", "B_Group_B"),
        ("Variable_X1", "B_Group_C"),
        ("Variable_X3", "B_Group_C")
    ]
    
    x_sol_indices = [2, 4]
    
    xlsindy.render.plot_bipartite_graph_svg(x_names, b_names, edges, x_sol_indices, output_file="fancy_bipartite_graph.svg")
