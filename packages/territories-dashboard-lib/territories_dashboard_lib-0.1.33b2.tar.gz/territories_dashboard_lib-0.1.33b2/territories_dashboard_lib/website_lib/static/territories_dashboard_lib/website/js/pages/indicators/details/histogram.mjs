import { getIndicatorDataScript, getParams } from "../dom.mjs";
import {
    getMeshLevelTitle,
    MAX_TERRITORIES_BEFORE_HIDE,
    MILLIONS,
    SHORT_MESH_NUMBER_OF_LETTERS,
    THOUSANDS,
} from "../enums.mjs";
import { makeChart, setBackgroundInDatasets } from "../utils.mjs";

import { addEmptyGraphMessage } from "./utils.mjs";
import { formatIndicatorValue } from "../format.mjs";

function getDatalabels(dataset, mesh) {
    return {
        anchor: "end",
        align: "end",
        color: "black",
        font: {
            weight: "bold",
        },
        formatter: function (value, context) {
            const formatted = formatIndicatorValue(value.y, {
                forceInteger: true,
            });
            if (!formatted) {
                return "";
            }
            if (
                context.active &&
                dataset.comments.length > context.dataIndex &&
                dataset.comments[context.dataIndex] !== "" &&
                dataset.comments[context.dataIndex].split("\n").length <=
                    MAX_TERRITORIES_BEFORE_HIDE
            ) {
                return dataset.comments[context.dataIndex];
            }
            return `${formatted} ${getMeshLevelTitle(mesh).slice(
                0,
                SHORT_MESH_NUMBER_OF_LETTERS
            )}.${value.y > 1 ? "s" : ""}`;
        },
    };
}

function getScales(labels, maxFromData) {
    return {
        x: {
            beginAtZero: false,
            grid: {
                display: false,
            },
            ticks: {
                callback: function (value) {
                    function formatLabel(v) {
                        if (
                            [THOUSANDS, MILLIONS].some((s) =>
                                labels[v].includes(s)
                            )
                        ) {
                            return labels[v];
                        }
                        return formatIndicatorValue(
                            Number.parseFloat(labels[v]),
                            { forceInteger: true }
                        );
                    }
                    if (value === labels.length - 1) {
                        return `${formatLabel(value)} +`;
                    }
                    return `${formatLabel(value)} - ${formatLabel(value + 1)}`;
                },
            },
        },
        y: {
            beginAtZero: true,
            grid: {
                display: false,
            },
            max:
                maxFromData <= MAX_TERRITORIES_BEFORE_HIDE
                    ? maxFromData + 1
                    : maxFromData,
        },
    };
}

export function makeHistogramChart(indicator) {
    const { mesh } = getParams();
    const histogramData = getIndicatorDataScript(indicator, "histogram");
    if (!histogramData) {
        return;
    }
    const { datasetsHistogramBarChart: dataset, deciles } = histogramData;

    const ctx = document.getElementById("histogramChart");
    if (Object.keys(dataset).length === 0) {
        addEmptyGraphMessage(ctx);
        return;
    }

    const labels = deciles.map((decile) => formatIndicatorValue(decile));

    setBackgroundInDatasets([dataset], false);

    const data = {
        labels: labels,
        datasets: [dataset],
    };
    const maxFromData = Math.max(...dataset.data.map((data) => data.y));
    const options = {
        indexAxis: "x",
        layout: {
            padding: {
                top: 30,
            },
        },
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false,
            },
            tooltip: {
                enabled: false,
            },
            datalabels: getDatalabels(dataset, mesh),
        },
        scales: getScales(labels, maxFromData),
    };

    makeChart(ctx, "bar", data, options);
}
