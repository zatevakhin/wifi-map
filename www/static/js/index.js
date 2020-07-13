

const MapDisplayAs = Object.freeze({
    HEATMAP: 0,
    MARKERS: 1,
})


const RequestMapData = Object.freeze({
    POSITION: 0x01,
    WIFI: 0x02,
    VISIBLE_ACCESS_POINTS: 0x03
})


class MapView {

    constructor() {
        this.mapDisplayAs = MapDisplayAs.MARKERS;
        this.gpsLocationMarker = null;
        
        this.mapSettings = { center: "0 0", zoom: 4 };

        this.map = null;
        this.mapHeatmapLayer = null;
        this.mapHeatmapLayerSignal = null;
        this.mapMarkerCluster = null;

        this.mapMarkersLayer = null;

        this.markerList = {};

        this.ws_host = window.location.hostname;

        this.websocket = null;
    }

    on_websocket_message(data) {
        console.log(data);

        if (data.return === RequestMapData.POSITION)
        {
            this.on_position_update(data);
        }
        else if (data.return === RequestMapData.VISIBLE_ACCESS_POINTS)
        {
            this.on_access_points_list_update(data);
        }
        else if (data.return === RequestMapData.WIFI)
        {
            this.on_map_data_update(data);
        }
    }

    on_position_update(data) {
        if (this.gpsLocationMarker)
        {
            this.gpsLocationMarker.setLatLng([data.position.latitude, data.position.longitude])
        }
        else
        {
            var geoPosition = L.icon.glyph({
                iconUrl: Marker.Red,
                prefix: 'mdi',
                glyph: 'crosshairs-gps'
            });

            this.gpsLocationMarker = L.marker([
                data.position.latitude, data.position.longitude
            ], {icon: geoPosition, zIndexOffset: 1000});

            this.gpsLocationMarker.addTo(this.map);
        }
    }

    on_map_data_update(data) {
        if (MapDisplayAs.MARKERS === this.mapDisplayAs) {
            this.on_markers_update(data)
        }
        else if (MapDisplayAs.HEATMAP === this.mapDisplayAs)
        {
            this.on_heatmap_update(data)
        }
        else
        {
            console.log(`NOT HANDLED MAP UPDATE = ${data}`);
        }
    }

    on_access_points_list_update(data) {

        Object.keys(this.markerList).forEach((id) => {
            let marker = this.markerList[id];
            let icon = marker.getIcon();

            let isIncludes = data.devices.includes(id);

            marker.setZIndexOffset(isIncludes ? 1 : 0);
            icon.options.iconUrl = isIncludes ? Marker.Green : Marker.Gray;

            marker.setIcon(icon);
        })
    }

    on_markers_update(data) {
        data.records.forEach((ap) => {
            console.log("add -> ", ap)
            this.add_access_point_marker(ap);
        })
    }

    on_heatmap_update(data) {

    }

    run() {
        this.mapSettings = {
            center: Cookie.get("map_center", this.mapSettings.center).split(" "),
            zoom: Cookie.get("map_zoom", this.mapSettings.zoom)
        };
        
        this.map = L.map('map-view', {
            center: this.mapSettings.center,
            zoom: this.mapSettings.zoom,
            maxZoom: 18,
        })

        this.mapMarkerCluster = L.markerClusterGroup({
            disableClusteringAtZoom: 18
        });

        this.map.addLayer(this.mapMarkerCluster);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(this.map);
    
        this.map.on('zoom', (e) => {
            Cookie.set("map_zoom", this.map.getZoom())
        });
    
        this.map.on('move', (e) => {
            Cookie.set("map_center", Object.values(this.map.getCenter()).join(" "))
        });


        this.websocket = new WebSocket(`ws://${this.ws_host}:8002/api/websocket`);
        
        setInterval(() => {
            this.websocket.send(JSON.stringify({"action": RequestMapData.WIFI}));
        }, 1000 * 5);

        setInterval(() => {
            this.websocket.send(JSON.stringify({"action": RequestMapData.POSITION}));
        }, 1000 * 5);

        setInterval(() => {
            this.websocket.send(JSON.stringify({"action": RequestMapData.VISIBLE_ACCESS_POINTS}));
        }, 1000 * 5);

        this.websocket.addEventListener('message', (event) => {
            let data = JSON.parse(event.data);
            this.on_websocket_message(data);
        });


        $.post("/api/index/action_channels", (data) => {
            for (let index = 0; index < data.channels.length; index++) {
                $("#channels-list").append(
                    aux.template("tt-channels-bar-item", {"channel": data.channels[index]})
                );
            }

            $("#channels-list").show();
        });

        $.post("/api/index/action_records", (data) => {
            for (let index = 0; index < data.records.length; index++) {
                this.add_access_point_marker(data.records[index]);
            }
        });
    }

    add_access_point_marker(ap) {
        this.markerList[ap.address] = L.marker([ap.latitude, ap.longitude], {icon: L.icon.glyph({
            iconUrl: Marker.Gray,
            prefix: 'mdi',
            glyph: 'router-wireless',
            glyphColor: ap.name ? 'white' : 'black',
        })});

        let marker = this.markerList[ap.address];
        
        let tooltipText = "Name: " + (ap.name || "<EMPTY>") + "<br>" 
        tooltipText += "Address: " + ap.address + "<br>" 
        tooltipText += "Channel: " + ap.channel + "<br>" 
        tooltipText += "Frequency: " + ap.frequency + "<br>" 
        tooltipText += "Signal: " + ap.signal

        marker.bindTooltip(tooltipText);

        this.mapMarkerCluster.addLayer(marker);
        // marker.addTo(this.map);
    }
}


$(() => {
    let mv = new MapView();
    mv.run();
});
