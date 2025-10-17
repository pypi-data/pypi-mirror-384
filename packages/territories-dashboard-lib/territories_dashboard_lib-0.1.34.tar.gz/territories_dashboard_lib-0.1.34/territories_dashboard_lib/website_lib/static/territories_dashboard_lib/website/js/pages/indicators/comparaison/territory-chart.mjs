import { getIndicatorDataScript, getParams } from "../dom.mjs";
import { MAX_TERRITORIES_BEFORE_HIDE } from "../enums.mjs";
import { formatIndicatorValue } from "../format.mjs";
import { makeChart, setBackgroundInDatasets } from "../utils.mjs";

function getChartData(histogram, params) {
    const labels = histogram.buckets.map(
        (bucket) =>
            `${formatIndicatorValue(bucket[0])}-${formatIndicatorValue(
                bucket[1]
            )}`
    );
    const dataMain = Object.entries(histogram.values).map((entries) => ({
        x: labels[Number(entries[0]) - 1],
        y: entries[1].length,
        territories: entries[1],
    }));
    const dataCompared = Object.entries(histogram.comparedValues).map(
        (entries) => ({
            x: labels[Number(entries[0]) - 1],
            y: entries[1].length * -1,
            territories: entries[1],
        })
    );
    const datasets = [
        {
            label: params.territory_name.split(" - ")[0],
            data: dataMain,
            backgroundColor: "#6A6AF4",
            barPercentage: 1.0,
        },
        {
            label: params.cmp_territory_name.split(" - ")[0],
            data: dataCompared,
            backgroundColor: "#000091",
            barPercentage: 1.0,
        },
    ];
    setBackgroundInDatasets(datasets);
    return {
        labels: labels,
        datasets,
    };
}

function getScales() {
    const zeroLineWidth = 2;
    return {
        x: {
            beginAtZero: false,
            display: true,
            type: "category",
            stacked: true,
        },
        y: {
            beginAtZero: true,
            display: true,
            stacked: true,
            ticks: {
                callback: function (value) {
                    if (typeof value === "number") {
                        return formatIndicatorValue(Math.abs(value));
                    }
                    return value;
                },
            },
            grid: {
                drawBorder: true,
                color: (context) =>
                    // Couleur distincte pour la ligne du zéro
                    context.tick.value === 0 ? "#000" : "#ccc",
                // Épaisseur de la ligne zéro
                lineWidth: (context) =>
                    context.tick.value === 0 ? zeroLineWidth : 1,
            },
        },
    };
}

function getOptions(params) {
    const { mesh } = params;

    return {
        responsive: true,
        maintainAspectRatio: false,
        minBarLength: 8,
        layout: {
            padding: {
                top: 40,
                right: 100,
            },
        },
        plugins: {
            legend: {
                display: true,
            },
            title: {
                display: true,
                text: "Comparaison des valeurs",
            },
            datalabels: {
                display: false,
            },
            tooltip: {
                callbacks: {
                    label: function (context) {
                        const multiplier = context.datasetIndex === 0 ? 1 : -1;
                        const numberOfTerritories = context.raw.y * multiplier;
                        return numberOfTerritories > MAX_TERRITORIES_BEFORE_HIDE
                            ? `${numberOfTerritories} ${mesh}${
                                  numberOfTerritories > 1 ? "s" : ""
                              }`
                            : context.raw.territories;
                    },
                },
            },
        },
        scales: getScales(),
    };
}

function makeComparedTerritoryChart(indicator) {
    const indicatorData = getIndicatorDataScript(
        indicator,
        "comparison-histogram"
    );
    if (!indicatorData) {
        return;
    }
    const params = getParams();

    const ctx = document.querySelector(
        `#card-${indicator.id} .comparison-chart`
    );
    const chartData = getChartData(indicatorData, params);
    const options = getOptions(params);

    makeChart(ctx, "bar", chartData, options);
}

export { makeComparedTerritoryChart };
