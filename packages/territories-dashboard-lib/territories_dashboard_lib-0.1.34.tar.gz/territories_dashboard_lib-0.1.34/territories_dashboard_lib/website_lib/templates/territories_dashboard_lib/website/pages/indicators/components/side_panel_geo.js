async function fetchTerritories(search, mesh, offset = 0, append = false) {
    const searchParams = new URLSearchParams(
        `mesh=${mesh}&search=${search}&offset=${offset}`
    ).toString();
    const resp = await fetch(`/api/geo/search-territories/?${searchParams}`);
    if (resp.ok) {
        const lis = await resp.text();
        const list = document.getElementById(`territories-menu-${mesh}`);
        if (append) {
            list.querySelector('li[data-type="load"]').remove();
            list.innerHTML += lis;
        } else {
            list.innerHTML = lis;
        }
    }
}

// eslint-disable-next-line no-unused-vars
function loadMoreTerritories(button) {
    const mesh = button.dataset.mesh;
    const offset = button.dataset.offset;
    const input = document.getElementById(`search-territories-${mesh}`);
    fetchTerritories(input.value, button.dataset.mesh, offset, true);
}

// eslint-disable-next-line no-unused-vars
function chooseTerritory(li) {
    const name = li.dataset.name;
    const code = li.dataset.code;
    const nameAndCode = li.textContent;
    const mesh = li.parentNode.dataset.mesh;
    document.getElementById(`search-territories-${mesh}`).value = nameAndCode;
    document.getElementById(`selected-territory-id-${mesh}`).value = code;
    document.getElementById(`selected-territory-mesh-${mesh}`).value = mesh;
    document.getElementById(`selected-territory-raw-name-${mesh}`).value = name;
    document.getElementById(
        `selected-territory-name-${mesh}`
    ).innerText = `(${name})`;
    document
        .getElementById(`selected-territory-validate-${mesh}`)
        .removeAttribute("disabled");
}

// eslint-disable-next-line no-unused-vars
function validateTerritory(button) {
    const mesh = button.dataset.mesh;
    const territoryID = document.getElementById(
        `selected-territory-id-${mesh}`
    ).value;
    const territoryMesh = document.getElementById(
        `selected-territory-mesh-${mesh}`
    ).value;
    const urlParams = new URLSearchParams(window.location.search);
    const comparison = button.dataset.comparison == "true" ? "cmp-" : "";
    const currentTerritory = urlParams.get(comparison + "territory");
    const currentTerritoryMesh = currentTerritory
        ? currentTerritory.split("-")[1]
        : null;
    if (territoryMesh !== currentTerritoryMesh) {
        urlParams.delete("mesh");
    }
    urlParams.set(comparison + "territory", `${territoryID}-${territoryMesh}`);
    window.location.search = urlParams;
}

function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        if (timeoutId) clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

const debouncedSearch = debounce(fetchTerritories, 400);

const inputs = document.querySelectorAll(".search-territory-input");

inputs.forEach((input) => {
    const mesh = input.dataset.mesh;
    input.addEventListener("input", () => {
        const searchValue = input.value;
        debouncedSearch(searchValue, mesh);
    });
    fetchTerritories("", mesh);
});
