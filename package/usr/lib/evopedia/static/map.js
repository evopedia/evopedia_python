function MapHandler() {
    var lthis = this;
    this.container = document.getElementById('mapContainer');
    if (window.location.search.indexOf('mode=link') < 0) {
        this.container.onclick = function(e) { return lthis.containerClicked(e); }
    }
}

MapHandler.prototype = {
    getEventPosition: function(e) {
        var x;
        var y;
        if (window.event) { /* ie */
            e = window.event;
            x = e.clientX + document.body.scrollLeft;
            y = e.clientY + document.body.scrollTop;
        } else { /* netscape */
            x = e.pageX;
            y = e.pageY;
        }
        return [x, y];
    },

    getAbsolutePosition: function(obj) {
        var x = 0;
        var y = 0;
        var parent = obj;
        while (parent) {
            y += parent.offsetTop;
            x += parent.offsetLeft;
            parent = parent.offsetParent;
        }
        return [x, y];
    },

    containerClicked: function(e) {
        pos = this.getEventPosition(e);
        containerPos = this.getAbsolutePosition(this.container);
        href = window.location.href.replace(/&clickx=[0-9]*&clicky=[0-9]*/, '');
        window.location.href = href + '&clickx=' + (pos[0] - containerPos[0]) +
                                '&clicky=' + (pos[1] - containerPos[1]);
        return false;
    }
}
