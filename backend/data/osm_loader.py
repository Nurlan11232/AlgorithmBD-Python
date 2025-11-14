
import geopandas as gpd
from shapely.geometry import LineString
from backend.graphs.graph import Graph, haversine_distance
def _safe_speed(value, default=50):
    try:
        if value in [None, 0, "0", "unknown", "none", "nan", ""]:
            return default
        return float(value)
    except Exception:
        return default
def _speed_factor(road_type: str, maxspeed: float) -> float:
    """замын төрөл ба хурдны хязгаараас хамаарсан коэффициент"""
    factors = {
        "motorway": 1.0,
        "trunk": 0.9,
        "primary": 0.8,
        "secondary": 0.7,
        "tertiary": 0.6,
        "residential": 0.5,
        "service": 0.4,
        "unclassified": 0.5,
    }
    base = factors.get(road_type, 0.5)
    return base * (maxspeed / 100.0)

class OSMRoadLoader:
    def __init__(self, use_access_filter=True, use_surface_filter=True, apply_penalties=True):
        self.use_access_filter = use_access_filter
        self.use_surface_filter = use_surface_filter
        self.apply_penalties = apply_penalties

    def load_roads(self, shp_file: str, road_types=None, bbox=None) -> Graph:
        print(f"OSM өгөгдөл ачаалж байна: {shp_file}")

        try:
            layers = gpd.list_layers(shp_file)
            layer_name = None
            for lyr in layers["name"]:
                if "road" in lyr or "roads" in lyr:
                    layer_name = lyr
                    break
            if not layer_name:
                layer_name = layers["name"].iloc[0]
            print(f" Layer: {layer_name}")

            gdf = gpd.read_file(shp_file, layer=layer_name)
            print(f" Нийт {len(gdf)} замын мөр ачааллаа")
        except Exception as e:
            print(f"❌Shapefile уншихад алдаа: {e}")
            return Graph()

        # fclass → замын төрөл шүүх
        if road_types and "fclass" in gdf.columns:
            gdf = gdf[gdf["fclass"].isin(road_types)]
            print(f"Шүүсэн: {len(gdf)} зам {road_types}")

        # bbox → газарзүйн шүүлт
        if bbox:
            min_lat, max_lat, min_lon, max_lon = bbox
            gdf = gdf.cx[min_lon:max_lon, min_lat:max_lat]
            print(f"🗺️  Хүрээгээр шүүсэн: {len(gdf)} зам")

        # access, surface, bridge/tunnel гэх мэт
        if self.use_access_filter and "access" in gdf.columns:
            gdf = gdf[gdf["access"].isin(["yes", "permissive", ""]) | gdf["access"].isna()]
            print(f"🚗 Access filter хэрэглэсэн: {len(gdf)} мөр")

        if self.use_surface_filter and "surface" in gdf.columns:
            good_surfaces = ["paved", "asphalt", "concrete", "cement"]
            gdf = gdf[gdf["surface"].isin(good_surfaces) | gdf["surface"].isna()]
            print(f"🛣️  Surface filter хэрэглэсэн: {len(gdf)} мөр")
        graph = self._build_graph(gdf)
        return graph
    def _build_graph(self, gdf) -> Graph:
        graph = Graph()
        processed = 0

        for _, row in gdf.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty or geom.geom_type != "LineString":
                continue

            coords = list(geom.coords)
            if len(coords) < 2:
                continue

            road_type = row.get("fclass", "unclassified")
            maxspeed = _safe_speed(row.get("maxspeed", 50))
            oneway = str(row.get("oneway", "no")).lower()
            bridge = str(row.get("bridge", "no")).lower()
            tunnel = str(row.get("tunnel", "no")).lower()

            # Жин тооцоолох нэмэлт үржвэр
            penalty = 1.0
            if self.apply_penalties:
                if bridge == "yes":
                    penalty *= 1.2  # гүүрэн зам → илүү үнэтэй
                if tunnel == "yes":
                    penalty *= 1.3  # нүхэн гарц → илүү үнэтэй

            # Замын сегмент бүрээр тооцоолох
            for i in range(len(coords) - 1):
                lon1, lat1 = coords[i]
                lon2, lat2 = coords[i + 1]
                n1 = f"{lat1:.6f}_{lon1:.6f}"
                n2 = f"{lat2:.6f}_{lon2:.6f}"

                graph.add_node(n1, lat1, lon1)
                graph.add_node(n2, lat2, lon2)

                # Зай
                distance = haversine_distance(lat1, lon1, lat2, lon2)

                # Хурд ба хугацаа (минут)
                actual_speed = _safe_speed(maxspeed)
                if actual_speed <= 0:
                    actual_speed = 30  # default

                travel_time = (distance / actual_speed) * 60  # минут
                weight = travel_time * penalty

                # Нэг чигийн эсэх
                graph.add_edge(n1, n2, weight)
                if oneway not in ["yes", "true", "1"]:
                    graph.add_edge(n2, n1, weight)

            processed += 1
            if processed % 5000 == 0:
                print(f"✅ Processed {processed} roads...")

        print(f"✅ Граф үүсгэлт дууслаа: {graph.node_count} орой, {graph.edge_count} ирмэг")
        return graph

def load_ulaanbaatar_roads(shp_file: str, strict=True) -> Graph:
    print("\n🚀 Улаанбаатарын замын график үүсгэж байна...")

    ub_bbox = (47.85, 48.05, 106.75, 107.10)
    important_roads = [
        "motorway", "trunk", "primary",
        "secondary", "tertiary", "residential"
    ]

    loader = OSMRoadLoader(
        use_access_filter=strict,
        use_surface_filter=strict,
        apply_penalties=True
    )

    return loader.load_roads(
        shp_file,
        road_types=important_roads,
        bbox=ub_bbox
    )

if __name__ == "__main__":
    shp_file = 'C:/Users/Nurlan/PyCharmMiscProject/backend/data/gis_osm_roads_free_1.shp'
    graph = load_ulaanbaatar_roads(shp_file, strict=True)
    print(f"🧮 Нийт орой: {graph.node_count}")
    print(f"🧩 Нийт ирмэг: {graph.edge_count}")
