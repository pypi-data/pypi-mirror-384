import { fillMethodoSidePanel } from "./dom.mjs";

let buttonWhichOpenedPanel = null;

function closeSidePanel() {
    const sidePanelGeo = document.getElementById("slide-panel-geo");
    const sidePanelMethodo = document.getElementById("slide-panel-methodo");
    sidePanelGeo.classList.remove("tdbmd-slide-panel--show");
    sidePanelMethodo.classList.remove("tdbmd-slide-panel--show");
    if (sidePanelGeo.style.display === "block") {
        setTimeout(() => {
            sidePanelGeo.style.display = "none";
        }, 500);
    }
    if (sidePanelMethodo.style.display === "block") {
        setTimeout(() => {
            sidePanelMethodo.style.display = "none";
        }, 500);
    }
    document.querySelectorAll(".validate-territory-btn").forEach((btn) => {
        delete btn.dataset.comparison;
    });
    releaseFocusTrap();
    if (buttonWhichOpenedPanel) {
        buttonWhichOpenedPanel.focus();
    } else {
        document.getElementById("contenu").focus();
    }
}

function openSidePanel(button, type, comparison = false) {
    buttonWhichOpenedPanel = button;
    const panelId = `slide-panel-${type}`;
    const sidePanel = document.getElementById(panelId);
    sidePanel.style.display = "block";
    setTimeout(() => sidePanel.classList.add("tdbmd-slide-panel--show"), 100);
    if (comparison) {
        document.querySelectorAll(".validate-territory-btn").forEach((btn) => {
            btn.dataset.comparison = "true";
        });
    }
    sidePanel.querySelector("button").focus();
    trapFocus(sidePanel);
}

let focusTrapListener;

function trapFocus(container) {
    const focusableSelectors =
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    const focusableElements = container.querySelectorAll(focusableSelectors);
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    focusTrapListener = function (e) {
        if (e.key === "Tab") {
            if (e.shiftKey && document.activeElement === firstElement) {
                e.preventDefault();
                lastElement.focus();
            } else if (!e.shiftKey && document.activeElement === lastElement) {
                e.preventDefault();
                firstElement.focus();
            }
        } else if (e.key === "Escape") {
            closeSidePanel();
        }
    };

    document.addEventListener("keydown", focusTrapListener);
}

function releaseFocusTrap() {
    document.removeEventListener("keydown", focusTrapListener);
}

function openMethodoSidePanel(indicator, button) {
    fillMethodoSidePanel(indicator);
    openSidePanel(button, "methodo");
}

function addSidePanelListener() {
    const button = document.querySelector(
        'button[aria-controls="slide-panel-geo"][data-comparison="false"]'
    );
    if (button) {
        button.addEventListener("click", () => openSidePanel(button, "geo"));
    }
    const cmpButton = document.querySelector(
        'button[aria-controls="slide-panel-geo"][data-comparison="true"]'
    );
    if (cmpButton) {
        cmpButton.addEventListener("click", () =>
            openSidePanel(cmpButton, "geo", true)
        );
    }
    document
        .querySelectorAll('button[data-side-panel-close="true"]')
        .forEach((closeButton) => {
            closeButton.addEventListener("click", () => closeSidePanel());
        });
}

export { openMethodoSidePanel, addSidePanelListener };
