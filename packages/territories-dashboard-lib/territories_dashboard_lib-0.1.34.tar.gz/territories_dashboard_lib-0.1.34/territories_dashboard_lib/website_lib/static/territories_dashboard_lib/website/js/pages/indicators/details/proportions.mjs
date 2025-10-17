import { getIndicatorDataScript, getParams } from "../dom.mjs";
import { getToolTip, makeChart, setBackgroundInDatasets } from "../utils.mjs";

import { COLORS } from "../enums.mjs";
import { addEmptyGraphMessage } from "./utils.mjs";
import { formatIndicatorValue } from "../format.mjs";

function getPlugins(indicator, total) {
    function getLabelFromValue(value) {
        return `${formatIndicatorValue(value)} ${indicator.unite}`;
    }
    return {
        datalabels: {
            display: (context) => {
                const chart = context.chart;
                const canvasWidth = chart.canvas.width;
                const value = context.dataset.data[context.dataIndex];
                const barWidth = (value / total) * canvasWidth;
                const label = getLabelFromValue(value);

                // --- measure text width in pixels ---
                const ctx = chart.ctx;
                const font = Chart.helpers.toFont(Chart.defaults.font);
                ctx.font = font.string;
                const labelWidth = ctx.measureText(label).width;

                // Add some padding
                const padding = 4;

                // Only display label if it fits
                return labelWidth + padding < barWidth;
            },
            color: (context) => {
                const bgColor = context.dataset.backgroundColor;
                return COLORS[bgColor] || "white";
            },
            anchor: "center",
            align: "center",
            font: {
                weight: "bold",
            },
            formatter: getLabelFromValue,
        },
        tooltip: getToolTip(indicator.unite),
    };
}

function makeProportionsChart(indicator) {
    const { territory_name: label } = getParams();

    const ctx = document.getElementById("proportionsChart");
    if (ctx === null) {
        return;
    }

    const proportionsData = getIndicatorDataScript(indicator, "proportions");
    if (!proportionsData) {
        return;
    }

    const datasets = proportionsData.values;

    const emptyDatasets = datasets
        .map((ds) => ds.data)
        .flat()
        .every((d) => d === null);
    if (datasets.length === 0 || emptyDatasets) {
        addEmptyGraphMessage(ctx);
        return;
    }

    const total = datasets.map((d) => d.data[0]).reduce((a, b) => a + b, 0);

    setBackgroundInDatasets(datasets);

    const data = {
        labels: [label],
        datasets,
    };
    const options = {
        indexAxis: "y",
        maintainAspectRatio: false,
        plugins: getPlugins(indicator, total),
        scales: {
            x: {
                display: false,
                stacked: true,
            },
            y: {
                display: false,
                stacked: true,
            },
        },
    };

    makeChart(ctx, "bar", data, options);
}

export { makeProportionsChart };
