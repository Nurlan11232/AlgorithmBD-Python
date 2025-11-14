# backend/api/main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import logging
import time
from datetime import datetime
from backend.graph_build.build_graph import build_graph_from_shapefile
from backend.algorithms.bfs_dfs import bfs, dfs_all_paths
from backend.algorithms.dijkstra import dijkstra
from backend.graphs.graph import Graph
# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Улаанбаатар замын алгоритм API",
    description="OSM өгөгдөл дээр суурилсан замын хайлтын алгоритм",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global
GRAPH: Optional[Graph] = None
GRAPH_LOAD_TIME: Optional[datetime] = None
SHP_PATH = "backend/data/gis_osm_roads_free_1.shp"


@app.on_event("startup")
async def startup_event():
    """График ачаалах"""
    global GRAPH, GRAPH_LOAD_TIME

    logger.info("=" * 60)
    logger.info("FastAPI сервер эхэлж байна...")
    logger.info("=" * 60)

    try:
        start_time = time.time()
        logger.info(f"📂 Shapefile: {SHP_PATH}")

        GRAPH = build_graph_from_shapefile(SHP_PATH, mode='ulaanbaatar', strict_filters=True)
        GRAPH_LOAD_TIME = datetime.now()

        elapsed = time.time() - start_time
        stats = GRAPH.get_stats()

        logger.info(" График амжилттай ачаалагдлаа!")
        logger.info(f" Nodes: {stats['nodes']:,}")
        logger.info(f" Edges: {stats['edges']:,}")
        logger.info(f"Хугацаа: {elapsed:.2f}с")

    except Exception as e:
        logger.error(f"Алдаа: {e}")
        GRAPH = None
def find_nearest_node(graph: Graph, lat: float, lon: float, max_distance_km: float = 10.0) -> Optional[str]:
    result = graph.find_nearest_node(lat, lon, max_distance_km)
    return result[0] if result else None


def get_path_coordinates(graph: Graph, path: List[str]) -> List[List[float]]:
    """Замын координат"""
    coords = []
    for node_id in path:
        node_coords = graph.get_node_coords(node_id)
        if node_coords:
            lat, lon = node_coords
            coords.append([lat, lon])
    return coords


def calculate_path_distance(graph: Graph, path: List[str]) -> float:
    """Замын зай"""
    total_dist = 0.0
    for i in range(len(path) - 1):
        edge_meta = graph.get_edge_metadata(path[i], path[i + 1])
        if edge_meta:
            total_dist += edge_meta.distance
    return total_dist

@app.get("/")
async def root():
    """Үндсэн"""
    if GRAPH is None:
        return {"message": "График ачаалагдаагүй", "status": "error"}

    stats = GRAPH.get_stats()
    return {
        "message": "✅ API ажиллаж байна",
        "version": "2.0.0",
        "nodes": stats['nodes'],
        "edges": stats['edges'],
    }


@app.get("/health")
async def health_check():
    if GRAPH is None:
        raise HTTPException(status_code=503, detail="График ачаалагдаагүй")

    return {
        "status": "healthy",
        "nodes": GRAPH.node_count,
        "edges": GRAPH.edge_count
    }


@app.get("/graph/stats")
async def get_graph_stats():
    """Статистик"""
    if GRAPH is None:
        raise HTTPException(status_code=503, detail="График ачаалагдаагүй")

    return GRAPH.get_stats()


@app.get("/graph/bbox")
async def get_graph_bbox():
    """Bbox"""
    if GRAPH is None:
        raise HTTPException(status_code=503, detail="График ачаалагдаагүй")

    min_lat, max_lat, min_lon, max_lon = GRAPH.get_bbox()
    return {
        "bbox": {"min_lat": min_lat, "max_lat": max_lat, "min_lon": min_lon, "max_lon": max_lon},
        "center": {"lat": (min_lat + max_lat) / 2, "lon": (min_lon + max_lon) / 2}
    }

@app.get("/bfs")
async def route_bfs(
        lat1: float = Query(...),
        lon1: float = Query(...),
        lat2: float = Query(...),
        lon2: float = Query(...)
):
    """BFS"""
    if GRAPH is None:
        raise HTTPException(status_code=503, detail="График ачаалагдаагүй")

    start_time = time.time()

    start_node = find_nearest_node(GRAPH, lat1, lon1)
    end_node = find_nearest_node(GRAPH, lat2, lon2)

    if not start_node or not end_node:
        raise HTTPException(status_code=404, detail="Орой олдсонгүй")

    path, steps = bfs(GRAPH, start_node, end_node)
    compute_time = (time.time() - start_time) * 1000

    if path is None:
        return {"success": False, "error": "Зам олдсонгүй"}

    distance = calculate_path_distance(GRAPH, path)

    return {
        "success": True,
        "algorithm": "bfs",
        "path": path,
        "steps": steps,
        "distance_km": distance,
        "computeTime": f"{compute_time / 1000:.3f}"
    }


