"use strict";

sap.ui.define(["sap/ui/core/mvc/Controller", "sap/ui/core/UIComponent", "sap/m/MessageBox", "sap/ui/core/routing/History"], function (Controller, UIComponent, MessageBox, History) {
  "use strict";

  /**
   * @namespace com.optrabot.ui.controller
   */
  const BaseController = Controller.extend("com.optrabot.ui.controller.BaseController", {
    /**
     * Convenience method for accessing the component of the controller's view.
     * @returns The component of the controller's view
     */
    getOwnerComponent: function _getOwnerComponent() {
      return Controller.prototype.getOwnerComponent.call(this);
    },
    /**
     * Convenience method to get the components' router instance.
     * @returns The router instance
     */
    getRouter: function _getRouter() {
      return UIComponent.getRouterFor(this);
    },
    /**
     * Convenience method for getting the i18n resource bundle of the component.
     * @returns The i18n resource bundle of the component
     */
    getResourceBundle: function _getResourceBundle() {
      const oModel = this.getOwnerComponent().getModel("i18n");
      return oModel.getResourceBundle();
    },
    /**
     * 
     */
    getBundleTextByModel: async function _getBundleTextByModel(sI18nKey, oResourceModel, aPlaceholderValues) {
      const oBundle = await oResourceModel.getResourceBundle();
      return oBundle.getText(sI18nKey, aPlaceholderValues);
    },
    /**
     * Convenience method for getting the view model by name in every controller of the application.
     * @param [sName] The model name
     * @returns The model instance
     */
    getModel: function _getModel(sName) {
      return this.getView().getModel(sName);
    },
    /**
     * Convenience method for setting the view model in every controller of the application.
     * @param oModel The model instance
     * @param [sName] The model name
     * @returns The current base controller instance
     */
    setModel: function _setModel(oModel, sName) {
      this.getView().setModel(oModel, sName);
      return this;
    },
    /**
     * Convenience method for triggering the navigation to a specific target.
     * @public
     * @param sName Target name
     * @param [oParameters] Navigation parameters
     * @param [bReplace] Defines if the hash should be replaced (no browser history entry) or set (browser history entry)
     */
    navTo: function _navTo(sName, oParameters, bReplace) {
      this.getRouter().navTo(sName, oParameters, undefined, bReplace);
    },
    /**
     * Convenience event handler for navigating back.
     * It there is a history entry we go one step back in the browser history
     * If not, it will replace the current entry of the browser history with the main route.
     */
    onNavBack: function _onNavBack() {
      const sPreviousHash = History.getInstance().getPreviousHash();
      if (sPreviousHash !== undefined) {
        window.history.go(-1);
      } else {
        this.getRouter().navTo("main", {}, undefined, true);
      }
    },
    showFunctionNotImplementedMessage: function _showFunctionNotImplementedMessage() {
      this.showMessage("FunctionNotImplemented", "information");
    },
    showMessage: function _showMessage(messageKey) {
      let messageType = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : "information";
      const i18nModel = this.getOwnerComponent().getModel("i18n");
      const resourceBundle = i18nModel.getResourceBundle();
      const message = resourceBundle.getText(messageKey);
      switch (messageType) {
        case "information":
          MessageBox.information(message);
          break;
        case "error":
          MessageBox.error(message);
          break;
        case "success":
          MessageBox.success(message);
          break;
      }
    }
  });
  return BaseController;
});
//# sourceMappingURL=BaseController-dbg.js.map
