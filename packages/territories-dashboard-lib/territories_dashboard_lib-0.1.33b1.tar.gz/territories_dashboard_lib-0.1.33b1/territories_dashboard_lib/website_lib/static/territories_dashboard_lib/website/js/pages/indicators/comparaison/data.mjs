import { getApiUrls, getParams, makeIndicatorDataScript } from "../dom.mjs";
import { getIndicatorFilters } from "../filters.mjs";
import { makeComparedTerritoryChart } from "./territory-chart.mjs";
import { updateHistoryDOM } from "./history.mjs";
import { updateMainValues } from "./main-values.mjs";

function getSearchParams(indicator) {
    const params = getParams();
    const filters = getIndicatorFilters(indicator);
    const filtersQuery = filters
        .map(([dimension, filter]) => `&${dimension}=${filter}`)
        .join("");
    const searchParams = new URLSearchParams(
        `submesh=${params.mesh}${filtersQuery}`
    );
    searchParams.set(
        "territory",
        `${params.territory_id}-${params.territory_mesh}`
    );
    searchParams.set(
        "cmp-territory",
        `${params.cmp_territory_id}-${params.cmp_territory_mesh}`
    );

    return searchParams.toString();
}

async function callComparisonHistogram(indicator) {
    const apiUrls = getApiUrls(indicator);
    const searchParams = getSearchParams(indicator);
    const response = await fetch(
        `${apiUrls["comparison-histogram"]}?${searchParams}`
    );
    if (response.ok) {
        const data = await response.json();
        makeIndicatorDataScript(indicator, "comparison-histogram", data);
        makeComparedTerritoryChart(indicator);
    }
}

async function callValues(indicator) {
    const apiUrls = getApiUrls(indicator);
    const searchParams = getSearchParams(indicator, "main");

    const response = await fetch(`${apiUrls.values}?${searchParams}`);
    if (response.ok) {
        const data = await response.json();
        makeIndicatorDataScript(indicator, "values", data);
    }

    if (response.ok) {
        updateMainValues(indicator);
        updateHistoryDOM(indicator);
    }
}

function callData(indicator) {
    callComparisonHistogram(indicator);
    callValues(indicator);
}

export { callData, getSearchParams };
