function makeHTTPRequest(url, onReady, userData) {
    var request;
    var onReadyFunc = onReady;
    var userDataLocal = userData;
    if (window.XMLHttpRequest) {
        request = new XMLHttpRequest();
    } else if (window.ActiveXObject) {
        request = new ActiveXObject("Microsoft.XMLHTTP");
    }
    request.open('GET', url, true);
    request.onreadystatechange = function() {
        if (request.readyState != 4) return;
        onReadyFunc(request, request.status == '200', userDataLocal);
    }
    request.send(null);
    return request;
}

function makeURLParams(params) {
    var parts = new Array();
    var k,v;
    for (key in params) {
        parts.push(encodeURIComponent(key) + '=' + encodeURIComponent(params[key]));
    }
    return parts.join('&');
}

function makeURL(url, params) {
    return url + '?' + makeURLParams(params);
}

function getNodeContent(node) {
    var value = '';
    var child = node.firstChild;
    while (child != null) {
        value += child.nodeValue;
        child = child.nextSibling;
    }
    return value;
}

function getInnerSize(theDocument) {
    if (theDocument == null) theDocument = document;
    var x, y;
    if (theDocument.innerWidth) {
        x = theDocument.innerWidth;
        y = theDocument.innerHeight;
    } else if (theDocument.documentElement && theDocument.documentElement.clientHeight) {
        x = theDocument.documentElement.clientWidth;
        y = theDocument.documentElement.clientHeight;
    } else if (theDocument.body) {
        x = theDocument.clientWidth;
        y = theDocument.clientHeight;
    }
    return [x, y];
}

function stopEventPropagation(e)
{
    var ev = e;
    if (!e) ev = window.event;
    ev.cancelBubble = true;
    if (ev.stopPropagation) ev.stopPropagation();
}




