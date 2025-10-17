import { getApiUrls, getIndicator, getParams } from "../dom.mjs";
import { getIndicatorFilters } from "../filters.mjs";

function addClickEventOnTableHeader(tableContainer) {
    tableContainer.querySelectorAll("thead th").forEach((element) => {
        element.addEventListener("click", () => {
            const orderflow =
                element.dataset.orderflow === "ASC" ? "DESC" : "ASC";
            updateTable({
                tableContainer,
                columnOrder: element.dataset.name,
                columnOrderFlow: orderflow,
                pagination: 1,
                focus: true,
            });
        });
    });
}

function addClickEventOnPagination(tableContainer) {
    tableContainer.querySelectorAll(".fr-pagination__link").forEach((page) => {
        page.addEventListener("click", () => {
            const pagination = page.dataset.page;
            updateTable({ tableContainer, pagination, focus: true });
        });
    });
}

function addOnSelectLimitInput(tableContainer) {
    tableContainer
        .querySelector(".select-table-limit")
        .addEventListener("input", (event) => {
            const limit = event.target.value;
            updateTable({ tableContainer, limit, focus: true });
        });
}

function addOnSearchInput(tableContainer) {
    tableContainer
        .querySelector(".table-search")
        .addEventListener("change", (event) => {
            const search = event.target.value;
            updateTable({ tableContainer, pagination: 1, search, focus: true });
        });
}

function addOnExportButtonClick(tableContainer, isFlows) {
    const params = getParams();
    const indicator = getIndicator();
    const apiUrls = getApiUrls(indicator);

    tableContainer.querySelectorAll(".table-export").forEach((button) => {
        button.addEventListener("click", async () => {
            const searchParams = new URLSearchParams(
                `territory=${params.territory_id}-${params.territory_mesh}&submesh=${params.mesh}`
            );
            if (button.dataset.year) {
                searchParams.set("year", button.dataset.year);
            }
            if (isFlows) {
                searchParams.set("flows", true);
            }
            const response = await fetch(
                `${apiUrls["details-table-export"]}?${searchParams.toString()}`
            );
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                const name = isFlows ? "flux" : indicator.name;
                a.download = `${name}${
                    button.dataset.year ? `_${button.dataset.year}` : ""
                }_export.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            }
        });
    });
}

function addFocusToLine(tableContainer) {
    const table = tableContainer.querySelector("table");
    const lineFocus = table.dataset.linefocus;
    if (lineFocus) {
        const line = table.querySelector(`tbody > tr:nth-child(${lineFocus})`);
        line.focus();
    }
}

function getDefaultValue({
    table,
    columnOrder,
    columnOrderFlow,
    pagination,
    limit,
    search,
}) {
    let colOrder = columnOrder;
    let colOrderFlow = columnOrderFlow;
    if (table && colOrder === undefined) {
        colOrder = table.dataset.sort;
    }
    if (table && colOrderFlow === undefined) {
        colOrderFlow = table.dataset.orderflow;
    }
    let newLimit = limit;
    if (table && newLimit === undefined) {
        newLimit = table.dataset.limit;
    }
    let newSearch = search;
    if (table && newSearch === undefined) {
        newSearch = table.dataset.search;
    }
    let page = pagination;
    if (table && page === undefined) {
        page = table.dataset.page;
    }

    return { colOrder, colOrderFlow, newLimit, page, newSearch };
}

function getSearchParams({
    indicator,
    isFlows,
    colOrder,
    colOrderFlow,
    newLimit,
    newSearch,
    page,
    table,
    focus,
}) {
    const params = getParams();
    const filters = getIndicatorFilters(indicator);
    let filtersQuery = filters
        .map(([dimension, filter]) => `&${dimension}=${filter}`)
        .join("");
    if (isFlows) {
        filtersQuery = "";
    }
    const searchParams = new URLSearchParams(
        `territory=${params.territory_id}-${params.territory_mesh}&submesh=${params.mesh}${filtersQuery}`
    );
    if (colOrder !== undefined) {
        searchParams.set("column_order", colOrder);
    }
    if (colOrderFlow !== undefined) {
        searchParams.set("column_order_flow", colOrderFlow);
    }
    if (page !== undefined) {
        searchParams.set("pagination", page);
    }
    if (table) {
        searchParams.set("previous_limit", table.dataset.limit);
    }
    if (newLimit !== undefined) {
        searchParams.set("limit", newLimit);
    }
    if (newSearch !== undefined && newSearch !== "") {
        searchParams.set("search", newSearch);
    }
    if (isFlows) {
        searchParams.set("flows", true);
    }
    if (focus) {
        searchParams.set("focus", true);
    }
    return searchParams;
}

async function updateTable({
    tableContainer,
    columnOrder,
    columnOrderFlow,
    pagination,
    limit,
    search,
    focus,
}) {
    const isFlows = tableContainer.dataset.source === "flows";
    const indicator = getIndicator();
    const apiUrls = getApiUrls(indicator);
    const table = tableContainer.querySelector("table");
    const { colOrder, colOrderFlow, newLimit, page, newSearch } =
        getDefaultValue({
            table,
            columnOrder,
            columnOrderFlow,
            pagination,
            limit,
            search,
        });
    const searchParams = getSearchParams({
        indicator,
        isFlows,
        table,
        colOrder,
        colOrderFlow,
        newLimit,
        page,
        newSearch,
        focus,
    });
    const response = await fetch(
        `${apiUrls["details-table"]}?${searchParams.toString()}`
    );
    if (response.ok) {
        const htmlData = await response.text();
        tableContainer.innerHTML = htmlData;
        addClickEventOnTableHeader(tableContainer);
        addClickEventOnPagination(tableContainer);
        addOnSelectLimitInput(tableContainer);
        addOnSearchInput(tableContainer);
        addOnExportButtonClick(tableContainer, isFlows);
        addFocusToLine(tableContainer);
    }
}

function makeTables() {
    const tableContainers = document.querySelectorAll(".data-table");
    tableContainers.forEach((tableContainer) => {
        updateTable({ tableContainer });
    });
}

export { makeTables };
