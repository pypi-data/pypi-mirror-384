function addEmptyGraphMessage(ctx) {
    const div = document.createElement("div");
    div.textContent =
        "Il n'y a pas assez de données pour afficher le graphique.";
    ctx.parentNode.insertBefore(div, ctx);
}

export { addEmptyGraphMessage };
