from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.engine.checkpointer import PostgresCheckpointer
from app.engine.nodes import GraphState, generate_node, retrieve_node, validate_node


def build_rag_graph(checkpointer: PostgresCheckpointer) -> CompiledStateGraph:
    graph: StateGraph = StateGraph(GraphState)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_node("validate", validate_node)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", "validate")
    graph.add_edge("validate", END)

    return graph.compile(checkpointer=checkpointer)
