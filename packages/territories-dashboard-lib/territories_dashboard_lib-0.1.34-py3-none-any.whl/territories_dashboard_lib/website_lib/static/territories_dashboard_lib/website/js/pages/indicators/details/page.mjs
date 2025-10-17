/* globals Chart, ChartDataLabels */

import { callData, getSearchParams } from "./data.mjs";
import {
    handleFilterClick,
    initializeFilters,
    updateFiltersReminder,
    updateUrlWithFilters,
} from "../filters.mjs";
import { addSidePanelListener, openMethodoSidePanel } from "../side_panel.mjs";

import { exportImageAsync } from "../export-graph.mjs";
import { exportToCSV } from "../export.mjs";
import { makeMap } from "./map.mjs";
import { makeProportionsChart } from "./proportions.mjs";
import { makeSankeyGraph } from "./sankey.mjs";
import { makeTop10Chart } from "./top10.mjs";

Chart.register(
    Chart.CategoryScale,
    Chart.LinearScale,
    Chart.BarElement,
    Chart.Title,
    Chart.Tooltip,
    Chart.Legend,
    ChartDataLabels
);

const indicator = JSON.parse(
    document.getElementById("indicator-js").textContent
);
initializeFilters(indicator);
callData(indicator);
makeMap(indicator);
makeSankeyGraph(indicator);
const openMethodoButton = document.querySelector(
    'button[aria-controls="slide-panel-methodo"]'
);
openMethodoButton.addEventListener("click", () => {
    openMethodoSidePanel(indicator, openMethodoButton);
});
document.querySelectorAll(".filter-tag").forEach((button) => {
    button.addEventListener("click", async () => {
        await handleFilterClick(indicator);
        updateUrlWithFilters();
        updateFiltersReminder(indicator);
        callData(indicator);
    });
});
updateUrlWithFilters();
updateFiltersReminder(indicator);

document
    .querySelectorAll('button[data-type="export-png"]')
    .forEach((button) => {
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

document
    .querySelectorAll('button[data-type="export-csv"]')
    .forEach((button) => {
        button.addEventListener("click", () => {
            button.setAttribute("disabled", "true");
            const searchParams = getSearchParams(indicator);
            exportToCSV(button, indicator, button.dataset.route, searchParams);
        });
    });

document.addEventListener("DOMContentLoaded", () => {
    const withPattern = localStorage.getItem("pattern") === "true";
    document.querySelectorAll(".pattern-toggle").forEach((button) => {
        button.checked = withPattern;
        button.addEventListener("click", () => {
            localStorage.setItem("pattern", button.checked ? "true" : "false");
            setTimeout(() => {
                makeProportionsChart(indicator);
                makeTop10Chart(indicator);
            }, 100);
            document.querySelectorAll(".pattern-toggle").forEach((b) => {
                const withUpdatedPattern =
                    localStorage.getItem("pattern") === "true";
                b.checked = withUpdatedPattern;
            });
        });
    });
    addSidePanelListener();
});
