function getIndicatorFilters(indicator) {
    return Array.from(
        document.querySelectorAll(
            `.filter-tag[aria-pressed="true"][data-indicator="${indicator.id}"]`
        )
    ).map((button) => [button.dataset.dimension, button.innerText]);
}

function getCurrentFiltersForIndicatorAndDimension(indicator, dimension) {
    return Array.from(
        document.querySelectorAll(
            `.filter-tag[aria-pressed="true"][data-indicator="${indicator.id}"][data-dimension="${dimension}"]`
        )
    ).map((button) => button.innerText);
}

function arrayAreSameSet(arr1, arr2) {
    const xs = new Set(arr1);
    const ys = new Set(arr2);
    return xs.size === ys.size && [...xs].every((x) => ys.has(x));
}

async function handleFilterClick(indicator) {
    // need for DOM to update
    const smallAmountOfTime = 10;
    await new Promise((resolve) => {
        setTimeout(resolve, smallAmountOfTime);
    });

    let indicatorStorage = localStorage.getItem(indicator.name);
    if (indicatorStorage === null) {
        localStorage.setItem(indicator.name, "{}");
        indicatorStorage = localStorage.getItem(indicator.name);
    }
    const indicatorLocalData = JSON.parse(indicatorStorage);

    const filtersToSet = {};
    indicator.filters.forEach(([dimensionObj, filtersObj]) => {
        const filters = filtersObj.map((filterOb) => filterOb.db_name);
        const dimension = dimensionObj.db_name;
        const currentFilters = getCurrentFiltersForIndicatorAndDimension(
            indicator,
            dimension
        );
        filtersToSet[dimension] = arrayAreSameSet(filters, currentFilters)
            ? null
            : currentFilters;
    });
    indicatorLocalData.filtersByDimension = filtersToSet;

    localStorage.setItem(indicator.name, JSON.stringify(indicatorLocalData));
}

function updateUrlWithFilters() {
    const excludeFilters = Array.from(
        document.querySelectorAll(
            '.filter-tag[data-default="true"][aria-pressed="false"]'
        )
    ).map((b) => [b.dataset.dimension, `!${b.innerText}`]);
    const includeFilters = Array.from(
        document.querySelectorAll(
            '.filter-tag[data-default="false"][aria-pressed="true"]'
        )
    ).map((b) => [b.dataset.dimension, b.innerText]);
    const stringFilters = includeFilters.concat(excludeFilters);
    const dimensions = new Set(
        Array.from(document.querySelectorAll(".filter-tag")).map(
            (b) => b.dataset.dimension
        )
    );
    const currentUrl = new URL(window.location);
    dimensions.forEach((dimension) => {
        currentUrl.searchParams.delete(dimension);
    });
    stringFilters.forEach((f) => {
        currentUrl.searchParams.append(f[0], f[1]);
    });
    window.history.replaceState({}, "", currentUrl.toString());
}

function initialFiltersByDimension(indicator, dimension) {
    let initialFilters = [];
    let initializedLocally = false;
    const localRawData = localStorage.getItem(indicator.name);
    if (localRawData) {
        const localData = JSON.parse(localRawData);
        if (
            localData.filtersByDimension &&
            localData.filtersByDimension[dimension] !== null
        ) {
            initialFilters = localData.filtersByDimension[dimension];
            initializedLocally = true;
        }
    }
    if (initializedLocally === false) {
        initialFilters = Array.from(
            document.querySelectorAll(
                `.filter-tag[data-indicator="${indicator.id}"][data-default="true"][data-dimension="${dimension}"]`
            )
        ).map((button) => button.innerText);
    }
    Array.from(
        document.querySelectorAll(
            `.filter-tag[data-indicator="${indicator.id}"][data-dimension="${dimension}"]`
        )
    ).forEach((button) => {
        if (button.dataset.setfromurl === "true") {
            return;
        }
        const pressed = initialFilters.includes(button.innerText)
            ? "true"
            : "false";
        button.setAttribute("aria-pressed", pressed);
    });
}

function initializeFilters(indicator) {
    indicator.filters.forEach(([dimension]) => {
        initialFiltersByDimension(indicator, dimension.db_name);
    });
}

function updateFiltersReminder(indicator) {
    if (indicator.filters.length > 1) {
        indicator.filters.forEach(([dimension]) => {
            if (!dimension.is_breakdown) {
                const currentFilters = Array.from(
                    document.querySelectorAll(
                        `.filters-dimension button[data-dimension="${dimension.db_name}"][aria-pressed="true"]`
                    )
                );
                const currentFiltersHtml =
                    currentFilters.length > 0
                        ? currentFilters
                              .map(
                                  (filter) =>
                                      `<p class="fr-tag">${filter.textContent.trim()}</p>`
                              )
                              .join("")
                        : "<p class=fr-tag>Aucun filtre</p>";
                Array.from(
                    document.querySelectorAll(
                        `.filters-reminder-dimension[data-dimension="${dimension.db_name}"]`
                    )
                ).forEach((container) => {
                    container.innerHTML = currentFiltersHtml;
                });
            }
        });
    }
}

export {
    initializeFilters,
    handleFilterClick,
    getIndicatorFilters,
    updateUrlWithFilters,
    updateFiltersReminder,
};
