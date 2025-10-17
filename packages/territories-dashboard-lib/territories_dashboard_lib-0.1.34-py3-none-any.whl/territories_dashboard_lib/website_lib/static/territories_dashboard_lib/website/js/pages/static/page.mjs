function addCaptionToTables() {
    // Pour rendre le titre du tableau accessible
    // pas d'option en markdown pour relier le titre du tableau au tableau directement.

    const tables = document.querySelectorAll("main table");

    tables.forEach((table) => {
        const previousElement = table.previousElementSibling;

        if (previousElement && previousElement.tagName.toLowerCase() === "p") {
            const caption = document.createElement("caption");
            caption.innerText = previousElement.innerText;
            previousElement.remove();
            table.insertBefore(caption, table.firstChild);
        }
    });
}

function replaceCodeWithEm() {
    // Dans le markdown on utilise des backticks pour mettre des éléments en avant
    // mais cela nuit à l'accessibilité en mettant une balise code

    const codeElements = document.querySelectorAll("code");

    codeElements.forEach((code) => {
        const em = document.createElement("em");
        em.className = "code";
        em.innerHTML = code.innerHTML;

        code.replaceWith(em);
    });
}

addCaptionToTables();
replaceCodeWithEm();
