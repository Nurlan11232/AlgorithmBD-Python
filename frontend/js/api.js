// frontend/js/api.js
const API_BASE = "http://127.0.0.1:8000";
export async function getRoute(algorithm, lat1, lon1, lat2, lon2) {
    // ✅ Шууд /${algorithm} (route/ биш)
    const url = new URL(`${API_BASE}/${algorithm}`);
    url.searchParams.set("lat1", lat1);
    url.searchParams.set("lon1", lon1);
    url.searchParams.set("lat2", lat2);
    url.searchParams.set("lon2", lon2);

    if (algorithm === "dfs") {
        url.searchParams.set("max_depth", 50);
    }
    const startTime = performance.now();
    try {
        const response = await fetch(url);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API алдаа (${response.status}): ${errorText}`);
        }
        const data = await response.json();
        const endTime = performance.now();
        data.computeTime = ((endTime - startTime) / 1000).toFixed(3);

        return data;
    } catch (err) {
        console.error("API алдаа:", err);
        throw err;
    }
}

export async function getGraphStats() {
    try {
        const response = await fetch(`${API_BASE}/graph/stats`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return await response.json();
    } catch (err) {
        console.error("Статистик авахад алдаа:", err);
        return null;
    }
}

export async function getGraphBbox() {
    try {
        const response = await fetch(`${API_BASE}/graph/bbox`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return await response.json();
    } catch (err) {
        console.error("Bbox авахад алдаа:", err);
        return null;
    }
}

export async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        return response.ok;
    } catch (err) {
        console.error("Health check алдаа:", err);
        return false;
    }
}

export async function getNearestNode(lat, lon) {
    try {
        const url = new URL(`${API_BASE}/nearest_node`);
        url.searchParams.set("lat", lat);
        url.searchParams.set("lon", lon);
        url.searchParams.set("max_distance_km", 10.0);

        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return await response.json();
    } catch (err) {
        console.error("Nearest node алдаа:", err);
        return null;
    }
}