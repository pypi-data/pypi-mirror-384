"use strict";

sap.ui.define(["./BaseController"], function (__BaseController) {
  "use strict";

  function _interopRequireDefault(obj) {
    return obj && obj.__esModule && typeof obj.default !== "undefined" ? obj.default : obj;
  }
  const BaseController = _interopRequireDefault(__BaseController);
  /**
   * @namespace com.optrabot.ui.controller
   */
  const TradeTemplates = BaseController.extend("com.optrabot.ui.controller.TradeTemplates", {
    onInit: function _onInit() {
      console.log("TradeTemplates controller initialized");
      this.oOwnerComponent = this.getOwnerComponent();
      this.oRouter = this.oOwnerComponent.getRouter();
      this.oRouter.attachRouteMatched(this.onRouteMatched, this);
      this.oControlModel = this.oOwnerComponent.getModel("control");
      //const oTemplatesModel = new JSONModel('model/TradeTemplates.json');
      //this.setModel(oTemplatesModel, "tradetemplates");
    },
    onRouteMatched: function _onRouteMatched(oEvent) {
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
    },
    onStateChange: function _onStateChange(oEvent) {
      console.log("State change event triggered");
      /*var bIsNavigationArrow = oEvent.getParameter("isNavigationArrow");
      var sLayout = oEvent.getParameter("layout");
      	// Replace the URL with the new layout if a navigation arrow was used
      if (bIsNavigationArrow) {
      	this.oRouter.navTo(this.sCurrentRouteName, {layout: sLayout, template: this.sCurrentTemplate}, true);
      }*/
    },
    onExit: function _onExit() {
      //this.oRouter.detachRouteMatched(this.onRouteMatched, this);
    }
  });
  return TradeTemplates;
});
//# sourceMappingURL=TradeTemplates-dbg.controller.js.map
