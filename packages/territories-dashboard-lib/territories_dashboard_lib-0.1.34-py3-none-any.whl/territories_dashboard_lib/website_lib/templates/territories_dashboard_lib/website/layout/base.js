function updateParamsUrl() {
    const paramsContainer = document.getElementById("params-js");
    if (paramsContainer) {
        const params = JSON.parse(paramsContainer.textContent);
        const currentUrl = new URL(window.location);
        currentUrl.searchParams.delete("territory");
        currentUrl.searchParams.delete("cmp-territory");
        currentUrl.searchParams.delete("mesh");

        if (params.url_params) {
            const newParams = new URLSearchParams(params.url_params);

            for (const [key, value] of newParams.entries()) {
                currentUrl.searchParams.set(key, value);
            }
        }

        window.history.replaceState({}, "", currentUrl.toString());
    }
}

function callAnalytics() {
    const analyticsId = document.querySelector("html").dataset.analytics;
    if (analyticsId) {
        const analyticsUrl =
            "https://audience-sites.din.developpement-durable.gouv.fr/";
        const _paq = (window._paq = window._paq || []);
        _paq.push(["trackPageView"]);
        _paq.push(["enableLinkTracking"]);
        _paq.push(["setTrackerUrl", analyticsUrl + "piwik.php"]);
        _paq.push(["setSiteId", analyticsId]);
        const g = document.createElement("script");
        const s = document.getElementsByTagName("script")[0];
        g.async = true;
        g.src = analyticsUrl + "piwik.js";
        if (s.parentNode) {
            s.parentNode.insertBefore(g, s);
        }
    }
}

document.addEventListener("DOMContentLoaded", function () {
    setTimeout(() => {
        updateParamsUrl();
        callAnalytics();
    }, 500);
});
