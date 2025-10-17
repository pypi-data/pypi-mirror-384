/* globals ReactDOM, React, SankeyGraph */

import { getParams } from "../dom.mjs";

function makeSankeyGraph(indicator) {
    const params = getParams();
    const container = document.getElementById("sankey-graph");
    if (container) {
        const root = ReactDOM.createRoot(container);
        const element = React.createElement(
            SankeyGraph,
            {
                indicator,
                mesh: params.mesh,
                territory: {
                    geoId: params.territory_id,
                    geoLevel: params.territory_mesh,
                    label: params.territory_name,
                },
            },
            null
        );
        root.render(element);
    }
}

export { makeSankeyGraph };
