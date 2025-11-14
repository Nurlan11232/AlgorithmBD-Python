# backend/graph_build/build_graph.py
from backend.data.osm_loader import OSMRoadLoader, load_ulaanbaatar_roads
from backend.graphs.graph import Graph
def build_graph_from_shapefile(filepath: str,
                                mode: str = 'ulaanbaatar',
                                strict_filters: bool = True) -> Graph:
    if mode == 'ulaanbaatar':
        print("🏙️  Улаанбаатар горооны замуудыг ачаалж байна...")
        return load_ulaanbaatar_roads(filepath, strict=strict_filters)
    elif mode == 'all':
        # Бүх замууд
        print("🌍 Бүх замуудыг ачаалж байна...")
        loader = OSMRoadLoader(
            use_access_filter=strict_filters,
            use_surface_filter=strict_filters,
            apply_penalties=True
        )
        return loader.load_roads(filepath)

    else:
        raise ValueError(f"Тодорхойгүй mode: {mode}. 'ulaanbaatar' эсвэл 'all' байх ёстой")
def build_custom_graph(filepath: str,
                      road_types: list = None,
                      bbox: tuple = None,
                      use_access: bool = True,
                      use_surface: bool = True,
                      apply_penalties: bool = True) -> Graph:

    loader = OSMRoadLoader(
        use_access_filter=use_access,
        use_surface_filter=use_surface,
        apply_penalties=apply_penalties
    )

    return loader.load_roads(filepath, road_types=road_types, bbox=bbox)

if __name__ == "__main__":
    import sys
    # Командын мөрөөс аргумент авах
    if len(sys.argv) > 1:
        shp_path = sys.argv[1]
    else:
        shp_path = 'C:/Users/Nurlan/PyCharmMiscProject/backend/data/gis_osm_roads_free_1.shp'
    print("\n📍 Вариант 2: Бүх замууд (relaxed mode)")
    graph2 = build_graph_from_shapefile(shp_path, mode='all', strict_filters=False)
    print(f"All roads (relaxed): {graph2.node_count:,} nodes, {graph2.edge_count:,} edges")
