/* globals html2canvas */

async function exportImageAsync(element, fileName, indicator, graphName) {
    const canvas = await html2canvas(element);
    const image = canvas.toDataURL("image/png", 1.0);
    const tempLink = document.createElement("a");
    tempLink.download = fileName;
    tempLink.href = image;
    document.body.appendChild(tempLink);
    tempLink.click();
    document.body.removeChild(tempLink);
    tempLink.remove();
    fetch("/api/tracking/event/", {
        method: "POST",
        body: JSON.stringify({
            indicator: indicator.name,
            event: "download",
            objet: graphName,
            type: "image",
        }),
    });
}

export { exportImageAsync };
