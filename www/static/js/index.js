

$(() => {
    var w = window.innerWidth;
    var h = window.innerHeight;

    $("#map_view").css({"height": `${h}px`})

    $("#channels_list").on('click', 'button[data-channel]', (evt) => {
        let channel = $(evt.target).data("channel");
        $.post("/", {"channel": channel}, (data) => {
            $('#map_view').attr('src', `/static/data/index_map_${channel}.html`);
        })

    });

});
