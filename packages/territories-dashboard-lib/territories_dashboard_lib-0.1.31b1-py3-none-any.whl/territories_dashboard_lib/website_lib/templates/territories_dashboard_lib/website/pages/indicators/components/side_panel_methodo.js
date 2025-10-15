const button = document.getElementById("methodo-export-button");
button.addEventListener("click", async () => {
    const indicatorName = button.dataset.indicatorName;
    const indicatorTitle = button.dataset.indicatorTitle;
    const response = await fetch(`/api/indicators/${indicatorName}/methodo/`);

    if (!response.ok) {
        throw new Error("Failed to fetch the PDF file.");
    }

    // Create a download link
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${indicatorTitle}.pdf`;
    a.click();
    window.URL.revokeObjectURL(url);
});
