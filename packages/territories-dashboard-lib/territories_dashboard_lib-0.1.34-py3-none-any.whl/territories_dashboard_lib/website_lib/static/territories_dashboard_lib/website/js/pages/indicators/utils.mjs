import { getIsAlternativeUnit } from "./dom.mjs";
import { COLORS, PATTERNS } from "./enums.mjs";
import { formatIndicatorValue } from "./format.mjs";

function _getDataInDatasets(values, indicator) {
    const displayAlternative = getIsAlternativeUnit(indicator.id);

    return values.map((value) => {
        const v = displayAlternative ? value.valeur_alternative : value.valeur;
        const isPercent =
            (displayAlternative
                ? indicator.unite_alternative
                : indicator.unite) === "%";
        return {
            x: value.annee,
            label: `${formatIndicatorValue(v)}${isPercent ? "%" : ""}`,
            y: v,
        };
    });
}

export function getDataset(label, values, indicator) {
    return {
        label: label,
        data: _getDataInDatasets(values, indicator),
    };
}

export function getToolTip(unite) {
    return {
        enabled: true,
        callbacks: {
            label: function (context) {
                const value = context.raw;
                const prefix =
                    context.dataset.label === unite
                        ? ""
                        : ` ${context.dataset.label}: `;
                return `${prefix} ${formatIndicatorValue(value, {
                    precise: true,
                })} ${unite}`;
            },
        },
    };
}

export function getDates(values) {
    const years = values.map((value) => value.annee);
    const minDate = Math.min(...years) - 1;
    const minNumberOfYears = 3;
    let maxDate = Math.max(...years);
    if (maxDate - minDate < minNumberOfYears) {
        maxDate += 1;
    }

    return { minDate, maxDate };
}

export function setBackgroundInDatasets(
    datasets,
    pattern = true,
    chartType = "bar"
) {
    const backgrounds = Object.keys(COLORS);
    const withPattern = localStorage.getItem("pattern") === "true";
    datasets.forEach((dataset, index) => {
        const initialColor = dataset.color ? dataset.color : backgrounds[index];
        // patternomaly library
        const color =
            pattern && chartType === "bar" && withPattern && window.pattern
                ? window.pattern.draw(PATTERNS[index], initialColor, "white")
                : initialColor;
        dataset.backgroundColor = color;
        dataset.borderColor = color;
        if (chartType === "line" && pattern && withPattern && index % 2 === 1) {
            dataset.borderDash = [5, 5];
        }
    });
}

export function makeChart(ctx, type, data, options) {
    const oldChart = Chart.getChart(ctx);
    if (oldChart) {
        oldChart.destroy();
    }

    new Chart(ctx, {
        type,
        data,
        options,
    });
}
