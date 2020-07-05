

$(() => {
    let heatMapLayer = null;
    let center = Cookie.get("map_center");
    let zoom = Cookie.get("map_zoom");
    let map = L.map('map-view', { center: (center ? center.split(" ") : [0, 0]), zoom: zoom });

    map.on('zoom', (e) => {
        Cookie.set("map_zoom", map.getZoom())
    });

    map.on('move', (e) => {
        Cookie.set("map_center", Object.values(map.getCenter()).join(" "))
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    $.post("/api/index/action_channels", (data) => {
        for (let index = 0; index < data.channels.length; index++) {
            $("#channels-list").append(aux.template("tt-channels-bar-item", {"channel": data.channels[index]}));
        }
        $("#channels-list").show();
    })

    $("#channels-list").on('click', 'button[data-channel]', (evt) => {
        let channel = $(evt.target).data("channel");
    
        $.post("/api/index/action_heat_map", {"channel": channel}, (data) => {
            if (heatMapLayer)
            {
                heatMapLayer.setLatLngs(data.heat_map)
                heatMapLayer.setOptions({"max": data.signal_max})
            }
            else
            {
                heatMapLayer = L.heatLayer(data.heat_map, {"blur": 20, "max": data.signal_max, "maxZoom": 1, "minOpacity": 0.2, "radius": 20});
                heatMapLayer.addTo(map);
            }
    
        })
    }); 
});