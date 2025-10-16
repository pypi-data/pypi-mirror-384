"use strict";

sap.ui.define(["./BaseController", "sap/ui/model/json/JSONModel", "sap/m/MessageBox"], function (__BaseController, JSONModel, MessageBox) {
  "use strict";

  function _interopRequireDefault(obj) {
    return obj && obj.__esModule && typeof obj.default !== "undefined" ? obj.default : obj;
  }
  const BaseController = _interopRequireDefault(__BaseController);
  /**
   * @namespace com.optrabot.ui.controller
   */
  const TradeTemplateList = BaseController.extend("com.optrabot.ui.controller.TradeTemplateList", {
    onInit: function _onInit() {
      this.oView = this.getView();
      this.oRouter = this.getOwnerComponent().getRouter();
      this.oViewModel = new JSONModel({
        TemplateCollection: []
      });
      this.oView.setModel(this.oViewModel, "tradetemplates");
      this.loadTemplates();
    },
    loadTemplates: async function _loadTemplates() {
      try {
        const globalModel = this.getOwnerComponent().getModel("global");
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
    },
    onAdd: function _onAdd() {
      this.showFunctionNotImplementedMessage();
    },
    onTemplatePress: function _onTemplatePress(oEvent) {
      var oFCL = this.oView.getParent().getParent();
      oFCL.setLayout("TwoColumnsMidExpanded");
      var templatePath = oEvent.getSource().getBindingContext("tradetemplates").getPath();
      var templateName = templatePath.split("/").slice(-1).pop();
      console.log("Template name: " + templateName);
      this.oRouter.navTo("template", {
        layout: "TwoColumnsMidExpanded",
        template: templateName
      });
    }
  });
  return TradeTemplateList;
});
//# sourceMappingURL=TradeTemplateList-dbg.controller.js.map
