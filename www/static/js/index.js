
Storage.prototype.setObject = function(key, value) {
    this.setItem(key, JSON.stringify(value));
}

Storage.prototype.getObject = function(key) {
    let value = this.getItem(key);
    return value && JSON.parse(value);
}

const MapDisplayAs = Object.freeze({
    HEATMAP: 0,
    MARKERS: 1,
})

const GpsStatus = Object.freeze({
    DISCONNECTED: 0x01,
    ZERO_DATA: 0x02,
    NO_2D_FIX: 0x03,
    NO_3D_FIX: 0x04,
    FULL_DATA: 0x05
})

const RequestMapData = Object.freeze({
    POSITION: 0x01,
    WIFI: 0x02,
    VISIBLE_ACCESS_POINTS: 0x03,
    AVAILABLE_WIRELESS_INTERFACES: 0x04,

    DEVICE_ENABLE: 0x05,
    DEVICE_DISABLE: 0x06,
    DEVICE_ADD_MONITOR: 0x07,
    DEVICE_REMOVE_MONITOR: 0x08,
    DEVICE_SET_CHANNEL: 0x09,

    STATUS_GPS: 0x0A,
    STATUS_SERVICES: 0x0B,
})

let rand = (min, max) => {
    return (Math.random() * (max - min) + min);
}

class WebSocketWrapper
{
    constructor(url)
    {
        this.url = url;
        this.websocket = null;
        this.messageHandler = null;
        this.connectionOpenHandler = null;
        this.connectionCloseHandler = null;

        this.websocketReconnect = null;
    }

    connect()
    {
        if (this.messageHandler)
        {
            let websocket = new WebSocket(this.url);

            websocket.addEventListener('open', (event) => {
                console.log("Connected.")

                if (this.websocketReconnect)
                {
                    clearInterval(this.websocketReconnect);
                }

                if (this.connectionOpenHandler)
                {
                    this.connectionOpenHandler(event);
                }
            });

            websocket.addEventListener('close', (event) => {
                console.warn("Disconnected.")

                if (this.websocketReconnect)
                {
                    clearInterval(this.websocketReconnect);
                }

                this.websocketReconnect = setInterval(() => {
                    this.connect();
                }, 1000 * 5);

                if (this.connectionCloseHandler)
                {
                    this.connectionCloseHandler(event);
                }
            });

            websocket.addEventListener('message', (event) => {
                this.messageHandler(JSON.parse(event.data));
            });

            this.websocket = websocket;
        }
        else
        {
            console.error("Message handler should be set!")
        }
    }

    setMessageHandler(fn)
    {
        this.messageHandler = fn;
    }

    setOpenHandler(fn)
    {
        this.connectionOpenHandler = fn;
    }

    setCloseHandler(fn)
    {
        this.connectionCloseHandler = fn;
    }

    reconnect()
    {
        console.warn("Reconnecting...")

        this.connect();
    }

