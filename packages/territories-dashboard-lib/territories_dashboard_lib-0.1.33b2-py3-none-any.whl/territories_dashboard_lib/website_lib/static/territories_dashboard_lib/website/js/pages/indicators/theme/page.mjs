/* globals Chart, ChartDataLabels */

import {
    delaySpinner,
    getApiUrls,
    getClosestIndicator,
    getParams,
    makeIndicatorDataScript,
} from "../dom.mjs";

import {
    getIndicatorFilters,
    handleFilterClick,
    initializeFilters,
} from "../filters.mjs";
import { addSidePanelListener, openMethodoSidePanel } from "../side_panel.mjs";

import { exportImageAsync } from "../export-graph.mjs";
import { exportToCSV } from "../export.mjs";

import { updateHistoryDOM } from "./history.mjs";
import { updateMainValueDOM } from "./main-value.mjs";
import { updateStatisticsDOM } from "./statistics.mjs";

Chart.register(
    Chart.CategoryScale,
    Chart.LinearScale,
    Chart.BarElement,
    Chart.Title,
    Chart.Tooltip,
    Chart.Legend,
    ChartDataLabels
);

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
    [
        [
            "values",
            (ind) => {
                updateMainValueDOM(ind);
                updateHistoryDOM(ind);
            },
        ],
        ["statistics", updateStatisticsDOM],
    ].forEach(async ([key, callbackUpdateDOM]) => {
        const response = await fetch(`${apiUrls[key]}?${searchParams}`);
        if (response.ok) {
            const data = await response.json();
            makeIndicatorDataScript(indicator, key, data);
            callbackUpdateDOM(indicator);
        }
    });
}

function makeIndicatorCards() {
    const subThemes = JSON.parse(
        document.getElementById("sub-themes-js").textContent
    );
    subThemes.forEach((subTheme) => {
        subTheme.indicators.forEach((indicator) => {
            initializeFilters(indicator);
            callData(indicator);
        });
    });
}

function toggleIndicatorUnit(input) {
    const indicator = getClosestIndicator(input);
    const unity = input.checked ? indicator.unite_alternative : indicator.unite;
    const accessibleName = input.checked
        ? indicator.unite_alternative_nom_accessible
        : indicator.unite_nom_accessible;
    Array.from(
        document.querySelectorAll(`#card-${indicator.id} .unite`)
    ).forEach((node) => {
        node.innerText = unity;
        node.setAttribute("aria-label", accessibleName);
    });
    const ariaLiveMessage = input.checked
        ? `L'unité affichée est : ${indicator.unite_alternative_nom_accessible}`
        : `L'unité affichée est : ${indicator.unite_nom_accessible}`;
    document.getElementById(`${indicator.id}-toggle-unit-messages`).innerText =
        ariaLiveMessage;
    updateMainValueDOM(indicator);
    updateStatisticsDOM(indicator);
    updateHistoryDOM(indicator);
}

delaySpinner();
makeIndicatorCards();
document.querySelectorAll(".indicator-card").forEach((indicatorCard) => {
    const indicator = getClosestIndicator(indicatorCard);

    indicatorCard.querySelectorAll(".filter-tag").forEach((button) => {
        button.addEventListener("click", async () => {
            await handleFilterClick(indicator);
            callData(indicator);
        });
    });

    indicatorCard.querySelectorAll(".toggle-unite").forEach((input) => {
        input.addEventListener("input", (event) => {
            toggleIndicatorUnit(event.target);
        });
    });

    indicatorCard
        .querySelectorAll('button[aria-controls="slide-panel-methodo"]')
        .forEach((button) => {
            button.addEventListener("click", () => {
                openMethodoSidePanel(indicator, button);
            });
        });
});

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".toggle-unite").forEach((input) => {
        toggleIndicatorUnit(input);
    });
    addSidePanelListener();
});

document
    .querySelectorAll('button[data-type="export-csv"]')
    .forEach((button) => {
        const indicator = getClosestIndicator(button);
        button.addEventListener("click", () => {
            button.setAttribute("disabled", "true");
            const searchParams = getSearchParams(indicator);
            exportToCSV(button, indicator, button.dataset.route, searchParams);
        });
    });

document
    .querySelectorAll('button[data-type="export-png"]')
    .forEach((button) => {
        const indicator = getClosestIndicator(button);
        button.addEventListener("click", async () => {
            button.setAttribute("disabled", "true");
            // need to wait a small amount of time for DOM update
            await new Promise((resolve) => setTimeout(resolve, 50));
            await exportImageAsync(
                button.parentElement.previousElementSibling,
                `${indicator.name} - ${button.dataset.title}`,
                indicator,
                button.dataset["trackingobjet"]
            );
            button.removeAttribute("disabled");
        });
    });
