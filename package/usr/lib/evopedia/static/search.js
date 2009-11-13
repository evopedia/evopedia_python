function makeHTTPRequest(url, onReady) {
    var request;
    var onReadyFunc = onReady;
    if (window.XMLHttpRequest) {
        request = new XMLHttpRequest();
    } else if (window.ActiveXObject) {
        request = new ActiveXObject("Microsoft.XMLHTTP");
    }
    request.open('GET', url, true);
    request.onreadystatechange = function() {
        if (request.readyState != 4) return;
        onReadyFunc(request, request.status == '200');
    }
    request.send(null);
    return request;
}

function urlencode(params) {
    var parts = new Array();
    for (key in params) {
        parts.push(encodeURIComponent(key) + '=' + encodeURIComponent(params[key]));
    }
    return parts.join("&");
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


function ArticleSearch() {
    var lthis = this;
    this.input = document.getElementById('searchInput');
    this.input.onkeyup = function(e) { return lthis.inputKeyUp(e || window.event); }
    this.input.focus();
    this.searchList = document.getElementById('searchList');

    this.searchTimeout = null;
}

ArticleSearch.prototype = {
    inputKeyUp: function(e) {
        if (this.searchTimeout != null) {
            window.clearTimeout(this.searchTimeout);
            this.searchTimeout = null;
        }

        //if (this.input.value.length < 3) return;

        var lthis = this;
        this.searchTimeout = window.setTimeout(function() { lthis.doSearch();}, 1200);
    },

    doSearch: function() {
        this.searchTimeout = null;
        var lthis = this;
        makeHTTPRequest('/search?' + urlencode({q: this.input.value}),
                function(request, success) { lthis.showSearchResults(request, success); });

        this.searchList.innerHTML = '';
        this.searchList.appendChild(document.createTextNode('searching...'));
    },

    showSearchResults: function(request, success) {
        this.searchList.innerHTML = '';

        if (!success) {
            this.searchList.appendChild(document.createTextNode('Error contacting server.'));
            return;
        }

        var errors = request.responseXML.getElementsByTagName('error');
        if (errors.length > 0) {
            this.searchList.appendChild(document.createTextNode('Error: ' + getNodeContent(errors[0])));
        } else {
            var listobj = request.responseXML.getElementsByTagName('list')[0];
            if (listobj == null) {
                this.searchList.appendChild(document.createTextNode('Invalid server response.'));
                return;
            }
            var list = request.responseXML.getElementsByTagName('article');
            for (var i = 0; i < list.length; i ++) {
                var name = list[i].getAttribute('name');
                var url = list[i].getAttribute('url');
                var link = document.createElement('a');
                link.className = "evopedianav";
                link.href = url;
                link.appendChild(document.createTextNode(name));
                this.searchList.appendChild(link);
                this.searchList.appendChild(document.createElement('br'));
            }
            if (list.length == 0) {
                this.searchList.appendChild(document.createTextNode('no results'));
            } else if (listobj.getAttribute('complete') != '1') {
                this.searchList.appendChild(document.createTextNode('...'));
            }
        }
    }
}