    send(obj)
    {
        if (this.websocket)
        {
            this.websocket.send(JSON.stringify(obj));
        }
        else
        {
            console.error("WebSocket should be connected!");
        }
    }
}

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
        this.websocketReconnect = null;
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
        else if (data.return === RequestMapData.STATUS_SERVICES)
        {
            console.log(data);
        }
        else if (data.return === RequestMapData.STATUS_GPS)
        {
            this.on_gps_status_updated(data);
        }
        else if (data.return === RequestMapData.AVAILABLE_WIRELESS_INTERFACES)
        {
            $("#devices-list").empty();

            for (const [device, properties] of Object.entries(data.interfaces)) {
                $("#devices-list").append(
                    aux.template("tt-device-item", {
                        "device": device,
                        "enabled": properties.enabled,
                        "monitor": properties.monitor,
                        "monitor_available": properties.monitor_available
                    })
                );

                $(`#devices-list button[data-device=${device}]`)
                    .addClass(properties.enabled ? "btn-success" : "btn-secondary")
                    .addClass(properties.monitor ? "device-monitor" : "");
            }

            $("#devices-list").show();
        }
    }

    on_gps_status_updated(data) {
        let getStatus = (status) => {
            switch(status)
            {
                case GpsStatus.FULL_DATA:
                    return ['mdi-crosshairs-gps', 'Gps Active'];
                case GpsStatus.NO_3D_FIX:
                    return ['mdi-crosshairs', 'No 3D fix'];
                case GpsStatus.NO_2D_FIX:
                    return ['mdi-crosshairs', 'No 2D fix'];
                case GpsStatus.ZERO_DATA:
                    return ['mdi-crosshairs-question', 'Gps have no data'];
                case GpsStatus.DISCONNECTED:
                default:
                    return ['mdi-crosshairs-off', 'Gps lost connection'];
            }
        }

        const [icon, title] = getStatus(data.status)

        $("#system-statuses span.gps-status i")
        .removeClass(['mdi-crosshairs-gps', 'mdi-crosshairs', 'mdi-crosshairs-question', 'mdi-crosshairs-off', 'mdi-spin'])
        .addClass([icon, (data.status === GpsStatus.FULL_DATA) ? 'mdi-spin' : '']);
        $("#system-statuses span.gps-status").attr({title: title});
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
        let accessPoints = localStorage.getObject("accessPoints") || {};

        for (let i = 0; i < data.records.length; i++) {
            const e = data.records[i];
            accessPoints[e.bssid] = e;
        }

        localStorage.setObject("accessPoints", accessPoints)

        this.on_markers_update(Object.values(accessPoints))
    }

    on_access_points_list_update(data) {

        console.log("on_access_points_list_update", data)

        Object.keys(this.markerList).forEach((id) => {
            let marker = this.markerList[id];
            let icon = marker.getIcon();

            let isIncludes = data.devices.includes(id);

            marker.setZIndexOffset(isIncludes ? 100 : 0);
            icon.options.iconUrl = isIncludes ? Marker.Green : Marker.Gray;

            marker.setIcon(icon);
        })
    }

    on_markers_update(data) {
        data.forEach((ap) => {
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
            zoomControl: false
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

        this.map.on('contextmenu.select', (e) => {
            console.log("contextmenu.select", e);
            e.hide()
        });


        this.websocket = new WebSocketWrapper(`ws://${this.ws_host}:8002/api/websocket`);

        this.websocket.setMessageHandler((e) => {
            this.on_websocket_message(e)
        })

        this.websocket.setOpenHandler((e) => {
            $("#system-statuses span.web-socket-status i").css({"color": "green"});
        });

        this.websocket.setCloseHandler((e) => {
            $("#system-statuses span.web-socket-status i").css({"color": "red"});
        });

        this.websocket.connect();

        setInterval(() => {
            this.websocket.send({"action": RequestMapData.WIFI});
        }, 1000 * 5);

        setInterval(() => {
            this.websocket.send({"action": RequestMapData.POSITION});
        }, 1000 * 5);

        setInterval(() => {
            this.websocket.send({"action": RequestMapData.VISIBLE_ACCESS_POINTS});
        }, 1000 * 5);

        setInterval(() => {
            this.websocket.send({"action": RequestMapData.AVAILABLE_WIRELESS_INTERFACES});
        }, 1000 * 5);

        setInterval(() => {
            this.websocket.send({"action": RequestMapData.STATUS_GPS});
        }, 1000 * 5);

        setInterval(() => {
            this.websocket.send({"action": RequestMapData.STATUS_SERVICES});
        }, 1000 * 5);


        $("#devices-list").on("click", "button[data-device]", (e) => {
            $("#devices-operations").empty();

            const device = $(e.currentTarget).data("device");
            const enabled = $(e.currentTarget).data("enabled");
            const monitor = $(e.currentTarget).data("monitor");
            const monitorAvailable = $(e.currentTarget).data("monitor-available");

            if (enabled) {
                $("#devices-operations").append(aux.template("tt-device-action", {
                    device: device,
                    text: `<i class="mdi mdi-access-point-off"></i>`,
                    title: "Disable",
                    action: RequestMapData.DEVICE_DISABLE
                }));

                $("#devices-operations").append(aux.template("tt-device-action", {
                    device: device,
                    text: `<i class="mdi mdi-alpha-c"></i>`,
                    title: "Set channel",
                    action: RequestMapData.DEVICE_SET_CHANNEL
                }));

            } else {
                $("#devices-operations").append(aux.template("tt-device-action", {
                    device: device,
                    text: `<i class="mdi mdi-access-point-check"></i>`,
                    title: "Enable",
                    action: RequestMapData.DEVICE_ENABLE
                }));
            }

            if (monitorAvailable && !monitor) {
                $("#devices-operations").append(aux.template("tt-device-action", {
                    device: device,
                    text: `<i class="mdi mdi-access-point-plus"></i>`,
                    title: "Add monitor",
                    action: RequestMapData.DEVICE_ADD_MONITOR
                }));
            }

            if (monitor) {
                $("#devices-operations").append(aux.template("tt-device-action", {
                    device: device,
                    text: `<i class="mdi mdi-access-point-remove"></i>`,
                    title: "Remove monitor",
                    action: RequestMapData.DEVICE_REMOVE_MONITOR
                }));
            }

            $("#devices-operations").show();
        });

        $("#devices-operations").on("click", "button[data-device]", (e) => {
            $("#devices-operations").empty();

            const device = $(e.currentTarget).data("device");
            const action = $(e.currentTarget).data("action");

            console.log(action, e)

            this.websocket.send({"action": parseInt(action), "device": device});
            this.websocket.send({"action": RequestMapData.AVAILABLE_WIRELESS_INTERFACES});
        });
    }

    add_access_point_marker(ap) {
        // let image = new Image();

        // var canvas = document.getElementById("canvas-txt");

        // image.onload = () => {
        //     var ctx = canvas.getContext("2d");
        //     ctx.drawImage(image, 0, 0);
        //     ctx.fillRect(10, 10, 5, 5);

        //     let marker = this.markerList[ap.bssid];
        //     let icon = marker.getIcon();

        //     icon.options.iconUrl = canvas.toDataURL("image/png");
        //     marker.setIcon(icon);
        // }

        // image.src = Marker.Gray;

        if (!this.markerList[ap.bssid])
        {
            this.markerList[ap.bssid] = L.marker([
                ap.latitude + rand(-0.0005, 0.0005),
                ap.longitude + rand(-0.0005, 0.0005)
            ], {
                contextmenu: true,
                contextmenuInheritItems: false,
                contextmenuItems: [
                    {
                        text: 'Add to capture list',
                        callback: (e) => { console.log(e); }
                    },
                    {
                        text: 'DoS',
                        callback: (e) => { console.log(arguments) }
                    }
                ],
                icon: L.icon.glyph({
                iconUrl: Marker.Gray,
                prefix: 'mdi',
                glyph: 'router-wireless',
                glyphColor: ap.ssid ? 'white' : 'black',
            })});
        }

        let marker = this.markerList[ap.bssid];
        console.log("menu", marker.options.contextmenuItems)

        // marker.setLatLng(new L.LatLng(ap.latitude + rand(-0.0005, 0.0005), ap.longitude + rand(-0.0005, 0.0005)));

        let tooltipText = "SSID: " + (ap.ssid || "&lt;EMPTY&gt;") + "<br>"
        tooltipText += "BSSID: " + ap.bssid + "<br>"
        tooltipText += "Channel: " + ap.channel + "<br>"
        if (ap.encrypted) {
            tooltipText += "Encryption: " + ap.encryption + "<br>"
        }

        marker.bindTooltip(tooltipText);

        this.mapMarkerCluster.addLayer(marker);
    }
}


$(() => {
    let mv = new MapView();
    mv.run();
});
