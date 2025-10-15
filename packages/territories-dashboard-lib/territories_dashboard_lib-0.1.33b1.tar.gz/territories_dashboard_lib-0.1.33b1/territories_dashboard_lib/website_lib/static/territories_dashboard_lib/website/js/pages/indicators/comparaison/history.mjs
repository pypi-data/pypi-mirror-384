import {
    getDataset,
    getDates,
    makeChart,
    setBackgroundInDatasets,
} from "../utils.mjs";
import { getIndicatorDataScript, getParams } from "../dom.mjs";
import { formatIndicatorValue } from "../format.mjs";

function getScales(minDate, maxDate, maxValue) {
    return {
        x: {
            beginAtZero: false,
            suggestedMax: maxDate,
            suggestedMin: minDate,
            type: "linear",
            ticks: {
                callback: function (value) {
                    if (typeof value === "string") {
                        return value;
                    }
                    return value % 1 === 0 ? value.toString() : "";
                },
            },
        },
        y: {
            beginAtZero: true,
            suggestedMax: Math.ceil(maxValue * 1.2),
            // stacked: true,
            type: "linear",
            ticks: {
                callback: function (value) {
                    if (typeof value === "string") {
                        return value;
                    }
                    return formatIndicatorValue(value);
                },
            },
        },
    };
}

function getMaxValue(history, comparedHistory) {
    history.map((v) => v.valeur);
    return Math.max(
        ...history.map((v) => v.valeur),
        ...comparedHistory.map((v) => v.valeur)
    );
}

function makeHistoryChart(indicator, history, comparedHistory) {
    const maxValue = getMaxValue(history, comparedHistory);
    const { minDate, maxDate } = getDates(history);

    const ctx = document.querySelector(`#card-${indicator.id} .history-chart`);
    const params = getParams();
    const datasets = [
        getDataset(params.territory_name, history, indicator),
        getDataset(params.cmp_territory_name, comparedHistory, indicator),
    ];
    const chartType = history.length > 1 ? "line" : "bar";
    setBackgroundInDatasets(datasets, true, chartType);
    const data = { datasets };
    const options = {
        layout: {
            padding: {
                top: 30,
            },
        },
        interaction: {
            intersect: false,
            mode: "x",
        },
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
            },
            datalabels: {
                anchor: "end",
                align: "end",
                color: "black",
            },
        },
        scales: getScales(minDate, maxDate, maxValue),
    };

    makeChart(ctx, chartType, data, options);
}

function updateHistoryDOM(indicator) {
    const history = getIndicatorDataScript(indicator, "values");
    if (history) {
        makeHistoryChart(indicator, history.values, history.cmp_values);
    }
}

export { updateHistoryDOM };
