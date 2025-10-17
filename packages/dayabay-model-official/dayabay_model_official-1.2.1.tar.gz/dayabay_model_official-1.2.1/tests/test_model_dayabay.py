from dag_modelling.core import Graph, NodeStorage
from dag_modelling.plot.graphviz import GraphDot

from dayabay_model_official import model_dayabay


def test_model_dayabay(output_path: str):
    model = model_dayabay()

    graph = model.graph
    storage = model.storage

    if not graph.closed:
        print("Nodes")
        print(storage("nodes").to_table(truncate=True))
        print("Outputs")
        print(storage("outputs").to_table(truncate=True))
        print("Not connected inputs")
        print(storage("inputs").to_table(truncate=True))

        plot_graph(graph, storage, output_path=output_path)
        return

    print(storage.to_table(truncate=True))
    if len(storage("inputs")) > 0:
        print("Not connected inputs")
        print(storage("inputs").to_table(truncate=True))

    storage.to_datax(f"{output_path}/dayabay_v0_data.tex")
    plot_graph(graph, storage, output_path=output_path)


def plot_graph(graph: Graph, storage: NodeStorage, output_path: str) -> None:
    GraphDot.from_graph(graph, show="all").savegraph(f"{output_path}/dayabay_v0.dot")
    GraphDot.from_graph(
        graph,
        show="all",
        filter={
            "reactor": [0],
            "detector": [0, 1],
            "isotope": [0],
            "period": [0],
            "background": [0],
        },
    ).savegraph(f"{output_path}/dayabay_v0_reduced.dot")
    GraphDot.from_node(
        storage["nodes.statistic.nuisance.all"],
        show="all",
        min_depth=-1,
        keep_direction=True,
    ).savegraph(f"{output_path}/dayabay_v0_nuisance.dot")
    GraphDot.from_output(
        storage["outputs.edges.energy_evis"],
        show="all",
        min_depth=-3,
        keep_direction=True,
    ).savegraph(f"{output_path}/dayabay_v0_top.dot")
