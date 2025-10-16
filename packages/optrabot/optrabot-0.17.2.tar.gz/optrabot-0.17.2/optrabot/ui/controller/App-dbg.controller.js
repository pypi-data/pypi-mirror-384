"use strict";

sap.ui.define(["./BaseController", "sap/ui/Device"], function (__BaseController, Device) {
  "use strict";

  function _interopRequireDefault(obj) {
    return obj && obj.__esModule && typeof obj.default !== "undefined" ? obj.default : obj;
  }
  const BaseController = _interopRequireDefault(__BaseController);
  /**
   * @namespace com.optrabot.ui.controller
   */
  const App = BaseController.extend("com.optrabot.ui.controller.App", {
    onInit: function _onInit() {
      // apply content density mode to root view
      this.getView().addStyleClass(this.getOwnerComponent().getContentDensityClass());

      // if the app starts on desktop devices with small or medium screen size, collaps the side navigation
      if (Device.resize.width <= 1024) {
        this.onSideNavButtonPress();
      }
    },
    getBundleText: function _getBundleText(sI18nKey, aPlaceholderValues) {
      return Promise.resolve(this.getBundleTextByModel(sI18nKey, this.getOwnerComponent().getModel("i18n"), aPlaceholderValues));
    },
    onSideNavButtonPress: function _onSideNavButtonPress() {
      console.log("SideNavButton pressed");
      const oToolPage = this.byId("optrabot_app");
      var bSideExpanded = oToolPage.getSideExpanded();
      oToolPage.setSideExpanded(!bSideExpanded);
      this._setToggleButtonTooltip(!bSideExpanded);
    },
    _setToggleButtonTooltip: async function _setToggleButtonTooltip(bSideExpanded) {
      const oToggleButton = this.byId("sideNavigationToggleButton");
      if (bSideExpanded) {
        oToggleButton.setTooltip(await this.getBundleText("sideNavigationCollapseTooltip"));
      } else {
        oToggleButton.setTooltip(await this.getBundleText("sideNavigationExpandTooltip"));
      }
    }
  });
  return App;
});
//# sourceMappingURL=App-dbg.controller.js.map
