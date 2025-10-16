import BaseController from "./BaseController";
import Device from "sap/ui/Device";
import JSONModel from "sap/ui/model/json/JSONModel";
import ToolPage from "sap/tnt/ToolPage";
import ResourceModel from "sap/ui/model/resource/ResourceModel";

/**
 * @namespace com.optrabot.ui.controller
 */
export default class App extends BaseController {
	public onInit(): void {
		// apply content density mode to root view
		this.getView().addStyleClass(this.getOwnerComponent().getContentDensityClass());

		// if the app starts on desktop devices with small or medium screen size, collaps the side navigation
		if (Device.resize.width <= 1024) {
			this.onSideNavButtonPress();
		}
	}
	
	public getBundleText(sI18nKey: string, aPlaceholderValues?: string[]): Promise<string> {
		return Promise.resolve(this.getBundleTextByModel(sI18nKey, this.getOwnerComponent().getModel("i18n") as ResourceModel, aPlaceholderValues));
	}

	public onSideNavButtonPress(): void {
		console.log("SideNavButton pressed");
		const oToolPage = this.byId("optrabot_app") as ToolPage;
		var bSideExpanded = oToolPage.getSideExpanded();
		oToolPage.setSideExpanded(!bSideExpanded);
		this._setToggleButtonTooltip(!bSideExpanded);
	}

	public async _setToggleButtonTooltip(bSideExpanded: boolean): Promise<void> {
		const oToggleButton = this.byId("sideNavigationToggleButton");
		if (bSideExpanded) {
			oToggleButton.setTooltip(await this.getBundleText("sideNavigationCollapseTooltip"));
		} else {
			oToggleButton.setTooltip(await this.getBundleText("sideNavigationExpandTooltip"));
		}
	}
}
