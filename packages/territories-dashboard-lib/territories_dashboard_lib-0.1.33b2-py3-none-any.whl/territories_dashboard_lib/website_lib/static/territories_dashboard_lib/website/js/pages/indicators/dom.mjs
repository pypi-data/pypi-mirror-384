function fillMethodoSidePanel(indicator) {
    const container = document.getElementById(
        "slide-panel-content-methodo-markdown"
    );
    container.innerHTML = indicator.methodo_html;
    const exportButton = document.getElementById("methodo-export-button");
    exportButton.dataset.indicatorName = indicator.name;
    exportButton.dataset.indicatorTitle = indicator.title;
    document.getElementById("slide-panel-methodo-indicator-title").textContent =
        indicator.title;
    document.getElementById("slide-panel-methodo-theme-title").textContent =
        indicator.theme;
}

function getClosestIndicator(element) {
    const indicatorId = element.closest(".indicator-card").dataset.indicator;
    return JSON.parse(document.getElementById(indicatorId).textContent);
}

function getIndicator() {
    return JSON.parse(document.getElementById("indicator-js").textContent);
}

function getScriptId(indicator, key) {
    return `${indicator.id}-data-${key}`;
}

function makeIndicatorDataScript(indicator, key, data) {
    const scriptId = getScriptId(indicator, key);

    const existingScript = document.getElementById(scriptId);
    if (existingScript) {
        existingScript.remove();
    }

    const script = document.createElement("script");
    script.id = scriptId;
    script.type = "application/json";
    script.textContent = JSON.stringify(data);

    let container = document.getElementById(`card-${indicator.id}`);
    if (container === null) {
        container = document.querySelector("body");
    }
    container.insertBefore(script, container.firstChild);
}

function getIndicatorDataScript(indicator, key) {
    const scriptId = getScriptId(indicator, key);
    const script = document.getElementById(scriptId);
    return script ? JSON.parse(script.textContent) : null;
}

function getIsAlternativeUnit(indicatorId) {
    const input = document.getElementById(`${indicatorId}-toggle-unit`);
    return input && input.checked;
}

function getParams() {
    return JSON.parse(document.getElementById("params-js").textContent);
}

function getApiUrls(indicator) {
    return JSON.parse(
        document.getElementById(`${indicator.id}-api-urls`).textContent
    );
}

function removeDelaySpinner(selector) {
    document.querySelectorAll(selector).forEach((el) => {
        el.classList.remove("delay-spinner");
    });
}

function delaySpinner() {
    setTimeout(() => {
        removeDelaySpinner(".delay-spinner");
    }, 1000);
}

export {
    delaySpinner,
    getClosestIndicator,
    fillMethodoSidePanel,
    makeIndicatorDataScript,
    getIndicatorDataScript,
    getIsAlternativeUnit,
    getParams,
    getIndicator,
    getApiUrls,
    removeDelaySpinner,
};
