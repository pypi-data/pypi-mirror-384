/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { ListRenderer } from '@web/views/list/list_renderer';
import { useEffect } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";


const CellLimitThreshold = 100; // px (height to trigger the limit cell feature)

// see static/src/css/list_renderer.css
const LimitCellClass = 'o_limit_cell';
const LimitCellArrowClass = 'o_limit_cell_arrow';


patch(ListRenderer.prototype, 'list_renderer_limit_cell', {
    setup() {
        this._super(...arguments);

        this.limit_fields = this.props.list.context?.limit_fields;
        useEffect(() => {
            if (this.limit_fields) {
                this.limitCellsHeight();
            }
        });
    },

    limitCellsHeight() {
        this.tableRef.el.querySelectorAll('td.o_data_cell').forEach((cellEl) => {
            if (this.limit_fields.includes(cellEl.getAttribute('name'))
                && cellEl.offsetHeight > CellLimitThreshold // too tall
            ) {
                // Wrap the content of the cell in a div
                let div = document.createElement('div');
                div.classList.add(LimitCellClass);
                div.innerHTML = cellEl.innerHTML;
                cellEl.innerHTML = '';
                cellEl.appendChild(div);

                // Add a arrow down to expand the cell
                let divDownArrow = document.createElement('div');
                divDownArrow.classList.add(LimitCellArrowClass);
                let spanDownArrow = document.createElement('span');
                spanDownArrow.innerHTML = _t('Read more ');
                let downArrow = document.createElement('i');
                downArrow.classList.add('fa', 'fa-angle-down');
                divDownArrow.addEventListener('click', this.onArrowClick.bind(this));
                divDownArrow.appendChild(spanDownArrow);
                divDownArrow.appendChild(downArrow);
                cellEl.appendChild(divDownArrow);

                // Add a arrow up to collapse the cell
                let divUpArrow = document.createElement('div');
                divUpArrow.classList.add(LimitCellArrowClass, 'd-none');
                let spanUpArrow = document.createElement('span');
                spanUpArrow.innerHTML = _t('Read less ');
                let upArrow = document.createElement('i');
                upArrow.classList.add('fa', 'fa-angle-up');
                divUpArrow.addEventListener('click', this.onArrowClick.bind(this));
                divUpArrow.appendChild(spanUpArrow);
                divUpArrow.appendChild(upArrow);
                cellEl.appendChild(divUpArrow);

            }

        });
    },

    _onArrowClick(cell) {
        if (!cell) return;

        const targetDiv = cell.querySelector('div:not(.o_limit_cell_arrow)');
        if (!targetDiv) return;

        targetDiv.classList.toggle(LimitCellClass)
        cell.querySelectorAll(`.${LimitCellArrowClass}`).forEach((arrow) => {
            arrow.classList.toggle('d-none');
        });

        if (targetDiv.classList.contains(LimitCellClass)) {
            targetDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    },

    onArrowClick(event) {
        event.stopPropagation();

        let cell = event.target.parentElement?.parentElement;
        if (!cell) return;

        this._onArrowClick(cell);
    },

    onClickSortColumn(column) {
        if (this.props.list.resModel === "mail.message"
            && this.props.list.model.root.resModel === "helpdesk.ticket"
            && ["message_type_mail", "body"].includes(column.name)
        ) {
            return;
        }
        this._super(column);
    }
});

export default ListRenderer;
