import {
    getDataset,
    getDates,
    makeChart,
    setBackgroundInDatasets,
} from "../utils.mjs";
import { getIndicatorDataScript, getParams } from "../dom.mjs";
import { formatIndicatorValue } from "../format.mjs";

function getScales(indicatorData) {
    const { minDate, maxDate } = getDates(indicatorData);

    function xTicksCallback(value) {
        if (typeof value === "string") {
            return value;
        }
        return value % 1 === 0 ? value.toString() : "";
    }
    function yTicksCallback(value) {
        if (typeof value === "string") {
            return value;
        }

        return formatIndicatorValue(value);
    }

    return {
        x: {
            type: "linear",
            position: "bottom",
            suggestedMax: maxDate,
            suggestedMin: minDate,
            ticks: {
                stepSize: 0.2,
                callback: xTicksCallback,
            },
        },
        y: {
            beginAtZero: true,
            ticks: {
                callback: yTicksCallback,
            },
        },
    };
}

function makeHistoryChart(indicator, indicatorData) {
    const ctx = document.querySelector(`#card-${indicator.id} .history-chart`);
    const params = getParams();
    const datasets = [
        getDataset(params.territory_name, indicatorData, indicator),
    ];
    setBackgroundInDatasets(datasets);
    const data = {
        datasets,
    };
    const options = {
        layout: {
            padding: {
                top: 40,
                right: 100,
            },
        },
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false,
            },
            datalabels: {
                align: "top",
                anchor: "end",
                color: "black",
            },
        },
        scales: getScales(indicatorData),
    };
    const chartType = indicatorData.length > 1 ? "line" : "bar";
    makeChart(ctx, chartType, data, options);
}

function updateHistoryDOM(indicator) {
    const indicatorData = getIndicatorDataScript(indicator, "values");
    if (!indicatorData) {
        return;
    }
    makeHistoryChart(indicator, indicatorData.values);
}

export { updateHistoryDOM };
