import {
    getIndicatorDataScript,
    getParams,
    removeDelaySpinner,
} from "../dom.mjs";
import { formatIndicatorValue } from "../format.mjs";

function updateMainValues(indicator) {
    const params = getParams();
    const data = getIndicatorDataScript(indicator, "values");
    if (!data) {
        return;
    }
    removeDelaySpinner(`#card-${indicator.id} .delay-spinner`);

    const element = document.querySelector(
        `#card-${indicator.id} .territory-value > span:first-child`
    );

    const value = formatIndicatorValue(data.values[0].valeur, {
        precise: true,
    });
    element.innerHTML = `<strong>${params.territory_name} : </strong>${value}`;

    const cmpElement = document.querySelector(
        `#card-${indicator.id} .compared-territory-value > span:first-child`
    );
    const cmpValue = formatIndicatorValue(data.cmp_values[0].valeur, {
        precise: true,
    });
    cmpElement.innerHTML = `<strong>${params.cmp_territory_name} : </strong>${cmpValue}`;
}

export { updateMainValues };
