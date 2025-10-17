function addCurrentLink() {
    const hrefs = Array.from(document.querySelectorAll("#navigation-tabs a"))
        .map((el) => new URL(el.href).pathname)
        .sort((a, b) => b.length - a.length);
    const path = window.location.pathname;
    for (let i = 0; i < hrefs.length; i++) {
        const href = hrefs[i];
        if (path.startsWith(href)) {
            const link = document.querySelector(
                `#navigation-tabs a[href="${href}"]`
            );
            if (link) {
                link.setAttribute("aria-current", true);
                return;
            }
        }
    }
}

addCurrentLink();

// NOTICE ---------------

const NOTICE_COOKIE = "notice";

function setCookie(cname, cvalue, exdays) {
    const d = new Date();
    d.setTime(d.getTime() + exdays * 24 * 60 * 60 * 1000);
    const expires = `expires=${d.toUTCString()}`;
    document.cookie = `${cname}=${cvalue};${expires};path=/`;
}

function getCookie(cname) {
    const name = `${cname}=`;
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(";");
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === " ") {
            c = c.substring(1);
        }
        if (c.indexOf(name) === 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

function focusAfterHeader() {
    const header = document.querySelector("header");
    const focusableSelectors = [
        "button",
        "[href]",
        "input",
        "select",
        "textarea",
        '[tabindex]:not([tabindex="-1"])',
    ];
    const focusableElements = Array.from(
        document.querySelectorAll(focusableSelectors.join(","))
    );

    // Find the first focusable element after the header
    for (let el of focusableElements) {
        if (
            !header.contains(el) &&
            header.compareDocumentPosition(el) &
                Node.DOCUMENT_POSITION_FOLLOWING
        ) {
            el.focus();
            return;
        }
    }
    const firstHeaderLink = document.querySelector("#navigation-tabs a");
    firstHeaderLink.focus();
}

const closeNotice = document.getElementById("close-notice");

if (closeNotice) {
    closeNotice.addEventListener("click", () => {
        const notice = closeNotice.parentNode.parentNode.parentNode;
        notice.parentNode.removeChild(notice);
        const cookie = getCookie(NOTICE_COOKIE);
        const newValue =
            cookie === ""
                ? notice.dataset.id
                : `${cookie},${notice.dataset.id}`;
        setCookie(NOTICE_COOKIE, newValue, 365);
        focusAfterHeader();
    });
}

const notice = document.querySelector(".fr-notice");
if (notice) {
    const cookie = getCookie(NOTICE_COOKIE);
    const isRead =
        cookie !== "" && cookie.split(",").includes(notice.dataset.id);
    if (!isRead) {
        notice.dataset.show = true;
    }
}
