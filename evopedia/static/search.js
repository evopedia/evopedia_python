function urlencode(params) {
    var parts = new Array();
    for (key in params) {
        parts.push(encodeURIComponent(key) + '=' + encodeURIComponent(params[key]));
    }
    return parts.join("&");
}

function getAbsolutePosition(obj) {
    var x = 0;
    var y = 0;
    var parent = obj;
    while (parent) {
        y += parent.offsetTop;
        x += parent.offsetLeft;
        parent = parent.offsetParent;
    }
    return [x, y];
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


function ArticleSearch() {
    var lthis = this;
    this.input = document.getElementById('searchInput');
    this.setInitialSearchValueFromURL();
    this.input.onkeyup = function(e) { return lthis.inputKeyUp(e || window.event); }
    this.input.focus();

    this.searchForm = document.getElementById('searchForm');
    this.searchForm.onsubmit = function() { lthis.doSearch(); return false; };
    this.searchList = document.getElementById('searchList');
    this.fullSearch = document.getElementById('full_search');
    this.caseSensitive = document.getElementById('case_sensitive');
    this.searchInfo = document.getElementById('searchInfo');

    this.searchList.onload = function() { lthis.searchInfo.style.display = 'none'; };
    this.fullSearch.onchange = function() { lthis.caseSensitive.disabled = !lthis.fullSearch.checked; lthis.doSearch(); };
    this.caseSensitive.disabled = !lthis.fullSearch.checked;
    this.caseSensitive.onchange = function() { lthis.doSearch(); }
    window.onresize = function() { lthis.browserResized(); };

    this.searchTimeout = null;
    this.doSearch();
    window.setTimeout(function() { lthis.browserResized(); }, 10);
}

ArticleSearch.prototype = {
    inputKeyUp: function(e) {
        if (this.searchTimeout != null) {
            window.clearTimeout(this.searchTimeout);
            this.searchTimeout = null;
        }

        var lthis = this;
        this.searchTimeout = window.setTimeout(function() { lthis.doSearch();}, 300);
    },

    setInitialSearchValueFromURL: function() {
        var query = window.location.search;
        var queries = query.split('=');
        if (queries.length > 1) {
            query = queries[queries.length - 1];
        } else {
            query = query.substring(1);
        }
        this.input.value = query;
    },

    doSearch: function() {
        this.searchTimeout = null;
        this.searchInfo.style.display = 'block';
        this.searchList.src = '/search?' +
                urlencode({q: this.input.value,
                        full_search: this.fullSearch.checked ? '1' : '0',
                        case_sensitive: this.caseSensitive.checked ? '1' : '0'});
    },

    browserResized: function() {
        var size = getInnerSize();
        var searchListPos = getAbsolutePosition(this.searchList);
        this.searchList.style.height = (size[1] - searchListPos[1]) + 'px';
    }
}
