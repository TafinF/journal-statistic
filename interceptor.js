window.apiMonitor = {
    responses: [],
    clear: function() {
        this.responses = [];
    },
    getJSON: function() {
        return JSON.stringify(this.responses, null, 2);
    },
    getByUrl: function(urlPattern) {
        return this.responses.filter(resp =>
            resp.url.includes(urlPattern)
        );
    }
};
const originalFetch = window.fetch;
window.fetch = function(...args) {
    const url = args[0];
    let fullUrl = url;

    try {
        if (typeof url === 'string' && !url.startsWith('http')) {
            fullUrl = new URL(url, window.location.origin).href;
        }
    } catch (e) {
        fullUrl = url;
    }

    if (typeof fullUrl === 'string' &&
        (fullUrl.includes('/api/') || fullUrl.includes('/graphql'))) {

        const requestId = Date.now() + Math.random().toString(36).substr(2, 9);

        return originalFetch.apply(this, args).then(response => {
            return response.clone().json().then(data => {
                window.apiMonitor.responses.push({
                    id: requestId,
                    url: fullUrl,
                    method: args[1]?.method || 'GET',
                    timestamp: new Date().toISOString(),
                    response: data,
                    status: response.status,
                    headers: Object.fromEntries(response.headers.entries())
                });

                return response;
            }).catch(() => response.clone().text().then(text => {
                window.apiMonitor.responses.push({
                    id: requestId,
                    url: fullUrl,
                    method: args[1]?.method || 'GET',
                    timestamp: new Date().toISOString(),
                    response: text,
                    status: response.status,
                    headers: Object.fromEntries(response.headers.entries())
                });

                return response;
            }));
        });
    }
    return originalFetch.apply(this, args);
};