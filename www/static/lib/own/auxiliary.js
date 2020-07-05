
let aux = {
    template: function(eid, data = {}) {
        return document.getElementById(eid).innerHTML.replace(/{(\w*)}/g, function(_, k) {
          return data.hasOwnProperty(k) ? data[k] : "";
        });
    }
};
