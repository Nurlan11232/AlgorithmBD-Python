// frontend/js/map.js
export const map = L.map("map").setView([47.921, 106.927], 12);
// OpenStreetMap tile layer нэмэх
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

// Layer хувьсагчид
let routeLayer = null;
let startMarker = null;
let endMarker = null;
let allRouteLayers = [];  // ✅ Олон замуудын layer

const startIcon = L.divIcon({
    html: '<div style="background:#10b981;width:24px;height:24px;border-radius:50%;border:3px solid white;box-shadow:0 2px 4px rgba(0,0,0,0.3)"></div>',
    className: '',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
});

const endIcon = L.divIcon({
    html: '<div style="background:#ef4444;width:24px;height:24px;border-radius:50%;border:3px solid white;box-shadow:0 2px 4px rgba(0,0,0,0.3)"></div>',
    className: '',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
});

export function drawRoute(path, startCoord, endCoord) {
    // Хуучин route-г устгах
    clearAllRoutes();

    const latlngs = path.map(node_id => {
        const [lat, lon] = node_id.split("_").map(Number);
        return [lat, lon];
    });

    // Polyline зурах
    routeLayer = L.polyline(latlngs, {
        color: "#667eea",
        weight: 5,
        opacity: 0.7
    }).addTo(map);

    // Marker нэмэх
    addMarkers(startCoord, endCoord);
    map.fitBounds(routeLayer.getBounds(), { padding: [50, 50] });
}

export function drawMultiplePaths(pathsData, startCoord, endCoord) {
    // Хуучин замуудыг устгах
    clearAllRoutes();

    // Өнгөний палитр
    const colors = [
        '#667eea',  // Хамгийн богино - цэнхэр
        '#10b981',  // Ногоон
        '#f59e0b',  // Шар
        '#ef4444',  // Улаан
        '#8b5cf6',  // Нил ягаан
        '#ec4899',  // Ягаан
        '#06b6d4',  // Цайвар цэнхэр
        '#84cc16',  // Лайм
        '#f97316',  // Улбар шар
        '#6366f1'   // Индиго
    ];

    console.log(`🎨 ${pathsData.length} зам зурж байна...`);
    pathsData.forEach((pathData, index) => {
        const color = colors[index % colors.length];
        const weight = index === 0 ? 6 : 4;  // Эхнийг илүү зузаан
        const opacity = index === 0 ? 0.9 : 0.6;
        const zIndex = pathsData.length - index;  // Эхний зам дээд давхаргад

        const layer = L.polyline(pathData.coordinates, {
            color: color,
            weight: weight,
            opacity: opacity,
            zIndexOffset: zIndex * 10
        }).addTo(map);

        // Popup нэмэх
        const popupContent = `
            <div style="font-family: sans-serif;">
                <b style="color: ${color};">Зам ${index + 1}</b><br>
                📏 Урт: <b>${pathData.distance_km.toFixed(2)} км</b><br>
                🔢 Цэгүүд: <b>${pathData.nodes}</b>
            </div>
        `;
        layer.bindPopup(popupContent);

        // Hover эффект
        layer.on('mouseover', function() {
            this.setStyle({ weight: weight + 2, opacity: 1.0 });
        });

        layer.on('mouseout', function() {
            this.setStyle({ weight: weight, opacity: opacity });
        });

        allRouteLayers.push(layer);
    });

    console.log(`✅ ${allRouteLayers.length} зам зурагдлаа`);

    // Marker-ууд нэмэх
    addMarkers(startCoord, endCoord);

    // Бүх замуудыг багтаах
    const allCoords = pathsData.flatMap(p => p.coordinates);
    if (allCoords.length > 0) {
        const bounds = L.latLngBounds(allCoords);
        map.fitBounds(bounds, { padding: [50, 50] });
    }
}


function addMarkers(startCoord, endCoord) {
    if (startMarker) map.removeLayer(startMarker);
    if (endMarker) map.removeLayer(endMarker);

    startMarker = L.marker(startCoord, { icon: startIcon }).addTo(map)
        .bindPopup('🎯 Эхлэх цэг');
    endMarker = L.marker(endCoord, { icon: endIcon }).addTo(map)
        .bindPopup('🏁 Төгсгөлийн цэг');
}

/**
 * Бүх замуудыг устгах
 */
export function clearAllRoutes() {
    // Олон замууд устгах
    allRouteLayers.forEach(layer => {
        map.removeLayer(layer);
    });
    allRouteLayers = [];

    // Нэг зам устгах
    if (routeLayer) {
        map.removeLayer(routeLayer);
        routeLayer = null;
    }
}

/**
 * Газрын зургийг цэвэрлэх
 */
export function clearMap() {
    clearAllRoutes();

    if (startMarker) {
        map.removeLayer(startMarker);
        startMarker = null;
    }
    if (endMarker) {
        map.removeLayer(endMarker);
        endMarker = null;
    }
}

/**
 * Газрын зураг дээр дарах эвент хандлах
 * @param {Function} callback - (lat, lon) => void
 */
export function onMapClick(callback) {
    map.on('click', function(e) {
        const lat = e.latlng.lat.toFixed(4);
        const lon = e.latlng.lng.toFixed(4);
        callback(parseFloat(lat), parseFloat(lon));
    });
}
export function flyTo(lat, lon, zoom = 14) {
    map.flyTo([lat, lon], zoom);
}

export function showTemporaryMarker(lat, lon, text) {
    const tempMarker = L.marker([lat, lon])
        .addTo(map)
        .bindPopup(text)
        .openPopup();

    setTimeout(() => {
        map.removeLayer(tempMarker);
    }, 3000);
}