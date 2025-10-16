import Router from "sap/ui/core/routing/Router";
import BaseController from "./BaseController";
import Page from "sap/m/Page";
import JSONModel from "sap/ui/model/json/JSONModel";
import MessageBox from "sap/m/MessageBox";
/**
 * @namespace com.optrabot.ui.controller
 */
export default class TradeTemplateDetail extends BaseController {
	private oRouter: Router;
	private oControlModel: any;
	private oViewModel: JSONModel;
	private _template: string;
	
	public onInit(): void {
		var oOwnerComponent = this.getOwnerComponent();
		this.oRouter = oOwnerComponent.getRouter();
		this.oControlModel = oOwnerComponent.getModel("control");

		this.oViewModel = new JSONModel({
			template: null,
			editable: false
		});
		this.getView().setModel(this.oViewModel, "viewModel");

		this.oRouter.getRoute("template").attachPatternMatched(this._onTemplateMatched, this);
		this.oRouter.getRoute("templateWOLayout").attachPatternMatched(this._onTemplateMatched, this);
	}

	public onEditToggleButtonPress(): void {
		this.showFunctionNotImplementedMessage();
		return;

		var oTemplatePage = this.getView().byId("TemplatePageLayout") as Page;
		var bCurrentShowFooterState = oTemplatePage.getShowFooter();
		oTemplatePage.setShowFooter(!bCurrentShowFooterState);
	}

	private async loadTemplateDetails(): Promise<void> {
		try {
			const globalModel = this.getOwnerComponent().getModel("global") as JSONModel;
			const backendBaseUrl = globalModel.getProperty("/backendBaseUrl");
			const response = await fetch(`${backendBaseUrl}/api/templates/` + this._template);
			if (!response.ok) {
				throw new Error('Failed to fetch template details');
			}
			console.log("Template details loaded");
			const templateData = await response.json();
			this.oViewModel.setProperty("/template", templateData);
		} catch (error) {
			MessageBox.error("Failed to load template details: " + error.message);
		}
	}

	public _onTemplateMatched(oEvent: any): void {
		console.log("Template matched");
		this._template = oEvent.getParameter("arguments").template || this._template || "0";
		
		// Store the current template in the model
		var layout = oEvent.getParameter("arguments").layout || "TwoColumnsMidExpanded";
		this.oControlModel.setProperty("/currentLayout", layout);

		this.loadTemplateDetails();
	}

	public onFullscreenPressed(): void {
		var sCurrentLayout = this.oControlModel.getProperty("/currentLayout");
		var sNewLayout = sCurrentLayout;
		if (sCurrentLayout === "MidColumnFullScreen") {
			sNewLayout = "TwoColumnsMidExpanded";
		} else if (sCurrentLayout === "TwoColumnsMidExpanded") {
			sNewLayout = "MidColumnFullScreen";
		}
		this.oRouter.navTo("template", {
			layout: sNewLayout, template: this._template}, true);
	}

	public onClosePressed(): void {
		this.oRouter.navTo("templates", {
			layout: "OneColumn"}, true);
	}

	public onExit(): void {
		this.oRouter.getRoute("template").detachPatternMatched(this._onTemplateMatched, this);
		this.oRouter.getRoute("templateWOLayout").detachPatternMatched(this._onTemplateMatched, this);
	}
}