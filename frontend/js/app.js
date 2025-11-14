// frontend/js/app.js
import { getRoute, checkHealth, getGraphStats, getGraphBbox } from './api.js';
import { drawRoute, drawMultiplePaths, clearMap, onMapClick, showTemporaryMarker } from './map.js';

const startLatInput = document.getElementById("start_lat");
const startLonInput = document.getElementById("start_lon");
const endLatInput = document.getElementById("end_lat");
const endLonInput = document.getElementById("end_lon");
const algorithmSelect = document.getElementById("algorithm");
const findRouteBtn = document.getElementById("find_route");
const clearRouteBtn = document.getElementById("clear_route");
const statusDiv = document.getElementById("status");
const infoPanelDiv = document.getElementById("info_panel");

const distanceSpan = document.getElementById("distance");
const nodesSpan = document.getElementById("nodes");
const timeSpan = document.getElementById("time");
const algoSpan = document.getElementById("algo");

let clickMode = 'start';
function setStatus(message, type = 'info') {
    statusDiv.className = type;
    statusDiv.innerHTML = message;
}

function showLoading() {
    findRouteBtn.disabled = true;
    setStatus('Зам тооцоолж байна... <span class="loading"></span>', 'loading');
}


function hideLoading() {
    findRouteBtn.disabled = false;
}


function updateInfoPanel(data, algorithm) {
    // Зайн урт
    if (data.distance_km !== undefined) {
        distanceSpan.textContent = `${data.distance_km.toFixed(2)} км`;
    } else if (data.distance !== undefined) {
        distanceSpan.textContent = `${(data.distance / 1000).toFixed(2)} км`;
    } else {
        distanceSpan.textContent = 'Тодорхойгүй';
    }

    if (data.path) {
        nodesSpan.textContent = data.path.length;
    } else if (data.paths && data.paths.length > 0) {
        nodesSpan.textContent = data.paths[0].length;
    } else {
        nodesSpan.textContent = '0';
    }

    // Хугацаа
    timeSpan.textContent = `${data.computeTime}с`;

    // Алгоритм
    const algoNames = {
        'dijkstra': 'Dijkstra',
        'bfs': 'BFS',
        'dfs': 'DFS'
    };
    algoSpan.textContent = algoNames[algorithm] || algorithm;

    // Panel харуулах
    infoPanelDiv.classList.add('show');
}


function clearAll() {
    clearMap();
    infoPanelDiv.classList.remove('show');
    setStatus('Газрын зураг цэвэрлэгдсэн');
}


async function findRoute() {
    // Input утгууд авах
    const lat1 = parseFloat(startLatInput.value);
    const lon1 = parseFloat(startLonInput.value);
    const lat2 = parseFloat(endLatInput.value);
    const lon2 = parseFloat(endLonInput.value);
    const algorithm = algorithmSelect.value;

    // Validation
    if (isNaN(lat1) || isNaN(lon1) || isNaN(lat2) || isNaN(lon2)) {
        setStatus('❌ Координат зөв оруулна уу!', 'error');
        return;
    }

    showLoading();

    try {

        const data = await getRoute(algorithm, lat1, lon1, lat2, lon2);

        if (!data) {
            setStatus('❌ API-аас хариу ирсэнгүй', 'error');
            return;
        }

        // Замыг олж авах
        let pathToRender = null;

    if (algorithm === "dfs") {
    console.log("🔍 DFS response:", data);

    if (!data.paths || data.paths.length === 0) {
        setStatus('⚠️ Зам олдсонгүй', 'error');
        return;
    }

    if (data.all_paths_data && data.all_paths_data.length > 1) {
    console.log(`🎨 ${data.all_paths_data.length} зам зурж байна...`);
    drawMultiplePaths(data.all_paths_data, [lat1, lon1], [lat2, lon2]);
    setStatus(`✅ DFS: ${data.all_paths_data.length} өөр зам харуулж байна`, 'success');
}
    else {
        // Зөвхөн 1 зам
        console.log("⚠️ Зөвхөн 1 зам байна");
        pathToRender = data.paths[0];
        drawRoute(pathToRender, [lat1, lon1], [lat2, lon2]);
        setStatus(`✅ DFS: 1 зам олдлоо`, 'success');
    }

    updateInfoPanel(data, algorithm);
    hideLoading();
    return;
}
        else if (algorithm === "bfs" || algorithm === "dijkstra") {
            if (!data.path || data.path.length === 0) {
                setStatus('⚠️ Зам олдсонгүй', 'error');
                return;
            }
            pathToRender = data.path;
            const algoName = algorithm === "bfs" ? "BFS" : "Dijkstra";
            setStatus(`✅ ${algoName}: Зам амжилттай олдлоо!`, 'success');
        }

        // Зураг дээр зурах
        if (pathToRender) {
            drawRoute(pathToRender, [lat1, lon1], [lat2, lon2]);
            updateInfoPanel(data, algorithm);
        }

    } catch (err) {
        setStatus(`❌ Алдаа: ${err.message}`, 'error');
        console.error(err);
    } finally {
        hideLoading();
    }
}

findRouteBtn.addEventListener("click", findRoute);
clearRouteBtn.addEventListener("click", clearAll);


onMapClick((lat, lon) => {
    if (clickMode === 'start') {
        startLatInput.value = lat;
        startLonInput.value = lon;
        setStatus(`✅ Эхлэх цэг: ${lat}, ${lon} - Одоо төгсгөлийн цэгийг сонгоно уу`, 'success');
        showTemporaryMarker(lat, lon, '🎯 Эхлэх цэг');
        clickMode = 'end';
    } else {
        endLatInput.value = lat;
        endLonInput.value = lon;
        setStatus(`✅ Төгсгөлийн цэг: ${lat}, ${lon} - "Зам тооцоолох" товчийг дарна уу`, 'success');
        showTemporaryMarker(lat, lon, '🏁 Төгсгөлийн цэг');
        clickMode = 'start';
    }
});

// Enter товчоор зам тооцоолох
document.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        findRoute();
    }
});

async function init() {
    console.log("🚀 Application эхэлж байна...");

    // Backend health check
    const isHealthy = await checkHealth();
    if (!isHealthy) {
        setStatus('⚠️ Backend серверт холбогдож чадсангүй. http://127.0.0.1:8000 эхэлсэн эсэхийг шалгана уу', 'error');
        findRouteBtn.disabled = true;
        return;
    }

    // Статистик авах
    const stats = await getGraphStats();
    if (stats) {
        console.log("📊 График статистик:", stats);

        if (stats.bbox) {
            const [min_lat, max_lat, min_lon, max_lon] = stats.bbox;
            const center_lat = (min_lat + max_lat) / 2;
            const center_lon = (min_lon + max_lon) / 2;

            // Анхны координатууд
            startLatInput.value = center_lat.toFixed(4);
            startLonInput.value = center_lon.toFixed(4);

            // Төгсгөлийн координат (жаахан зайтай)
            endLatInput.value = (center_lat + 0.01).toFixed(4);
            endLonInput.value = (center_lon + 0.01).toFixed(4);

            console.log(`📍 Анхны координат тохирууллаа: ${center_lat.toFixed(4)}, ${center_lon.toFixed(4)}`);
        }
    }

    // Анхны мэдээлэл
    setStatus('🗺️ Бэлэн байна. Эхлэх цэгийг газрын зураг дээр дарж сонгоно уу');

    console.log("✅ Application амжилттай эхэллээ");
}

init();