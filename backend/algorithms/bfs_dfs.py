# backend/algorithms/bfs_dfs.py
from collections import deque
from typing import Tuple, List
from backend.graphs.graph import Graph
def bfs(graph: Graph, start: str, end: str) -> Tuple[List[str], int]:
    if start not in graph.nodes or end not in graph.nodes:
        return None, None
    visited = {start}
    queue = deque([(start, [start])])
    while queue:
        current, path = queue.popleft()
        if current == end:
            return path, len(path) - 1
        for neighbor, _ in graph.get_neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return None, None
def dfs_all_paths(graph: Graph, start: str, end: str,
                  max_depth: int = 100, max_paths: int = 100) -> List[List[str]]:
    if start not in graph.nodes or end not in graph.nodes:
        return []
    all_paths = []
    def dfs(curr, path, visited):
        if len(all_paths) >= max_paths:
            return

        if len(path) > max_depth:
            return
        # Зорилтот цэг рүү очсон
        if curr == end:
            all_paths.append(path.copy())
            return
        # Хөршүүдийг эргэх
        for neighbor, _ in graph.get_neighbors(curr):
            if neighbor not in visited:
                visited.add(neighbor)
                path.append(neighbor)
                dfs(neighbor, path, visited)
                path.pop()
                visited.remove(neighbor)

    # DFS эхлүүлэх
    dfs(start, [start], {start})

    return all_paths


def dfs_iterative_deepening(graph: Graph, start: str, end: str,
                            max_depth: int = 200) -> List[List[str]]:
    if start not in graph.nodes or end not in graph.nodes:
        return []
    all_paths = []
    for depth_limit in [10, 20, 40, 80, max_depth]:
        # ✅ max_paths параметр нэмсэн
        paths = dfs_all_paths(graph, start, end,
                              max_depth=depth_limit,
                              max_paths=50)

        if paths:
            all_paths.extend(paths)
            # Хангалттай зам олдвол зогсоох
            if len(all_paths) >= 10:
                break
    unique_paths = []
    seen = set()
    for path in all_paths:
        path_tuple = tuple(path)
        if path_tuple not in seen:
            seen.add(path_tuple)
            unique_paths.append(path)
    return unique_paths