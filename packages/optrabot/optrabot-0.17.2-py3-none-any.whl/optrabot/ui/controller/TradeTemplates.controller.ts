import JSONModel from "sap/ui/model/json/JSONModel";
import BaseController from "./BaseController";
import Component from "../Component";
import Router from "sap/ui/core/routing/Router";

/**
 * @namespace com.optrabot.ui.controller
 */
export default class TradeTemplates extends BaseController {
	private oOwnerComponent: Component;
	private oRouter: Router;
	private sCurrentRouteName: string;
	private sCurrentTemplate: string;
	private sLayout: string;
	private oControlModel: JSONModel;

	public onInit(): void {
		console.log("TradeTemplates controller initialized");
		this.oOwnerComponent = this.getOwnerComponent();
		this.oRouter = this.oOwnerComponent.getRouter();
		this.oRouter.attachRouteMatched(this.onRouteMatched, this);
		this.oControlModel = this.oOwnerComponent.getModel("control") as JSONModel;
		//const oTemplatesModel = new JSONModel('model/TradeTemplates.json');
		//this.setModel(oTemplatesModel, "tradetemplates");
	}

	public onRouteMatched(oEvent: any): void {
		const sRouteName = oEvent.getParameter("name");
		const oArguments = oEvent.getParameter("arguments");
		// Save the current route name
		this.sCurrentRouteName = sRouteName;
		this.sCurrentTemplate = oArguments.template;
		var sLayout = "";
		if (!oArguments.layout && this.sCurrentTemplate) {
			sLayout = "TwoColumnsMidExpanded";
		} else {
			sLayout = oArguments.layout || "OneColumn";
		}
		
		// Get Layout from route and set it
		this.getView().byId("flexibleColumnLayout").setLayout(sLayout);
	}

	public onStateChange(oEvent: any): void {
		console.log("State change event triggered");
		/*var bIsNavigationArrow = oEvent.getParameter("isNavigationArrow");
		var sLayout = oEvent.getParameter("layout");

		// Replace the URL with the new layout if a navigation arrow was used
		if (bIsNavigationArrow) {
			this.oRouter.navTo(this.sCurrentRouteName, {layout: sLayout, template: this.sCurrentTemplate}, true);
		}*/
	}

	public onExit(): void {
		//this.oRouter.detachRouteMatched(this.onRouteMatched, this);
	}
}