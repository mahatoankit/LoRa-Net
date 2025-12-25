// Initialize Socket.IO connection
const socket = io();

// Initialize map
let map;
let markers = [];
const eventColors = {
    'GUNSHOT': '#ef4444',
    'SAW_MACHINE': '#f59e0b',
    'CHOPPING_TREE': '#10b981',
    'EXPLOSION': '#dc2626',
    'VEHICLE_HORN': '#3b82f6',
    'ALARM': '#8b5cf6'
};

// Store all events
let allEvents = [];

// Initialize the map centered on Kathmandu, Nepal
function initMap() {
    map = L.map('map').setView([27.7172, 85.3240], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);
}

// Get color for event type
function getEventColor(eventType) {
    return eventColors[eventType] || '#6b7280';
}

// Get event icon based on type
function getEventIcon(eventType) {
    const icons = {
        'GUNSHOT': '🔫',
        'SAW_MACHINE': '🔧',
        'CHOPPING_TREE': '🪓',
        'EXPLOSION': '💥',
        'VEHICLE_HORN': '🚗',
        'ALARM': '🚨'
    };
    return icons[eventType] || '📍';
}

// Add marker to map
function addMarkerToMap(event) {
    const lat = parseFloat(event.LAT);
    const lon = parseFloat(event.LON);
    const color = getEventColor(event.VT);

    // Create custom icon
    const customIcon = L.divIcon({
        className: 'custom-marker',
        html: `<div style="background-color: ${color}; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; font-size: 16px;">${getEventIcon(event.VT)}</div>`,
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    });

    const marker = L.marker([lat, lon], { icon: customIcon }).addTo(map);

    // Create popup content
    const popupContent = `
        <div class="p-2">
            <h3 class="font-bold text-lg mb-2">${event.VT.replace(/_/g, ' ')}</h3>
            <p class="text-sm"><strong>Confidence:</strong> ${(parseFloat(event.CONF) * 100).toFixed(0)}%</p>
            <p class="text-sm"><strong>Location:</strong> ${event.LAT}, ${event.LON}</p>
            <p class="text-sm"><strong>Time:</strong> ${event.formatted_time}</p>
        </div>
    `;

    marker.bindPopup(popupContent);
    markers.push(marker);

    // Keep only last 20 markers
    if (markers.length > 20) {
        const oldMarker = markers.shift();
        map.removeLayer(oldMarker);
    }

    // Center map on new marker with animation
    map.setView([lat, lon], 14, { animate: true });
}

// Format confidence as percentage
function formatConfidence(conf) {
    return (parseFloat(conf) * 100).toFixed(0) + '%';
}

// Get confidence color
function getConfidenceColor(conf) {
    const confidence = parseFloat(conf);
    if (confidence >= 0.9) return 'bg-green-500';
    if (confidence >= 0.75) return 'bg-yellow-500';
    return 'bg-red-500';
}

// Update latest event card
function updateLatestEventCard(event) {
    const cardHTML = `
        <div class="border-l-4 pl-4" style="border-color: ${getEventColor(event.VT)}">
            <div class="flex items-center justify-between mb-3">
                <h3 class="text-2xl font-bold text-gray-800">${getEventIcon(event.VT)} ${event.VT.replace(/_/g, ' ')}</h3>
                <span class="text-sm text-gray-500">${event.formatted_time}</span>
            </div>
            
            <div class="space-y-3">
                <div>
                    <div class="flex justify-between items-center mb-1">
                        <span class="text-sm font-medium text-gray-600">Confidence</span>
                        <span class="text-sm font-bold text-gray-800">${formatConfidence(event.CONF)}</span>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-3">
                        <div class="confidence-bar ${getConfidenceColor(event.CONF)} h-3 rounded-full" 
                             style="width: ${formatConfidence(event.CONF)}"></div>
                    </div>
                </div>
                
                <div class="grid grid-cols-2 gap-4">
                    <div class="bg-gray-50 rounded-lg p-3">
                        <p class="text-xs text-gray-500 mb-1">Latitude</p>
                        <p class="font-mono font-semibold text-gray-800">${event.LAT}</p>
                    </div>
                    <div class="bg-gray-50 rounded-lg p-3">
                        <p class="text-xs text-gray-500 mb-1">Longitude</p>
                        <p class="font-mono font-semibold text-gray-800">${event.LON}</p>
                    </div>
                </div>
                
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p class="text-xs text-blue-600 mb-1">Timestamp</p>
                    <p class="font-mono text-sm text-blue-900">${event.TS}</p>
                </div>
            </div>
        </div>
    `;

    document.getElementById('latest-event-card').innerHTML = cardHTML;
}

// Add event to history
function addEventToHistory(event) {
    const historyContainer = document.getElementById('event-history');

    // Remove "no events" message if present
    if (historyContainer.querySelector('.text-center')) {
        historyContainer.innerHTML = '';
    }

    const eventHTML = `
        <div class="event-card new-event-animation bg-gray-50 hover:bg-gray-100 rounded-lg p-4 border-l-4" 
             style="border-color: ${getEventColor(event.VT)}">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3 flex-1">
                    <div class="text-2xl">${getEventIcon(event.VT)}</div>
                    <div class="flex-1">
                        <h4 class="font-bold text-gray-800">${event.VT.replace(/_/g, ' ')}</h4>
                        <p class="text-sm text-gray-600">${event.formatted_time}</p>
                    </div>
                </div>
                <div class="text-right">
                    <div class="text-sm font-semibold text-gray-700">${formatConfidence(event.CONF)}</div>
                    <div class="text-xs text-gray-500">${event.LAT}, ${event.LON}</div>
                </div>
            </div>
        </div>
    `;

    historyContainer.insertAdjacentHTML('afterbegin', eventHTML);
}

// Update statistics
function updateStats() {
    document.getElementById('total-events').textContent = allEvents.length;

    if (allEvents.length > 0) {
        const latestEvent = allEvents[allEvents.length - 1];
        document.getElementById('latest-event').textContent = latestEvent.VT.replace(/_/g, ' ');

        // Calculate average confidence
        const avgConf = allEvents.reduce((sum, e) => sum + parseFloat(e.CONF), 0) / allEvents.length;
        document.getElementById('avg-confidence').textContent = (avgConf * 100).toFixed(0) + '%';
    }
}

// Handle new event from server
function handleNewEvent(event) {
    console.log('New event received:', event);

    allEvents.push(event);

    // Update UI
    addMarkerToMap(event);
    updateLatestEventCard(event);
    addEventToHistory(event);
    updateStats();
}

// Socket.IO event handlers
socket.on('connect', () => {
    console.log('Connected to server');
    document.getElementById('status').textContent = 'Connected';
    document.getElementById('status').classList.remove('text-red-400');
    document.getElementById('status').classList.add('text-green-400');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    document.getElementById('status').textContent = 'Disconnected';
    document.getElementById('status').classList.remove('text-green-400');
    document.getElementById('status').classList.add('text-red-400');
});

socket.on('initial_events', (data) => {
    console.log('Received initial events:', data.events.length);
    data.events.forEach(event => {
        allEvents.push(event);
        addEventToHistory(event);
        if (data.events.indexOf(event) === data.events.length - 1) {
            // Only show the latest event on map and details
            addMarkerToMap(event);
            updateLatestEventCard(event);
        }
    });
    updateStats();
});

socket.on('new_event', (event) => {
    handleNewEvent(event);
});

// Initialize map when page loads
document.addEventListener('DOMContentLoaded', () => {
    initMap();
});
