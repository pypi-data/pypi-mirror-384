import {
    getIndicatorDataScript,
    getIsAlternativeUnit,
    removeDelaySpinner,
} from "../dom.mjs";
import { formatIndicatorValue } from "../format.mjs";

function updateStatisticsDOM(indicator) {
    const data = getIndicatorDataScript(indicator, "statistics");
    if (!data) {
        return;
    }
    const displayAlternative = getIsAlternativeUnit(indicator.id);
    const alternative = displayAlternative ? "_alternative" : "";
    ["min", "med", "max"].forEach((prefix) => {
        removeDelaySpinner(`#card-${indicator.id} .delay-spinner`);
        const key = `${prefix}${alternative}`;
        const name = data[`code_${key}_name`];
        if (name !== undefined) {
            document.querySelector(
                `#card-${indicator.id} .${prefix}-name`
            ).textContent = name;
        }
        const value = data[key];
        document.querySelector(
            `#card-${indicator.id} .${prefix}-value > span:first-child`
        ).textContent =
            value === undefined ? "-" : `${formatIndicatorValue(value)}`;
        const count = data[`count_${key}`];
        if (count !== undefined) {
            const text =
                count > 1
                    ? `+${count - 1} autre${count - 1 > 1 ? "s" : ""}`
                    : "";
            document.querySelector(
                `#card-${indicator.id} .${prefix}-count`
            ).textContent = text;
        }
    });
}

export { updateStatisticsDOM };
