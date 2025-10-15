import {
    getIndicatorDataScript,
    getIsAlternativeUnit,
    removeDelaySpinner,
} from "../dom.mjs";
import { formatIndicatorValue } from "../format.mjs";

function updateMainValueDOM(indicator) {
    const mainData = getIndicatorDataScript(indicator, "values");
    if (!mainData) {
        return;
    }
    const data = mainData.values[0];
    const displayAlternative = getIsAlternativeUnit(indicator.id);
    const val = displayAlternative ? data.valeur_alternative : data.valeur;
    removeDelaySpinner(`#card-${indicator.id} .delay-spinner`);
    document.querySelector(
        `#card-${indicator.id} .main-value span:first-child`
    ).textContent = `${formatIndicatorValue(val, { precise: true })}`;
}

export { updateMainValueDOM };
