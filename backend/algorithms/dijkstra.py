# backend/algorithms/dijkstra.py
import heapq
from typing import Tuple, List, Any
from backend.graphs.graph import Graph
def dijkstra(graph: Graph, start: str, end: str) -> tuple[list[Any], float] | tuple[None, float]:
    if start not in graph.nodes or end not in graph.nodes:
        return None, float('inf')
    distances = {node: float('inf') for node in graph.nodes}
    previous = {node: None for node in graph.nodes}
    distances[start] = 0.0
    pq = [(0.0, start)]
    visited = set()
    while pq:
        dist_u, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        if u == end:
            # recover path
            path = []
            v = end
            while v is not None:
                path.append(v)
                v = previous[v]
            return path[::-1], distances[end]
        for neighbor, weight in graph.get_neighbors(u):
            alt = dist_u + weight
            if alt < distances[neighbor]:
                distances[neighbor] = alt
                previous[neighbor] = u
                heapq.heappush(pq, (alt, neighbor))
    return None, float('inf')