/* globals ReactDOM, React, IndicatorMap */

import { getParams } from "../dom.mjs";

function makeMap(indicator) {
    const params = getParams();
    const container = document.getElementById("indicator-map");
    const root = ReactDOM.createRoot(container);
    const element = React.createElement(
        IndicatorMap,
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

export { makeMap };