@app.get("/dijkstra")
async def route_dijkstra(
        lat1: float = Query(...),
        lon1: float = Query(...),
        lat2: float = Query(...),
        lon2: float = Query(...)
):
    """Dijkstra"""
    if GRAPH is None:
        raise HTTPException(status_code=503, detail="График ачаалагдаагүй")

    start_time = time.time()

    start_node = find_nearest_node(GRAPH, lat1, lon1)
    end_node = find_nearest_node(GRAPH, lat2, lon2)

    if not start_node or not end_node:
        raise HTTPException(status_code=404, detail="Орой олдсонгүй")

    path, total_weight = dijkstra(GRAPH, start_node, end_node)
    compute_time = (time.time() - start_time) * 1000

    if path is None:
        return {"success": False, "error": "Зам олдсонгүй"}

    distance = calculate_path_distance(GRAPH, path)

    return {
        "success": True,
        "algorithm": "dijkstra",
        "path": path,
        "distance_km": distance,
        "computeTime": f"{compute_time / 1000:.3f}"
    }


@app.get("/dfs")
async def route_dfs(
        lat1: float = Query(...),
        lon1: float = Query(...),
        lat2: float = Query(...),
        lon2: float = Query(...),
        max_depth: int = Query(200)
):
    """DFS - бүх замууд"""
    if GRAPH is None:
        raise HTTPException(status_code=503, detail="График ачаалагдаагүй")

    start_time = time.time()

    # Хамгийн ойр node олох
    start_node = find_nearest_node(GRAPH, lat1, lon1)
    end_node = find_nearest_node(GRAPH, lat2, lon2)

    if not start_node or not end_node:
        raise HTTPException(status_code=404, detail="Орой олдсонгүй")

    print(f" DFS: {start_node} → {end_node}")

    # ========== DFS хэрэгжүүлэлт ==========
    all_paths = []
    max_paths = 3

    def dfs_search(curr, path, visited, depth_limit):
        """DFS рекурсив функц"""
        if len(all_paths) >= max_paths:
            return
        if len(path) > depth_limit:
            return
        if curr == end_node:
            all_paths.append(path.copy())
            return

        for neighbor, _ in GRAPH.get_neighbors(curr):
            if neighbor not in visited:
                visited.add(neighbor)
                path.append(neighbor)
                dfs_search(neighbor, path, visited, depth_limit)
                path.pop()
                visited.remove(neighbor)

    # Гүнийг аажмаар нэмэгдүүлэх
    for depth_limit in [20, 50, 100, max_depth]:
        dfs_search(start_node, [start_node], {start_node}, depth_limit)
        if len(all_paths) >= 3:
            break

    compute_time = (time.time() - start_time) * 1000

    # Зам олдсонгүй
    if not all_paths:
        print("DFS: Зам олдсонгүй")
        return {
            "success": False,
            "error": "Зам олдсонгүй. Цэгүүдийг илүү ойр сонгоно уу.",
            "paths": [],
            "path_count": 0
        }

    # Уртаар эрэмбэлэх
    all_paths.sort(key=len)

    print(f"DFS: {len(all_paths)} зам олдлоо")

    # ========== КООРДИНАТУУД ҮҮСГЭХ ==========
    all_paths_coords = []
    for path in all_paths[:3]:  # Эхний 3 замыг авах
        coords = []
        for node_id in path:
            node_coords = GRAPH.get_node_coords(node_id)
            if node_coords:
                lat, lon = node_coords
                coords.append([lat, lon])

        # Зай тооцоолох
        distance = 0.0
        for i in range(len(path) - 1):
            edge_meta = GRAPH.get_edge_metadata(path[i], path[i + 1])
            if edge_meta:
                distance += edge_meta.distance

        all_paths_coords.append({
            "path": path,
            "coordinates": coords,
            "distance_km": distance,
            "nodes": len(path)
        })
    print(f"📊 all_paths_coords: {len(all_paths_coords)} зам")
    shortest_path = all_paths[0]
    shortest_distance = all_paths_coords[0]["distance_km"]

    return {
        "success": True,
        "algorithm": "dfs",
        "path": shortest_path,
        "paths": all_paths[:3],
        "all_paths_data": all_paths_coords,  # ← ЭНЭ ЧУХАЛ!
        "path_count": len(all_paths),
        "distance_km": shortest_distance,
        "computeTime": f"{compute_time / 1000:.3f}"
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)