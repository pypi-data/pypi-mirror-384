import { getApiUrls, getParams, makeIndicatorDataScript } from "../dom.mjs";
import { getIndicatorFilters } from "../filters.mjs";

import { makeHistogramChart } from "./histogram.mjs";
import { makeProportionsChart } from "./proportions.mjs";
import { makeTables } from "./table.mjs";
import { makeTop10Chart } from "./top10.mjs";

async function fetchHistogram(indicator, apiUrls, searchParams) {
    const response = await fetch(`${apiUrls.histogram}?${searchParams}`);
    if (response.ok) {
        const data = await response.json();
        makeIndicatorDataScript(indicator, "histogram", data);
        makeHistogramChart(indicator);
    }
}

async function fetchTop10(indicator, apiUrls, searchParams) {
    const response = await fetch(`${apiUrls["top-10"]}?${searchParams}`);
    if (response.ok) {
        const data = await response.json();
        makeIndicatorDataScript(indicator, "top-10", data);
        makeTop10Chart(indicator);
    }
}

async function fetchProportions(indicator, apiUrls, searchParams) {
    if (indicator.filters.length > 0) {
        const response = await fetch(`${apiUrls.proportions}?${searchParams}`);
        if (response.ok) {
            const data = await response.json();
            makeIndicatorDataScript(indicator, "proportions", data);
            makeProportionsChart(indicator);
        }
    }
}

function getSearchParams(indicator) {
    const params = getParams();
    const filters = getIndicatorFilters(indicator);
    const filtersQuery = filters
        .map(([dimension, filter]) => `&${dimension}=${filter}`)
        .join("");
    const searchParams = new URLSearchParams(
        `territory=${params.territory_id}-${params.territory_mesh}&submesh=${params.mesh}${filtersQuery}`
    ).toString();
    return searchParams;
}

function callData(indicator) {
    const apiUrls = getApiUrls(indicator);
    const searchParams = getSearchParams(indicator);
    fetchHistogram(indicator, apiUrls, searchParams);
    fetchTop10(indicator, apiUrls, searchParams);
    fetchProportions(indicator, apiUrls, searchParams);
    makeTables();
}

export { callData, getSearchParams };
