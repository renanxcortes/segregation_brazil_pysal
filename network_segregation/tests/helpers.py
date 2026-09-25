import networkx as nx


def grid_graph(nx_: int, ny: int, spacing: float = 100.0, origin=(0.0, 0.0)) -> nx.MultiGraph:
    """Projected lattice street graph: nodes (i, j) at origin + spacing*(i, j)."""
    base = nx.grid_2d_graph(nx_, ny)
    G = nx.MultiGraph()
    G.graph["crs"] = "EPSG:31982"
    for (i, j) in base.nodes:
        G.add_node((i, j), x=origin[0] + i * spacing, y=origin[1] + j * spacing)
    for u, v in base.edges:
        G.add_edge(u, v, length=spacing)
    return G
