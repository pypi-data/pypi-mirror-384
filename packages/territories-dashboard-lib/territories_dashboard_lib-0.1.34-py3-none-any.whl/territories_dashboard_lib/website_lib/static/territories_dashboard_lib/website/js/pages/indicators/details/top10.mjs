import { getToolTip, makeChart, setBackgroundInDatasets } from "../utils.mjs";

import { addEmptyGraphMessage } from "./utils.mjs";
import { formatIndicatorValue } from "../format.mjs";
import { getIndicatorDataScript } from "../dom.mjs";

function getPlugins(indicator) {
    return {
        datalabels: {
            display: false,
        },
        tooltip: getToolTip(indicator.unite),
    };
}

function makeTop10Chart(indicator) {
    const top10Data = getIndicatorDataScript(indicator, "top-10");
    if (!top10Data) {
        return;
    }
    const { datasetsTopBarChart: datasets, labelsTopBarChart: labels } =
        top10Data;

    setBackgroundInDatasets(datasets);

    const ctx = document.getElementById("top10Chart");
    const data = {
        labels: labels.map((label, index) => {
            const v = datasets.reduce(
                (acc, dataset) => acc + dataset.data[index],
                0
            );
            if (datasets.length > 0) {
                return `${label} (${formatIndicatorValue(v)} ${
                    indicator.unite
                })`;
            }
            return label;
        }),
        datasets,
    };

    if (data.labels.length === 0) {
        addEmptyGraphMessage(ctx);
        return;
    }

    const options = {
        indexAxis: "y",
        plugins: getPlugins(indicator),
        scales: {
            x: {
                stacked: true,
            },
            y: {
                beginAtZero: true,
                stacked: true,
            },
        },
    };

    makeChart(ctx, "bar", data, options);
}

export { makeTop10Chart };
