"use strict";

let Cookie = {
    set: function (name, value, exp_y, exp_m, exp_d, path, domain, secure) {

        let cookie_string = name + "=" + encodeURI(value);

        if (exp_y) {
            let expires = new Date(exp_y, exp_m, exp_d);
            cookie_string += "; expires=" + expires.toUTCString();
        }

        if (path) {
            cookie_string += "; path=" + encodeURI(path);
        }
        if (domain) {
            cookie_string += "; domain=" + encodeURI(domain);
        }
        if (secure) {
            cookie_string += "; secure";
        }
        document.cookie = cookie_string;
    },
    get: function (cookie_name) {
        let results = document.cookie.match(`(^|;) ?${cookie_name}=([^;]*)(;|$)`);
        if (results) {
            return (decodeURI(results[2]));
        } else {
            return null;
        }
    },
    remove: function (cookie_name) {
        let cookie_date = new Date();
        cookie_date.setTime(cookie_date.getTime() - 1);
        document.cookie = cookie_name + "=; expires=" + cookie_date.toUTCString();
    }
};
