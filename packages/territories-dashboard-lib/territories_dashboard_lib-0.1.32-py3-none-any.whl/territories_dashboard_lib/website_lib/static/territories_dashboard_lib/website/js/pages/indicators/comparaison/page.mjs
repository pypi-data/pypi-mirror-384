/* globals Chart, ChartDataLabels */
import { callData, getSearchParams } from "./data.mjs";
import { delaySpinner, getClosestIndicator } from "../dom.mjs";
import { handleFilterClick, initializeFilters } from "../filters.mjs";
import { addSidePanelListener, openMethodoSidePanel } from "../side_panel.mjs";

import { exportImageAsync } from "../export-graph.mjs";
import { exportToCSV } from "../export.mjs";

Chart.register(
    Chart.CategoryScale,
    Chart.LinearScale,
    Chart.BarElement,
    Chart.PointElement,
    Chart.LineElement,
    Chart.Title,
    Chart.Tooltip,
    Chart.Legend,
    Chart.LogarithmicScale,
    ChartDataLabels
);

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

    indicatorCard
        .querySelectorAll('button[aria-controls="slide-panel-methodo"]')
        .forEach((button) => {
            button.addEventListener("click", () => {
                openMethodoSidePanel(indicator, button);
            });
        });
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

document.addEventListener("DOMContentLoaded", () => {
    const withPattern = localStorage.getItem("pattern") === "true";
    document.querySelectorAll(".pattern-toggle").forEach((button) => {
        button.checked = withPattern;
        button.addEventListener("click", () => {
            localStorage.setItem("pattern", button.checked ? "true" : "false");
            setTimeout(() => {
                document
                    .querySelectorAll(".indicator-card")
                    .forEach((indicatorCard) => {
                        const indicator = getClosestIndicator(indicatorCard);
                        callData(indicator);
                    });
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
