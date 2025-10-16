"use strict";

sap.ui.define(["sap/ui/core/UIComponent", "./model/models", "sap/ui/Device", "sap/ui/model/json/JSONModel"], function (UIComponent, __models, Device, JSONModel) {
  "use strict";

  function _interopRequireDefault(obj) {
    return obj && obj.__esModule && typeof obj.default !== "undefined" ? obj.default : obj;
  }
  const models = _interopRequireDefault(__models);
  /**
   * @namespace com.optrabot.ui
   */
  const Component = UIComponent.extend("com.optrabot.ui.Component", {
    metadata: {
      manifest: "json"
    },
    init: async function _init() {
      // call the base component's init function
      UIComponent.prototype.init.call(this);

      // create the device model
      this.setModel(models.createDeviceModel(), "device");
      var oControlModel = new JSONModel();
      this.setModel(oControlModel, "control");

      // Initialisiere das global-Model
      await this.initializeGlobalModel();

      // create the views based on the url/hash
      this.getRouter().initialize();
    },
    /**
     * Initializes the global model with the backend URL and the app version.
     * @returns {Promise<void>}
     */
    initializeGlobalModel: async function _initializeGlobalModel() {
      var environment = window.environment || "PROD";
      var backendBaseUrl = "";
      backendBaseUrl = window.location.origin;
      if (environment !== "PROD") {
        // In development the backend uses a different port
        backendBaseUrl = backendBaseUrl.slice(0, backendBaseUrl.lastIndexOf(":"));
        backendBaseUrl = backendBaseUrl + ":8080";
      }
      const globalData = {
        "backendBaseUrl": backendBaseUrl,
        "appVersion": "1.0.0"
      };
      const globalModel = new JSONModel(globalData);
      this.setModel(globalModel, "global");
    },
    /**
     * This method can be called to determine whether the sapUiSizeCompact or sapUiSizeCozy
     * design mode class should be set, which influences the size appearance of some controls.
     * @public
     * @returns css class, either 'sapUiSizeCompact' or 'sapUiSizeCozy' - or an empty string if no css class should be set
     */
    getContentDensityClass: function _getContentDensityClass() {
      if (this.contentDensityClass === undefined) {
        // check whether FLP has already set the content density class; do nothing in this case
        if (document.body.classList.contains("sapUiSizeCozy") || document.body.classList.contains("sapUiSizeCompact")) {
          this.contentDensityClass = "";
        } else if (!Device.support.touch) {
          // apply "compact" mode if touch is not supported
          this.contentDensityClass = "sapUiSizeCompact";
        } else {
          // "cozy" in case of touch support; default for most sap.m controls, but needed for desktop-first controls like sap.ui.table.Table
          this.contentDensityClass = "sapUiSizeCozy";
        }
      }
      return this.contentDensityClass;
    }
  });
  return Component;
});
//# sourceMappingURL=Component-dbg.js.map
