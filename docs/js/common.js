/**
 * Shared utilities for Boe Eno Moto search pages.
 */

function escapeHtml(text) {
    if (!text) return '';
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function highlightMatches(text, indices) {
    if (!text || !indices || indices.length === 0) return escapeHtml(text);

    var result = '';
    var lastIndex = 0;
    var sortedIndices = indices.sort(function(a, b) { return a[0] - b[0]; });

    for (var i = 0; i < sortedIndices.length; i++) {
        var start = sortedIndices[i][0];
        var end = sortedIndices[i][1];
        result += escapeHtml(text.slice(lastIndex, start));
        result += '<span class="highlight">' + escapeHtml(text.slice(start, end + 1)) + '</span>';
        lastIndex = end + 1;
    }
    result += escapeHtml(text.slice(lastIndex));
    return result;
}

function debounce(func, wait) {
    var timeout;
    return function() {
        var context = this, args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(function() { func.apply(context, args); }, wait);
    };
}

/**
 * Initialize a search page with Fuse.js fuzzy search.
 *
 * @param {Object} config
 * @param {Array}  config.data         - Array of data entries
 * @param {Array}  config.fuseKeys     - Fuse.js key definitions [{name, weight}]
 * @param {string} config.filterField  - Field name to filter by (e.g. 'pos')
 * @param {string} config.filterElementId - ID of the <select> filter element
 * @param {Function} config.renderEntry - function(entry, matchMap) → HTML string
 * @param {Object} config.labels       - UI strings: {results, emptyTitle, emptyText,
 *                                        noResults, noResultsHint, overflow}
 * @param {Function} [config.filterFn] - Optional custom filter function(entry, filterValue) → boolean
 * @param {Function} [config.onResults] - Optional callback after results are rendered
 */
function initSearchPage(config) {
    var fuse = new Fuse(config.data, {
        keys: config.fuseKeys,
        threshold: 0.4,
        ignoreLocation: true,
        includeMatches: true,
        minMatchCharLength: 2
    });

    var searchInput = document.getElementById('search-input');
    var filterSelect = config.filterElementId ? document.getElementById(config.filterElementId) : null;
    var resultsContainer = document.getElementById('results');
    var statsDiv = document.getElementById('stats');
    var currentResults = [];

    var defaultFilterFn = function(entry, filterValue) {
        return entry[config.filterField] === filterValue;
    };
    var filterFn = config.filterFn || defaultFilterFn;

    function search() {
        var query = searchInput.value.trim();
        var selectedFilter = filterSelect ? filterSelect.value : '';

        if (query.length < 2) {
            if (selectedFilter) {
                currentResults = config.data
                    .filter(function(item) { return filterFn(item, selectedFilter); })
                    .map(function(item) { return { item: item }; });
            } else {
                resultsContainer.innerHTML =
                    '<div class="empty-state">' +
                    '<h2>' + config.labels.emptyTitle + '</h2>' +
                    '<p>' + config.labels.emptyText + '</p>' +
                    '</div>';
                statsDiv.textContent = '';
                return;
            }
        } else {
            currentResults = fuse.search(query);
            if (selectedFilter) {
                currentResults = currentResults.filter(function(result) {
                    return filterFn(result.item, selectedFilter);
                });
            }
        }

        var count = currentResults.length;
        statsDiv.textContent = count + ' ' + config.labels.results(count);

        if (count === 0) {
            resultsContainer.innerHTML =
                '<div class="empty-state">' +
                '<h2>' + config.labels.noResults + '</h2>' +
                '<p>' + config.labels.noResultsHint + '</p>' +
                '</div>';
        } else {
            var displayResults = currentResults.slice(0, 100);
            var html = displayResults.map(function(result) {
                var entry = result.item || result;
                var matchMap = {};
                if (result.matches) {
                    for (var i = 0; i < result.matches.length; i++) {
                        matchMap[result.matches[i].key] = result.matches[i].indices;
                    }
                }
                return config.renderEntry(entry, matchMap);
            }).join('');

            if (count > 100) {
                html += '<div class="empty-state"><p>' + config.labels.overflow(count) + '</p></div>';
            }

            resultsContainer.innerHTML = html;
            if (config.onResults) config.onResults();
        }
    }

    searchInput.addEventListener('input', debounce(search, 200));
    if (filterSelect) filterSelect.addEventListener('change', search);

    // Auto-search from URL query parameter (e.g. ?search=term)
    var urlParams = new URLSearchParams(window.location.search);
    var initialQuery = urlParams.get('search');
    if (initialQuery) {
        searchInput.value = initialQuery;
        search();
    }

    searchInput.focus();

    return { fuse: fuse, search: search };
}
