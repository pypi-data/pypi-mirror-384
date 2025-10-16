import Router from "sap/ui/core/routing/Router";
import BaseController from "./BaseController";
import JSONModel from "sap/ui/model/json/JSONModel";
import MessageBox from "sap/m/MessageBox";
import ResourceModel from "sap/ui/model/resource/ResourceModel";
/**
 * @namespace com.optrabot.ui.controller
 */
export default class TradeTemplateList extends BaseController {
	private oView: any;
	private oRouter: Router;
	private oViewModel: JSONModel;

	public onInit(): void {
		this.oView = this.getView();
		this.oRouter = this.getOwnerComponent().getRouter();

		this.oViewModel = new JSONModel({
			TemplateCollection: []
		});
		this.oView.setModel(this.oViewModel, "tradetemplates");

		this.loadTemplates();
	}

	private async loadTemplates(): Promise<void> {
		try {
			const globalModel = this.getOwnerComponent().getModel("global") as JSONModel;
			const backendBaseUrl = globalModel.getProperty("/backendBaseUrl");
			const response = await fetch(`${backendBaseUrl}/api/templates/`);
			if (!response.ok) {
				throw new Error('Failed to fetch templates');
			}
			const templates = await response.json();
			this.oViewModel.setProperty("/TemplateCollection", templates);
		} catch (error) {
			MessageBox.error("Failed to load templates: " + error.message);
		}
	}

	public onAdd(): void {
		this.showFunctionNotImplementedMessage();
	}

	public onTemplatePress(oEvent: any): void {
		var oFCL = this.oView.getParent().getParent();
		oFCL.setLayout("TwoColumnsMidExpanded");
		var templatePath = oEvent.getSource().getBindingContext("tradetemplates").getPath();
		var templateName = templatePath.split("/").slice(-1).pop();
		console.log("Template name: " + templateName);
		this.oRouter.navTo("template", {layout: "TwoColumnsMidExpanded", template: templateName} );
	}
}