function MapHandler(zoom, centerx, centery, repos) {
    var lthis = this;

    this.zoom = zoom;
    this.centerx = centerx;
    this.centery = centery;
    this.repos = repos;

    document.getElementById('jswarning').style.display = 'none';

    var repo = 0;
    /* check if we came here via "back button" and set position */
    var hash = window.location.hash.substring(1);
    if (hash.split(',').length == 4) {
        var last_data = hash.split(',');

        var lpzoom = parseInt(last_data[0]);
        var lpcenterx = parseFloat(last_data[1]);
        var lpcentery = parseFloat(last_data[2]);
        repo = parseInt(last_data[3]);
        if (lpzoom != null && lpcenterx != null && lpcentery != null) {
            this.zoom = lpzoom;
            this.centerx = lpcenterx;
            this.centery = lpcentery;
        }
    }

    /* this is changed on every browser resize and right at startup */
    this.map_width = 400;
    this.map_height = 380;

    this.tilesize = 256;

    this.gps_pos = null;

    this.container = document.getElementById('mapContainer');
    this.container.onclick = function(e) { return lthis.containerClicked(e); }
    this.tileContainer = document.getElementById('tileContainer');
    this.articleContainer = document.getElementById('articleContainer');
    this.articles = [];

    this.populateRepoChooser(repo);

    this.lastArticleRequest = null;

    this.zoomToGPSPosUsed = false;
    document.getElementById('gpspos').onclick = function() { lthis.zoomToGPSPos(); return false; }
    document.getElementById('zoomin').onclick = function() { lthis.zoomDelta(1); return false; }
    document.getElementById('zoomout').onclick = function() { lthis.zoomDelta(-1); return false; }
    document.getElementById('searchlink').onclick = function() { lthis.saveDataInHash(); return true; }
    document.getElementById('randomlink').onclick = function() { lthis.saveDataInHash(); return true; }

    this.crosshairs = document.getElementById('crosshairs');

    //this.click_action_sel = document.getElementById('click_action');
    this.repochooser = document.getElementById('tile_repo');
    this.repochooser.onchange = function() { lthis.browserResized(); }

    this.infodiv = document.getElementById('infodiv');
    this.infodivinterior = document.getElementById('infodivinterior');
    document.getElementById('infodivclose').onclick = function(e) { lthis.infodiv.style.display = 'none'; stopEventPropagation(e); return false; }
    this.errortext = document.getElementById('errortext');

    window.onresize = function() { lthis.browserResized(); };

    window.setTimeout(function() { lthis.browserResized();
                                   lthis.updateGPSPosition(); }, 10);
    this.gpsPositionUpdateInterval = window.setInterval(function() { lthis.updateGPSPosition(); }, 10000);
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

    populateRepoChooser: function(defaultRepo) {
        var chooser = document.getElementById('tile_repo');
        var i;
        for (i = 0; i < this.repos.length; i ++) {
            chooser.options[i] = new Option(this.repos[i], i, i == defaultRepo);
        }
    },

    updateMap: function(centerx, centery, zoom) {
        this.updateCrosshairs(centerx, centery, zoom);
        this.updateTiles(centerx, centery, zoom);
        this.updateArticles(centerx, centery, zoom);
        this.centerx = centerx;
        this.centery = centery;
        this.zoom = zoom;
    },

    updateTiles: function(centerx, centery, zoom) {
        this.tileContainer.innerHTML = '';

        var minxtile = Math.floor((centerx - this.map_width / 2) / this.tilesize);
        var numxtiles = Math.ceil(this.map_width / this.tilesize) + 1;
        var minytile = Math.floor((centery - this.map_height / 2) / this.tilesize);
        var numytiles = Math.ceil(this.map_height / this.tilesize) + 1;

        var repoindex = this.repochooser.selectedIndex;

        var tiley;
        var tilex;
        var img;
        for (tiley = minytile; tiley < minytile + numytiles; tiley ++) {
            for (tilex = minxtile; tilex < minxtile + numxtiles; tilex ++) {
                img = document.createElement('img');
                img.style.position = 'absolute';
                img.style.left = Math.floor(tilex * this.tilesize - centerx + this.map_width / 2) + 'px';
                img.style.top = Math.floor(tiley * this.tilesize - centery + this.map_height / 2) + 'px';
                img.src = '/maptile/' + repoindex + '/' + zoom + '/' + tilex + '/' + tiley + '.png';
                this.tileContainer.appendChild(img);
            }
        }
    },

    updateArticles: function(centerx, centery, zoom) {
        var params = {
            'minx': Math.floor(centerx - this.map_width / 2),
            'maxx': Math.floor(centerx + this.map_width / 2),
            'miny': Math.ceil(centery - this.map_height / 2),
            'maxy': Math.ceil(centery + this.map_height / 2),
            'zoom': zoom
        };

        var text;
        var lthis = this;
        if (this.lastArticleRequest != null) {
            this.lastArticleRequest.abort();
        }
        this.lastArticleRequest = makeHTTPRequest(makeURL('/geo', params),
                function(request) { lthis.updateArticlesResponse(request); });
        text = 'Loading articles...';
        this.errortext.innerHTML = '';
        this.errortext.appendChild(document.createTextNode(text));
        this.errortext.style.display = 'block';

        /* this code is almost duplicated at updateCrosshairs */
        var factor = 1;
        if (this.zoom < zoom) {
            factor = 1 << (zoom - this.zoom);
        } else if (this.zoom > zoom) {
            factor = 1 / (1 << (this.zoom - zoom));
        }
        /* 32 is icon size */
        var xoffset = (this.map_width - 32) / 2  * (1 - factor) + this.centerx * factor - centerx;
        var yoffset = (this.map_height - 32) / 2  * (1 - factor) + this.centery * factor - centery;
        var i = 0;
        var a;
        for (i = 0; i < this.articles.length; i ++) {
            a = this.articles[i];
            a.left = a.left * factor + xoffset;
            a.top = a.top * factor + yoffset;
            a.icon.style.left = a.left + 'px';
            a.icon.style.top = a.top + 'px';
        }
    },

    updateArticlesResponse: function(request) {
        if (request != this.lastArticleRequest) return;

        var error = request.responseXML.getElementsByTagName('error');
        if (error.length > 0) {
            this.errortext.innerHTML = '';
            this.errortext.appendChild(document.createTextNode(getNodeContent(error[0])));
            this.errortext.style.display = 'block';
        } else {
            this.errortext.style.display = 'none';
        }

        var lthis = this;
        this.articles = [];
        this.articleContainer.innerHTML = '';
        var articles = request.responseXML.getElementsByTagName('article');
        if (articles === null) return;
        var article;
        var wikipedialink;
        var topleftx = Math.floor(this.centerx - this.map_width / 2);
        var toplefty = Math.floor(this.centery - this.map_height / 2);
        for (var i = 0; i < articles.length; i ++) {
            article = articles[i];
            wikipedialink = document.createElement('img');
            wikipedialink.src = '/static/wikipedia.png';
            wikipedialink.articleName = article.getAttribute('name');
            wikipedialink.articleLink = article.getAttribute('href');
            wikipedialink.articleInfodivpos = (parseFloat(article.getAttribute('y')) - toplefty + 16) > this.map_height / 2 ? 'top' : 'bottom';
            wikipedialink.style.position = 'absolute';
            wikipedialink.style.left = (parseFloat(article.getAttribute('x')) - topleftx - 16) + 'px';
            wikipedialink.style.top = (parseFloat(article.getAttribute('y')) - toplefty - 16) + 'px';
            wikipedialink.onclick = function(e) { return lthis.articleClicked(this, e); };
            this.articleContainer.appendChild(wikipedialink);
            this.articles[this.articles.length] = {
                                            left: parseFloat(article.getAttribute('x')) - topleftx - 16,
                                            top: parseFloat(article.getAttribute('y')) - toplefty - 16,
                                            icon: wikipedialink
                                        };
        }
    },

    updateGPSPosition: function() {
        var lthis = this;
        if (!this.zoomToGPSPosUsed) return;
        makeHTTPRequest(makeURL('/gpspos', {zoom: this.zoom}),
                function(request) { lthis.updateGPSPositionResponse(request); });
    },

    updateGPSPositionResponse: function(request) {
        var error = request.responseXML.getElementsByTagName('error');
        var pos = request.responseXML.getElementsByTagName('position')[0];
        if (error.length > 0 || pos == null) {
            /* cannot display error message in asynchronous request
            this.errortext.innerHTML = '';
            if (error.length > 0) {
                this.errortext.appendChild(document.createTextNode(getNodeContent(error[0])));
            } else {
                this.errortext.appendChild(document.createTextNode('Error getting GPS fix.'));
            }
            this.errortext.style.display = 'block';
            */
            /* XXX decrease gps poll interval */
            return;
        }

        if (pos === null || parseInt(pos.getAttribute('zoom')) != this.zoom) return;
        this.gps_pos = [parseFloat(pos.getAttribute('x')), parseFloat(pos.getAttribute('y'))];

        this.updateCrosshairs(this.centerx, this.centery, this.zoom);
    },

    updateCrosshairs: function(centerx, centery, zoom) {
        if (this.gps_pos === null) {
            this.crosshairs.style.display = 'none';
        } else {
            /* this code is almost duplicated at updateArticles */
            var factor = 1;
            if (this.zoom < zoom) {
                factor = 1 << (zoom - this.zoom);
            } else if (this.zoom > zoom) {
                factor = 1 / (1 << (this.zoom - zoom));
            }
            var xoffset = 0;//this.map_width / 2  * (1 - factor);
            var yoffset = 0;//this.map_height / 2  * (1 - factor);

            this.gps_pos[0] = this.gps_pos[0] * factor + xoffset;
            this.gps_pos[1] = this.gps_pos[1] * factor + yoffset;

            var topleftx = Math.floor(centerx - this.map_width / 2);
            var toplefty = Math.floor(centery - this.map_height / 2);
            this.crosshairs.style.left = (this.gps_pos[0] - topleftx - 15) + 'px';
            this.crosshairs.style.top = (this.gps_pos[1] - toplefty - 15) + 'px';
            this.crosshairs.style.display = 'block';
        }
    },

    zoomToGPSPos: function() {
        this.zoomToGPSPosUsed = true;
        this.updateGPSPosition();
        if (this.gps_pos === null) {
            return;
        }

        this.updateMap(this.gps_pos[0], this.gps_pos[1], 12);
    },

    containerClicked: function(e) {
        var pos = this.getEventPosition(e);
        var containerPos = this.getAbsolutePosition(this.container);
        this.updateMap(this.centerx + pos[0] - containerPos[0] - this.map_width / 2,
                this.centery + pos[1] - containerPos[1] - this.map_height / 2,
                this.zoom);
        return true;
    },

    articleClicked: function(article, e) {
        stopEventPropagation(e);

        var lthis = this;
        this.infodiv.style.display = 'none';
        this.infodivinterior.innerHTML = '';
        var infolink = document.createElement('a');
        infolink.className = 'evopedianav';
        infolink.href = article.articleLink;
        infolink.onclick = function(e) { lthis.saveDataInHash(); stopEventPropagation(e); return true; };
        infolink.appendChild(document.createTextNode(article.articleName));
        this.infodivinterior.appendChild(infolink);
        this.infodiv.style.top = (article.articleInfodivpos == 'bottom' ? this.map_height * .8 : 0) + 'px';
        this.infodiv.style.display = 'block';
        return false;
    },


    zoomDelta: function(delta) {
        if (this.zoom + delta > 18) {
            delta = 18 - this.zoom;
        } else if (this.zoom + delta < 1) {
            delta = 1 - this.zoom;
        }

        var zoom;
        var centerx;
        var centery
        zoom = this.zoom + delta;
        if (delta > 0) {
            centerx = this.centerx * (1 << delta);
            centery = this.centery * (1 << delta);
        } else {
            centerx = this.centerx / (1 << (-delta));
            centery = this.centery / (1 << (-delta));
        }

        this.updateMap(centerx, centery, zoom);
    },

    browserResized: function() {
        var size = getInnerSize();
        var containerPos = this.getAbsolutePosition(this.container);

        this.map_width = size[0];
        this.map_height = size[1] - containerPos[1];
        this.container.style.width = this.map_width + 'px';
        this.container.style.height = this.map_height + 'px';

        this.infodiv.style.height = (this.map_height * 0.2) + 'px';

        this.updateMap(this.centerx, this.centery, this.zoom);
    },

    saveDataInHash: function() {
        window.location.hash = this.zoom + ',' + this.centerx + ',' + this.centery + ',' + this.repochooser.selectedIndex;
    }
}
