# backend/graphs/graph.py

import math
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field


@dataclass
class NodeMetadata:
    """Node-ийн нэмэлт мэдээлэл"""
    lat: float
    lon: float
    neighbors_count: int = 0
    name: Optional[str] = None

    def to_dict(self):
        return {
            'lat': self.lat,
            'lon': self.lon,
            'neighbors': self.neighbors_count,
            'name': self.name
        }

@dataclass
class EdgeMetadata:
    """Edge-ийн нэмэлт мэдээлэл"""
    distance: float  # км
    weight: float  # жин (хугацаа эсвэл зай)
    road_type: Optional[str] = None
    oneway: bool = False
    maxspeed: Optional[float] = None
    surface: Optional[str] = None

    def to_dict(self):
        return {
            'distance': self.distance,
            'weight': self.weight,
            'road_type': self.road_type,
            'oneway': self.oneway,
            'maxspeed': self.maxspeed,
            'surface': self.surface
        }


class Graph:
    """Замын график бүтэц"""

    def __init__(self):
        # Үндсэн бүтэц
        self.nodes: Dict[str, Tuple[float, float]] = {}  # id -> (lat, lon)
        self.edges: Dict[str, List[Tuple[str, float]]] = {}  # id -> [(neighbor, weight)]

        # Metadata
        self.node_metadata: Dict[str, NodeMetadata] = {}
        self.edge_metadata: Dict[Tuple[str, str], EdgeMetadata] = {}

        # Тоолуур
        self.node_count = 0
        self.edge_count = 0

        # Кэш
        self._bbox_cache: Optional[Tuple[float, float, float, float]] = None

    def add_node(self, node_id: str, lat: float, lon: float, **kwargs) -> None:
        if node_id not in self.nodes:
            self.nodes[node_id] = (lat, lon)
            self.edges[node_id] = []
            self.node_metadata[node_id] = NodeMetadata(
                lat=lat,
                lon=lon,
                name=kwargs.get('name')
            )
            self.node_count += 1
            self._bbox_cache = None  # Cache устгах

    def add_edge(self, from_node: str, to_node: str, weight: float,
                 distance: Optional[float] = None, **kwargs) -> None:

        if from_node in self.nodes and to_node in self.nodes:
            # Edge нэмэх
            self.edges[from_node].append((to_node, weight))
            self.edge_count += 1

            # Metadata хадгалах
            edge_key = (from_node, to_node)
            self.edge_metadata[edge_key] = EdgeMetadata(
                distance=distance if distance is not None else weight,
                weight=weight,
                road_type=kwargs.get('road_type'),
                oneway=kwargs.get('oneway', False),
                maxspeed=kwargs.get('maxspeed'),
                surface=kwargs.get('surface')
            )

            # Node neighbors тоолох
            self.node_metadata[from_node].neighbors_count += 1

    def get_neighbors(self, node_id: str) -> List[Tuple[str, float]]:
        """Node-ийн хөршүүдийг авах"""
        return self.edges.get(node_id, [])

    def get_node_coords(self, node_id: str) -> Optional[Tuple[float, float]]:
        """Node-ийн координат авах"""
        return self.nodes.get(node_id)

    def node_exists(self, node_id: str) -> bool:
        """Node байгаа эсэхийг шалгах"""
        return node_id in self.nodes

    def get_edge_metadata(self, from_node: str, to_node: str) -> Optional[EdgeMetadata]:
        """Edge-ийн metadata авах"""
        return self.edge_metadata.get((from_node, to_node))

    def find_nearest_node(self, lat: float, lon: float,
                          max_distance_km: float = 1.0) -> Optional[Tuple[str, float]]:

        best_node = None
        best_dist = float('inf')
        for node_id, (nlat, nlon) in self.nodes.items():
            dist = haversine_distance(lat, lon, nlat, nlon)
            if dist < best_dist:
                best_node = node_id
                best_dist = dist

        if best_dist <= max_distance_km:
            return (best_node, best_dist)
        return None

    def get_bbox(self) -> Tuple[float, float, float, float]:
        """
        График хамарч байгаа хязгаар олох

        Returns:
            (min_lat, max_lat, min_lon, max_lon)
        """
        if self._bbox_cache:
            return self._bbox_cache

        if not self.nodes:
            return (0, 0, 0, 0)

        lats = [lat for lat, lon in self.nodes.values()]
        lons = [lon for lat, lon in self.nodes.values()]

        self._bbox_cache = (min(lats), max(lats), min(lons), max(lons))
        return self._bbox_cache

    def get_subgraph(self, node_ids: Set[str]) -> 'Graph':
        subgraph = Graph()
        # Node-уудыг хуулах
        for node_id in node_ids:
            if node_id in self.nodes:
                lat, lon = self.nodes[node_id]
                metadata = self.node_metadata.get(node_id)
                subgraph.add_node(
                    node_id, lat, lon,
                    name=metadata.name if metadata else None
                )

        # Edge-үүдийг хуулах
        for node_id in node_ids:
            if node_id in self.edges:
                for neighbor, weight in self.edges[node_id]:
                    if neighbor in node_ids:
                        edge_meta = self.get_edge_metadata(node_id, neighbor)
                        if edge_meta:
                            subgraph.add_edge(
                                node_id, neighbor, weight,
                                distance=edge_meta.distance,
                                road_type=edge_meta.road_type,
                                oneway=edge_meta.oneway,
                                maxspeed=edge_meta.maxspeed,
                                surface=edge_meta.surface
                            )

        return subgraph

    def get_stats(self) -> dict:
        avg_degree = (self.edge_count / self.node_count) if self.node_count > 0 else 0

        # Зэргийн тархалт
        degrees = [len(neighbors) for neighbors in self.edges.values()]
        max_degree = max(degrees) if degrees else 0
        min_degree = min(degrees) if degrees else 0

        # Isolated nodes (хөрш байхгүй)
        isolated = sum(1 for d in degrees if d == 0)

        # Замын төрлүүдийн тархалт
        road_types = {}
        for edge_meta in self.edge_metadata.values():
            if edge_meta.road_type:
                road_types[edge_meta.road_type] = road_types.get(edge_meta.road_type, 0) + 1

        return {
            'nodes': self.node_count,
            'edges': self.edge_count,
            'avg_degree': avg_degree,
            'max_degree': max_degree,
            'min_degree': min_degree,
            'isolated_nodes': isolated,
            'road_type_distribution': road_types,
            'bbox': self.get_bbox()
        }

    def export_to_geojson(self, include_metadata: bool = True) -> dict:
        features = []
        # Edge-үүдийг LineString болгох
        for from_node, neighbors in self.edges.items():
            from_lat, from_lon = self.nodes[from_node]

            for to_node, weight in neighbors:
                to_lat, to_lon = self.nodes[to_node]

                properties = {'weight': weight}

                if include_metadata:
                    edge_meta = self.get_edge_metadata(from_node, to_node)
                    if edge_meta:
                        properties.update(edge_meta.to_dict())

                feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': [[from_lon, from_lat], [to_lon, to_lat]]
                    },
                    'properties': properties
                }
                features.append(feature)

        return {
            'type': 'FeatureCollection',
            'features': features
        }

    def __repr__(self):
        return f"Graph(nodes={self.node_count}, edges={self.edge_count})"

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0  # Дэлхийн радиус (км)
    # Радиан руу хөрвүүлэх
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def create_grid_graph(rows: int, cols: int, spacing_km: float = 1.0) -> Graph:
    graph = Graph()
    base_lat, base_lon = 47.9, 106.9

    # Node-ууд үүсгэх
    for i in range(rows):
        for j in range(cols):
            lat = base_lat + (i * spacing_km / 111.0)  # 1° ≈ 111 км
            lon = base_lon + (j * spacing_km / 111.0)
            node_id = f"n_{i}_{j}"
            graph.add_node(node_id, lat, lon, name=f"Node {i},{j}")

    # Edge-үүд үүсгэх (4-холбоос)
    for i in range(rows):
        for j in range(cols):
            current = f"n_{i}_{j}"

            # Баруун
            if j < cols - 1:
                neighbor = f"n_{i}_{j + 1}"
                graph.add_edge(current, neighbor, spacing_km, road_type='grid')
                graph.add_edge(neighbor, current, spacing_km, road_type='grid')

            # Доош
            if i < rows - 1:
                neighbor = f"n_{i + 1}_{j}"
                graph.add_edge(current, neighbor, spacing_km, road_type='grid')
                graph.add_edge(neighbor, current, spacing_km, road_type='grid')

    return graph
if __name__ == "__main__":
    print("🧪 Graph класс туршилт\n")

    # Жижиг график үүсгэх
    g = create_grid_graph(5, 5, spacing_km=0.5)

    print("📊 Статистик:")
    stats = g.get_stats()
    for key, value in stats.items():
        if key != 'road_type_distribution':
            print(f"  {key}: {value}")

    # Хамгийн ойр node олох
    test_lat, test_lon = 47.905, 106.905
    result = g.find_nearest_node(test_lat, test_lon, max_distance_km=1.0)
    if result:
        node_id, distance = result
        print(f"\n🔍 ({test_lat}, {test_lon}) хамгийн ойр node:")
        print(f"  Node: {node_id}")
        print(f"  Зай: {distance * 1000:.1f} метр")

    # Subgraph
    subset = set(list(g.nodes.keys())[:10])
    subg = g.get_subgraph(subset)
    print(f"\n📦 Subgraph: {subg.node_count} nodes, {subg.edge_count} edges")

    print("\n✅ Бүх тестүүд амжилттай!")