/* eslint-disable no-magic-numbers */
import { MILLIONS, THOUSANDS } from "./enums.mjs";

function removeUseless0(value) {
    let newValue = value;
    if (newValue.indexOf(".") > 0) {
        if (newValue.slice(-2) === "00") {
            newValue = newValue.slice(0, -2);
        }
        if (newValue.slice(-1) === "0") {
            newValue = newValue.slice(0, -1);
        }
        if (newValue.slice(-1) === ".") {
            newValue = newValue.slice(0, -1);
        }
    }
    return newValue;
}

function getPrecision(value, forceInteger) {
    if (forceInteger) {
        return value.toFixed(0);
    }
    return value.toFixed(1);
}

function formatIndicatorValue(
    value,
    { forceInteger = false, precise = false } = {}
) {
    if (value === undefined || value === null || isNaN(value)) {
        return "-";
    }
    let nb = null;

    if (Math.abs(value) > 999 && precise) {
        nb = new Intl.NumberFormat("fr-FR").format(Math.round(value));
    } else if (Math.abs(value) > 999999) {
        nb =
            removeUseless0(
                getPrecision(
                    (Math.sign(value) * Math.abs(value)) / 1000000,
                    forceInteger
                )
            ) + MILLIONS;
    } else if (Math.abs(value) > 999) {
        nb =
            removeUseless0(
                getPrecision(
                    (Math.sign(value) * Math.abs(value)) / 1000,
                    forceInteger
                )
            ) + THOUSANDS;
    } else {
        nb = removeUseless0(getPrecision(value, forceInteger));
    }
    nb = nb.replace(".", ",");
    return nb;
}

export { formatIndicatorValue };
