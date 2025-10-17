import * as u from '@hat-open/util';
import r from '@hat-open/renderer';
import * as common from './common.js';
import { headerVt } from './header.js';
import { menuVt } from './menu.js';
import { tableVt } from './table.js';
import { detailsVt } from './details.js';
async function main() {
    const root = document.body.appendChild(document.createElement('div'));
    r.init(root, common.defaultState, mainVt);
    common.init();
}
function mainVt() {
    const state = common.getState();
    if (!state.remote)
        return ['div.main'];
    return ['div.main',
        headerVt(),
        menuVt(),
        tableVt(),
        detailsVt()
    ];
}
window.addEventListener('load', main);
window.r = r;
window.u = u;
