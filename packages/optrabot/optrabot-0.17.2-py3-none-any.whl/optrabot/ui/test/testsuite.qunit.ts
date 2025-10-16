export default {
	name: "QUnit test suite for the UI5 Application: com.optrabot.ui",
	defaults: {
		page: "ui5://test-resources/com/optrabot/ui/Test.qunit.html?testsuite={suite}&test={name}",
		qunit: {
			version: 2
		},
		sinon: {
			version: 1
		},
		ui5: {
			language: "EN",
			theme: "sap_horizon"
		},
		coverage: {
			only: "com/optrabot/ui/",
			never: "test-resources/com/optrabot/ui/"
		},
		loader: {
			paths: {
				"com/optrabot/ui": "../"
			}
		}
	},
	tests: {
		"unit/unitTests": {
			title: "Unit tests for com.optrabot.ui"
		},
		"integration/opaTests": {
			title: "Integration tests for com.optrabot.ui"
		}
	}
};
