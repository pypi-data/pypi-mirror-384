import { getApiUrls } from "./dom.mjs";

async function exportToCSV(button, indicator, route, searchParams) {
    const apiUrls = getApiUrls(indicator);
    const response = await fetch(`${apiUrls[route]}export/?${searchParams}`);
    button.removeAttribute("disabled");
    if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${indicator.name} - ${button.dataset.title}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
}

export { exportToCSV };
