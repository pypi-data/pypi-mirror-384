/** @odoo-module **/
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
const { Component } = owl;
const cogMenuRegistry = registry.category("cogMenu");

export class CogMenu extends Component {
    setup() {
        this.actionService = useService("action");
    }

    async actionImportFromSinli() {
        try {
            this.actionService.doAction({
                name: "Importar pedidos desde fichero SINLI",
                type: 'ir.actions.act_window',
                res_model: 'import.sale.order.sinli',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
            });
        } catch (error) {
            console.error("Error al abrir el wizard:", error);
        }
    }
}
CogMenu.template = "sinli_import_dropdown";
CogMenu.components = { DropdownItem };

export const CogMenuItem = {
    Component: CogMenu,
    groupNumber: 20,
    isDisplayed: ({ searchModel }) => {
        return searchModel.resModel === 'sale.order';
    },
};

cogMenuRegistry.add("sinli_import_dropdown", CogMenuItem, { sequence: 10 });