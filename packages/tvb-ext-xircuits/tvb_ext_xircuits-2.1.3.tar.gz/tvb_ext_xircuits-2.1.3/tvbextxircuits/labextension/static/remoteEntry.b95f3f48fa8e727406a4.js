var _JUPYTERLAB;
/******/ (() => { // webpackBootstrap
/******/ 	"use strict";
/******/ 	var __webpack_modules__ = ({

/***/ "webpack/container/entry/tvb-ext-xircuits":
/*!***********************!*\
  !*** container entry ***!
  \***********************/
/***/ ((__unused_webpack_module, exports, __webpack_require__) => {

var moduleMap = {
	"./index": () => {
		return Promise.all([__webpack_require__.e("vendors-node_modules_lodash_lodash_js"), __webpack_require__.e("vendors-node_modules_projectstorm_react-diagrams-core_dist_index_js"), __webpack_require__.e("webpack_sharing_consume_default_react"), __webpack_require__.e("style_ContextMenu_css"), __webpack_require__.e("webpack_sharing_consume_default_emotion_react_emotion_react-webpack_sharing_consume_default_e-5b0e13"), __webpack_require__.e("lib_index_js")]).then(() => (() => ((__webpack_require__(/*! ./lib/index.js */ "./lib/index.js")))));
	},
	"./extension": () => {
		return Promise.all([__webpack_require__.e("vendors-node_modules_lodash_lodash_js"), __webpack_require__.e("vendors-node_modules_projectstorm_react-diagrams-core_dist_index_js"), __webpack_require__.e("webpack_sharing_consume_default_react"), __webpack_require__.e("style_ContextMenu_css"), __webpack_require__.e("webpack_sharing_consume_default_emotion_react_emotion_react-webpack_sharing_consume_default_e-5b0e13"), __webpack_require__.e("lib_index_js")]).then(() => (() => ((__webpack_require__(/*! ./lib/index.js */ "./lib/index.js")))));
	},
	"./style": () => {
		return Promise.all([__webpack_require__.e("style_ContextMenu_css"), __webpack_require__.e("style_index_js")]).then(() => (() => ((__webpack_require__(/*! ./style/index.js */ "./style/index.js")))));
	}
};
var get = (module, getScope) => {
	__webpack_require__.R = getScope;
	getScope = (
		__webpack_require__.o(moduleMap, module)
			? moduleMap[module]()
			: Promise.resolve().then(() => {
				throw new Error('Module "' + module + '" does not exist in container.');
			})
	);
	__webpack_require__.R = undefined;
	return getScope;
};
var init = (shareScope, initScope) => {
	if (!__webpack_require__.S) return;
	var name = "default"
	var oldScope = __webpack_require__.S[name];
	if(oldScope && oldScope !== shareScope) throw new Error("Container initialization failed as it has already been initialized with a different share scope");
	__webpack_require__.S[name] = shareScope;
	return __webpack_require__.I(name, initScope);
};

// This exports getters to disallow modifications
__webpack_require__.d(exports, {
	get: () => (get),
	init: () => (init)
});

/***/ })

/******/ 	});
/************************************************************************/
/******/ 	// The module cache
/******/ 	var __webpack_module_cache__ = {};
/******/ 	
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/ 		// Check if module is in cache
/******/ 		var cachedModule = __webpack_module_cache__[moduleId];
/******/ 		if (cachedModule !== undefined) {
/******/ 			return cachedModule.exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = __webpack_module_cache__[moduleId] = {
/******/ 			id: moduleId,
/******/ 			loaded: false,
/******/ 			exports: {}
/******/ 		};
/******/ 	
/******/ 		// Execute the module function
/******/ 		__webpack_modules__[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/ 	
/******/ 		// Flag the module as loaded
/******/ 		module.loaded = true;
/******/ 	
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/ 	
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = __webpack_modules__;
/******/ 	
/******/ 	// expose the module cache
/******/ 	__webpack_require__.c = __webpack_module_cache__;
/******/ 	
/************************************************************************/
/******/ 	/* webpack/runtime/compat get default export */
/******/ 	(() => {
/******/ 		// getDefaultExport function for compatibility with non-harmony modules
/******/ 		__webpack_require__.n = (module) => {
/******/ 			var getter = module && module.__esModule ?
/******/ 				() => (module['default']) :
/******/ 				() => (module);
/******/ 			__webpack_require__.d(getter, { a: getter });
/******/ 			return getter;
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/define property getters */
/******/ 	(() => {
/******/ 		// define getter functions for harmony exports
/******/ 		__webpack_require__.d = (exports, definition) => {
/******/ 			for(var key in definition) {
/******/ 				if(__webpack_require__.o(definition, key) && !__webpack_require__.o(exports, key)) {
/******/ 					Object.defineProperty(exports, key, { enumerable: true, get: definition[key] });
/******/ 				}
/******/ 			}
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/ensure chunk */
/******/ 	(() => {
/******/ 		__webpack_require__.f = {};
/******/ 		// This file contains only the entry chunk.
/******/ 		// The chunk loading function for additional chunks
/******/ 		__webpack_require__.e = (chunkId) => {
/******/ 			return Promise.all(Object.keys(__webpack_require__.f).reduce((promises, key) => {
/******/ 				__webpack_require__.f[key](chunkId, promises);
/******/ 				return promises;
/******/ 			}, []));
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/get javascript chunk filename */
/******/ 	(() => {
/******/ 		// This function allow to reference async chunks
/******/ 		__webpack_require__.u = (chunkId) => {
/******/ 			// return url for filenames based on template
/******/ 			return "" + chunkId + "." + {"vendors-node_modules_lodash_lodash_js":"8d2c7e783fc0d66d7cab","vendors-node_modules_projectstorm_react-diagrams-core_dist_index_js":"02f8e1328b4f1c3788b7","style_ContextMenu_css":"4e0b5917838e146a8fea","lib_index_js":"02e5cb3f185caeb02764","style_index_js":"152bab04b76eaba057ff","vendors-node_modules_babel_runtime_helpers_esm_extends_js-node_modules_emotion_serialize_dist-ff2f34":"8387ca11e87c3db28b75","vendors-node_modules_emotion_react_dist_emotion-react_browser_development_esm_js":"063677e96616f032d84d","vendors-node_modules_emotion_styled_dist_emotion-styled_browser_development_esm_js":"e0a597f33195855044ff","vendors-node_modules_projectstorm_react-canvas-core_node_modules_projectstorm_geometry_dist_i-aeec94":"12502d4859f623696b58","vendors-node_modules_projectstorm_react-diagrams-core_node_modules_projectstorm_geometry_dist-d6cb54":"bbe7f530890fd24a0c73","vendors-node_modules_projectstorm_react-diagrams-defaults_node_modules_projectstorm_geometry_-6256fb":"f479d04e8330a32e6d80","vendors-node_modules_projectstorm_react-diagrams-routing_node_modules_projectstorm_geometry_d-b38dc1":"2be4346e83accbf06f6b","vendors-node_modules_lodash__baseFlatten_js-node_modules_lodash_forEach_js-node_modules_lodas-1d1d9b":"b9bfc0f93e56a6e16315","vendors-node_modules_projectstorm_geometry_dist_index_js":"b9f4b2d478b6af15ba49","vendors-node_modules_projectstorm_react-diagrams_dist_index_js":"b79dcdcd13428cb161ea","vendors-node_modules_colorjs_io_dist_color_js":"fbb657e2a6e01084d244","vendors-node_modules_marked_lib_marked_esm_js":"a0eaee8eef1b869bed08","vendors-node_modules_react-accessible-accordion_dist_es_index_js":"37aae9f7edb0a0847d04","vendors-node_modules_react-collapsed_dist_index_mjs":"9f4541b729bd5682e5d9","vendors-node_modules_prop-types_index_js":"33d1e841c7dfd8fb75d1","vendors-node_modules_react-numeric-input_index_js":"0861f223f6a2a115a9f7","vendors-node_modules_react-switch_dist_index_dev_mjs":"07c2844f9e24baeffc53","node_modules_react-textarea-autosize_dist_react-textarea-autosize_browser_development_esm_js-_6d7d0":"b13d0b814addce4b170d","vendors-node_modules_react-toggle_dist_component_index_js":"9e65a3cada51258f3b98","vendors-node_modules_react-tooltip_dist_index_es_js":"458d34ead2520a84c522","node_modules_react-textarea-autosize_dist_react-textarea-autosize_browser_development_esm_js-_6d7d1":"f0fb630e2930591823c2"}[chunkId] + ".js";
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/global */
/******/ 	(() => {
/******/ 		__webpack_require__.g = (function() {
/******/ 			if (typeof globalThis === 'object') return globalThis;
/******/ 			try {
/******/ 				return this || new Function('return this')();
/******/ 			} catch (e) {
/******/ 				if (typeof window === 'object') return window;
/******/ 			}
/******/ 		})();
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/hasOwnProperty shorthand */
/******/ 	(() => {
/******/ 		__webpack_require__.o = (obj, prop) => (Object.prototype.hasOwnProperty.call(obj, prop))
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/load script */
/******/ 	(() => {
/******/ 		var inProgress = {};
/******/ 		var dataWebpackPrefix = "tvb-ext-xircuits:";
/******/ 		// loadScript function to load a script via script tag
/******/ 		__webpack_require__.l = (url, done, key, chunkId) => {
/******/ 			if(inProgress[url]) { inProgress[url].push(done); return; }
/******/ 			var script, needAttach;
/******/ 			if(key !== undefined) {
/******/ 				var scripts = document.getElementsByTagName("script");
/******/ 				for(var i = 0; i < scripts.length; i++) {
/******/ 					var s = scripts[i];
/******/ 					if(s.getAttribute("src") == url || s.getAttribute("data-webpack") == dataWebpackPrefix + key) { script = s; break; }
/******/ 				}
/******/ 			}
/******/ 			if(!script) {
/******/ 				needAttach = true;
/******/ 				script = document.createElement('script');
/******/ 		
/******/ 				script.charset = 'utf-8';
/******/ 				if (__webpack_require__.nc) {
/******/ 					script.setAttribute("nonce", __webpack_require__.nc);
/******/ 				}
/******/ 				script.setAttribute("data-webpack", dataWebpackPrefix + key);
/******/ 		
/******/ 				script.src = url;
/******/ 			}
/******/ 			inProgress[url] = [done];
/******/ 			var onScriptComplete = (prev, event) => {
/******/ 				// avoid mem leaks in IE.
/******/ 				script.onerror = script.onload = null;
/******/ 				clearTimeout(timeout);
/******/ 				var doneFns = inProgress[url];
/******/ 				delete inProgress[url];
/******/ 				script.parentNode && script.parentNode.removeChild(script);
/******/ 				doneFns && doneFns.forEach((fn) => (fn(event)));
/******/ 				if(prev) return prev(event);
/******/ 			}
/******/ 			var timeout = setTimeout(onScriptComplete.bind(null, undefined, { type: 'timeout', target: script }), 120000);
/******/ 			script.onerror = onScriptComplete.bind(null, script.onerror);
/******/ 			script.onload = onScriptComplete.bind(null, script.onload);
/******/ 			needAttach && document.head.appendChild(script);
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/make namespace object */
/******/ 	(() => {
/******/ 		// define __esModule on exports
/******/ 		__webpack_require__.r = (exports) => {
/******/ 			if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 				Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 			}
/******/ 			Object.defineProperty(exports, '__esModule', { value: true });
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/node module decorator */
/******/ 	(() => {
/******/ 		__webpack_require__.nmd = (module) => {
/******/ 			module.paths = [];
/******/ 			if (!module.children) module.children = [];
/******/ 			return module;
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/sharing */
/******/ 	(() => {
/******/ 		__webpack_require__.S = {};
/******/ 		var initPromises = {};
/******/ 		var initTokens = {};
/******/ 		__webpack_require__.I = (name, initScope) => {
/******/ 			if(!initScope) initScope = [];
/******/ 			// handling circular init calls
/******/ 			var initToken = initTokens[name];
/******/ 			if(!initToken) initToken = initTokens[name] = {};
/******/ 			if(initScope.indexOf(initToken) >= 0) return;
/******/ 			initScope.push(initToken);
/******/ 			// only runs once
/******/ 			if(initPromises[name]) return initPromises[name];
/******/ 			// creates a new share scope if needed
/******/ 			if(!__webpack_require__.o(__webpack_require__.S, name)) __webpack_require__.S[name] = {};
/******/ 			// runs all init snippets from all modules reachable
/******/ 			var scope = __webpack_require__.S[name];
/******/ 			var warn = (msg) => {
/******/ 				if (typeof console !== "undefined" && console.warn) console.warn(msg);
/******/ 			};
/******/ 			var uniqueName = "tvb-ext-xircuits";
/******/ 			var register = (name, version, factory, eager) => {
/******/ 				var versions = scope[name] = scope[name] || {};
/******/ 				var activeVersion = versions[version];
/******/ 				if(!activeVersion || (!activeVersion.loaded && (!eager != !activeVersion.eager ? eager : uniqueName > activeVersion.from))) versions[version] = { get: factory, from: uniqueName, eager: !!eager };
/******/ 			};
/******/ 			var initExternal = (id) => {
/******/ 				var handleError = (err) => (warn("Initialization of sharing external failed: " + err));
/******/ 				try {
/******/ 					var module = __webpack_require__(id);
/******/ 					if(!module) return;
/******/ 					var initFn = (module) => (module && module.init && module.init(__webpack_require__.S[name], initScope))
/******/ 					if(module.then) return promises.push(module.then(initFn, handleError));
/******/ 					var initResult = initFn(module);
/******/ 					if(initResult && initResult.then) return promises.push(initResult['catch'](handleError));
/******/ 				} catch(err) { handleError(err); }
/******/ 			}
/******/ 			var promises = [];
/******/ 			switch(name) {
/******/ 				case "default": {
/******/ 					register("@emotion/react", "11.14.0", () => (Promise.all([__webpack_require__.e("vendors-node_modules_babel_runtime_helpers_esm_extends_js-node_modules_emotion_serialize_dist-ff2f34"), __webpack_require__.e("vendors-node_modules_emotion_react_dist_emotion-react_browser_development_esm_js"), __webpack_require__.e("webpack_sharing_consume_default_react")]).then(() => (() => (__webpack_require__(/*! ./node_modules/@emotion/react/dist/emotion-react.browser.development.esm.js */ "./node_modules/@emotion/react/dist/emotion-react.browser.development.esm.js"))))));
/******/ 					register("@emotion/styled", "11.14.1", () => (Promise.all([__webpack_require__.e("vendors-node_modules_babel_runtime_helpers_esm_extends_js-node_modules_emotion_serialize_dist-ff2f34"), __webpack_require__.e("vendors-node_modules_emotion_styled_dist_emotion-styled_browser_development_esm_js"), __webpack_require__.e("webpack_sharing_consume_default_react"), __webpack_require__.e("webpack_sharing_consume_default_emotion_react_emotion_react")]).then(() => (() => (__webpack_require__(/*! ./node_modules/@emotion/styled/dist/emotion-styled.browser.development.esm.js */ "./node_modules/@emotion/styled/dist/emotion-styled.browser.development.esm.js"))))));
/******/ 					register("@projectstorm/geometry", "7.0.1", () => (Promise.all([__webpack_require__.e("vendors-node_modules_lodash_lodash_js"), __webpack_require__.e("vendors-node_modules_projectstorm_react-canvas-core_node_modules_projectstorm_geometry_dist_i-aeec94")]).then(() => (() => (__webpack_require__(/*! ./node_modules/@projectstorm/react-canvas-core/node_modules/@projectstorm/geometry/dist/index.js */ "./node_modules/@projectstorm/react-canvas-core/node_modules/@projectstorm/geometry/dist/index.js"))))));
/******/ 					register("@projectstorm/geometry", "7.0.1", () => (Promise.all([__webpack_require__.e("vendors-node_modules_lodash_lodash_js"), __webpack_require__.e("vendors-node_modules_projectstorm_react-diagrams-core_node_modules_projectstorm_geometry_dist-d6cb54")]).then(() => (() => (__webpack_require__(/*! ./node_modules/@projectstorm/react-diagrams-core/node_modules/@projectstorm/geometry/dist/index.js */ "./node_modules/@projectstorm/react-diagrams-core/node_modules/@projectstorm/geometry/dist/index.js"))))));
/******/ 					register("@projectstorm/geometry", "7.0.1", () => (Promise.all([__webpack_require__.e("vendors-node_modules_lodash_lodash_js"), __webpack_require__.e("vendors-node_modules_projectstorm_react-diagrams-defaults_node_modules_projectstorm_geometry_-6256fb")]).then(() => (() => (__webpack_require__(/*! ./node_modules/@projectstorm/react-diagrams-defaults/node_modules/@projectstorm/geometry/dist/index.js */ "./node_modules/@projectstorm/react-diagrams-defaults/node_modules/@projectstorm/geometry/dist/index.js"))))));
/******/ 					register("@projectstorm/geometry", "7.0.1", () => (Promise.all([__webpack_require__.e("vendors-node_modules_lodash_lodash_js"), __webpack_require__.e("vendors-node_modules_projectstorm_react-diagrams-routing_node_modules_projectstorm_geometry_d-b38dc1")]).then(() => (() => (__webpack_require__(/*! ./node_modules/@projectstorm/react-diagrams-routing/node_modules/@projectstorm/geometry/dist/index.js */ "./node_modules/@projectstorm/react-diagrams-routing/node_modules/@projectstorm/geometry/dist/index.js"))))));
/******/ 					register("@projectstorm/geometry", "7.0.3", () => (Promise.all([__webpack_require__.e("vendors-node_modules_lodash__baseFlatten_js-node_modules_lodash_forEach_js-node_modules_lodas-1d1d9b"), __webpack_require__.e("vendors-node_modules_projectstorm_geometry_dist_index_js")]).then(() => (() => (__webpack_require__(/*! ./node_modules/@projectstorm/geometry/dist/index.js */ "./node_modules/@projectstorm/geometry/dist/index.js"))))));
/******/ 					register("@projectstorm/react-diagrams", "7.0.2", () => (Promise.all([__webpack_require__.e("vendors-node_modules_lodash_lodash_js"), __webpack_require__.e("vendors-node_modules_lodash__baseFlatten_js-node_modules_lodash_forEach_js-node_modules_lodas-1d1d9b"), __webpack_require__.e("vendors-node_modules_projectstorm_react-diagrams_dist_index_js"), __webpack_require__.e("vendors-node_modules_projectstorm_react-diagrams-core_dist_index_js"), __webpack_require__.e("webpack_sharing_consume_default_react"), __webpack_require__.e("webpack_sharing_consume_default_emotion_react_emotion_react-webpack_sharing_consume_default_e-5b0e13"), __webpack_require__.e("webpack_sharing_consume_default_emotion_styled_emotion_styled-webpack_sharing_consume_default-cef64d")]).then(() => (() => (__webpack_require__(/*! ./node_modules/@projectstorm/react-diagrams/dist/index.js */ "./node_modules/@projectstorm/react-diagrams/dist/index.js"))))));
/******/ 					register("colorjs.io", "0.4.5", () => (__webpack_require__.e("vendors-node_modules_colorjs_io_dist_color_js").then(() => (() => (__webpack_require__(/*! ./node_modules/colorjs.io/dist/color.js */ "./node_modules/colorjs.io/dist/color.js"))))));
/******/ 					register("marked", "11.2.0", () => (__webpack_require__.e("vendors-node_modules_marked_lib_marked_esm_js").then(() => (() => (__webpack_require__(/*! ./node_modules/marked/lib/marked.esm.js */ "./node_modules/marked/lib/marked.esm.js"))))));
/******/ 					register("react-accessible-accordion", "5.0.1", () => (Promise.all([__webpack_require__.e("vendors-node_modules_react-accessible-accordion_dist_es_index_js"), __webpack_require__.e("webpack_sharing_consume_default_react")]).then(() => (() => (__webpack_require__(/*! ./node_modules/react-accessible-accordion/dist/es/index.js */ "./node_modules/react-accessible-accordion/dist/es/index.js"))))));
/******/ 					register("react-collapsed", "4.2.0", () => (Promise.all([__webpack_require__.e("vendors-node_modules_react-collapsed_dist_index_mjs"), __webpack_require__.e("webpack_sharing_consume_default_react")]).then(() => (() => (__webpack_require__(/*! ./node_modules/react-collapsed/dist/index.mjs */ "./node_modules/react-collapsed/dist/index.mjs"))))));
/******/ 					register("react-numeric-input", "2.2.3", () => (Promise.all([__webpack_require__.e("vendors-node_modules_prop-types_index_js"), __webpack_require__.e("vendors-node_modules_react-numeric-input_index_js"), __webpack_require__.e("webpack_sharing_consume_default_react")]).then(() => (() => (__webpack_require__(/*! ./node_modules/react-numeric-input/index.js */ "./node_modules/react-numeric-input/index.js"))))));
/******/ 					register("react-switch", "7.1.0", () => (Promise.all([__webpack_require__.e("vendors-node_modules_prop-types_index_js"), __webpack_require__.e("vendors-node_modules_react-switch_dist_index_dev_mjs"), __webpack_require__.e("webpack_sharing_consume_default_react")]).then(() => (() => (__webpack_require__(/*! ./node_modules/react-switch/dist/index.dev.mjs */ "./node_modules/react-switch/dist/index.dev.mjs"))))));
/******/ 					register("react-textarea-autosize", "8.5.9", () => (Promise.all([__webpack_require__.e("webpack_sharing_consume_default_react"), __webpack_require__.e("node_modules_react-textarea-autosize_dist_react-textarea-autosize_browser_development_esm_js-_6d7d0")]).then(() => (() => (__webpack_require__(/*! ./node_modules/react-textarea-autosize/dist/react-textarea-autosize.browser.development.esm.js */ "./node_modules/react-textarea-autosize/dist/react-textarea-autosize.browser.development.esm.js"))))));
/******/ 					register("react-toggle", "4.1.3", () => (Promise.all([__webpack_require__.e("vendors-node_modules_prop-types_index_js"), __webpack_require__.e("vendors-node_modules_react-toggle_dist_component_index_js"), __webpack_require__.e("webpack_sharing_consume_default_react")]).then(() => (() => (__webpack_require__(/*! ./node_modules/react-toggle/dist/component/index.js */ "./node_modules/react-toggle/dist/component/index.js"))))));
/******/ 					register("react-tooltip", "4.5.1", () => (Promise.all([__webpack_require__.e("vendors-node_modules_prop-types_index_js"), __webpack_require__.e("vendors-node_modules_react-tooltip_dist_index_es_js"), __webpack_require__.e("webpack_sharing_consume_default_react")]).then(() => (() => (__webpack_require__(/*! ./node_modules/react-tooltip/dist/index.es.js */ "./node_modules/react-tooltip/dist/index.es.js"))))));
/******/ 					register("tvb-ext-xircuits", "2.1.3", () => (Promise.all([__webpack_require__.e("vendors-node_modules_lodash_lodash_js"), __webpack_require__.e("vendors-node_modules_projectstorm_react-diagrams-core_dist_index_js"), __webpack_require__.e("webpack_sharing_consume_default_react"), __webpack_require__.e("style_ContextMenu_css"), __webpack_require__.e("webpack_sharing_consume_default_emotion_react_emotion_react-webpack_sharing_consume_default_e-5b0e13"), __webpack_require__.e("lib_index_js")]).then(() => (() => (__webpack_require__(/*! ./lib/index.js */ "./lib/index.js"))))));
/******/ 				}
/******/ 				break;
/******/ 			}
/******/ 			if(!promises.length) return initPromises[name] = 1;
/******/ 			return initPromises[name] = Promise.all(promises).then(() => (initPromises[name] = 1));
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/publicPath */
/******/ 	(() => {
/******/ 		var scriptUrl;
/******/ 		if (__webpack_require__.g.importScripts) scriptUrl = __webpack_require__.g.location + "";
/******/ 		var document = __webpack_require__.g.document;
/******/ 		if (!scriptUrl && document) {
/******/ 			if (document.currentScript && document.currentScript.tagName.toUpperCase() === 'SCRIPT')
/******/ 				scriptUrl = document.currentScript.src;
/******/ 			if (!scriptUrl) {
/******/ 				var scripts = document.getElementsByTagName("script");
/******/ 				if(scripts.length) {
/******/ 					var i = scripts.length - 1;
/******/ 					while (i > -1 && (!scriptUrl || !/^http(s?):/.test(scriptUrl))) scriptUrl = scripts[i--].src;
/******/ 				}
/******/ 			}
/******/ 		}
/******/ 		// When supporting browsers where an automatic publicPath is not supported you must specify an output.publicPath manually via configuration
/******/ 		// or pass an empty string ("") and set the __webpack_public_path__ variable from your code to use your own logic.
/******/ 		if (!scriptUrl) throw new Error("Automatic publicPath is not supported in this browser");
/******/ 		scriptUrl = scriptUrl.replace(/^blob:/, "").replace(/#.*$/, "").replace(/\?.*$/, "").replace(/\/[^\/]+$/, "/");
/******/ 		__webpack_require__.p = scriptUrl;
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/consumes */
/******/ 	(() => {
/******/ 		var parseVersion = (str) => {
/******/ 			// see webpack/lib/util/semver.js for original code
/******/ 			var p=p=>{return p.split(".").map(p=>{return+p==p?+p:p})},n=/^([^-+]+)?(?:-([^+]+))?(?:\+(.+))?$/.exec(str),r=n[1]?p(n[1]):[];return n[2]&&(r.length++,r.push.apply(r,p(n[2]))),n[3]&&(r.push([]),r.push.apply(r,p(n[3]))),r;
/******/ 		}
/******/ 		var versionLt = (a, b) => {
/******/ 			// see webpack/lib/util/semver.js for original code
/******/ 			a=parseVersion(a),b=parseVersion(b);for(var r=0;;){if(r>=a.length)return r<b.length&&"u"!=(typeof b[r])[0];var e=a[r],n=(typeof e)[0];if(r>=b.length)return"u"==n;var t=b[r],f=(typeof t)[0];if(n!=f)return"o"==n&&"n"==f||("s"==f||"u"==n);if("o"!=n&&"u"!=n&&e!=t)return e<t;r++}
/******/ 		}
/******/ 		var rangeToString = (range) => {
/******/ 			// see webpack/lib/util/semver.js for original code
/******/ 			var r=range[0],n="";if(1===range.length)return"*";if(r+.5){n+=0==r?">=":-1==r?"<":1==r?"^":2==r?"~":r>0?"=":"!=";for(var e=1,a=1;a<range.length;a++){e--,n+="u"==(typeof(t=range[a]))[0]?"-":(e>0?".":"")+(e=2,t)}return n}var g=[];for(a=1;a<range.length;a++){var t=range[a];g.push(0===t?"not("+o()+")":1===t?"("+o()+" || "+o()+")":2===t?g.pop()+" "+g.pop():rangeToString(t))}return o();function o(){return g.pop().replace(/^\((.+)\)$/,"$1")}
/******/ 		}
/******/ 		var satisfy = (range, version) => {
/******/ 			// see webpack/lib/util/semver.js for original code
/******/ 			if(0 in range){version=parseVersion(version);var e=range[0],r=e<0;r&&(e=-e-1);for(var n=0,i=1,a=!0;;i++,n++){var f,s,g=i<range.length?(typeof range[i])[0]:"";if(n>=version.length||"o"==(s=(typeof(f=version[n]))[0]))return!a||("u"==g?i>e&&!r:""==g!=r);if("u"==s){if(!a||"u"!=g)return!1}else if(a)if(g==s)if(i<=e){if(f!=range[i])return!1}else{if(r?f>range[i]:f<range[i])return!1;f!=range[i]&&(a=!1)}else if("s"!=g&&"n"!=g){if(r||i<=e)return!1;a=!1,i--}else{if(i<=e||s<g!=r)return!1;a=!1}else"s"!=g&&"n"!=g&&(a=!1,i--)}}var t=[],o=t.pop.bind(t);for(n=1;n<range.length;n++){var u=range[n];t.push(1==u?o()|o():2==u?o()&o():u?satisfy(u,version):!o())}return!!o();
/******/ 		}
/******/ 		var exists = (scope, key) => {
/******/ 			return scope && __webpack_require__.o(scope, key);
/******/ 		}
/******/ 		var get = (entry) => {
/******/ 			entry.loaded = 1;
/******/ 			return entry.get()
/******/ 		};
/******/ 		var eagerOnly = (versions) => {
/******/ 			return Object.keys(versions).reduce((filtered, version) => {
/******/ 					if (versions[version].eager) {
/******/ 						filtered[version] = versions[version];
/******/ 					}
/******/ 					return filtered;
/******/ 			}, {});
/******/ 		};
/******/ 		var findLatestVersion = (scope, key, eager) => {
/******/ 			var versions = eager ? eagerOnly(scope[key]) : scope[key];
/******/ 			var key = Object.keys(versions).reduce((a, b) => {
/******/ 				return !a || versionLt(a, b) ? b : a;
/******/ 			}, 0);
/******/ 			return key && versions[key];
/******/ 		};
/******/ 		var findSatisfyingVersion = (scope, key, requiredVersion, eager) => {
/******/ 			var versions = eager ? eagerOnly(scope[key]) : scope[key];
/******/ 			var key = Object.keys(versions).reduce((a, b) => {
/******/ 				if (!satisfy(requiredVersion, b)) return a;
/******/ 				return !a || versionLt(a, b) ? b : a;
/******/ 			}, 0);
/******/ 			return key && versions[key]
/******/ 		};
/******/ 		var findSingletonVersionKey = (scope, key, eager) => {
/******/ 			var versions = eager ? eagerOnly(scope[key]) : scope[key];
/******/ 			return Object.keys(versions).reduce((a, b) => {
/******/ 				return !a || (!versions[a].loaded && versionLt(a, b)) ? b : a;
/******/ 			}, 0);
/******/ 		};
/******/ 		var getInvalidSingletonVersionMessage = (scope, key, version, requiredVersion) => {
/******/ 			return "Unsatisfied version " + version + " from " + (version && scope[key][version].from) + " of shared singleton module " + key + " (required " + rangeToString(requiredVersion) + ")"
/******/ 		};
/******/ 		var getInvalidVersionMessage = (scope, scopeName, key, requiredVersion, eager) => {
/******/ 			var versions = scope[key];
/******/ 			return "No satisfying version (" + rangeToString(requiredVersion) + ")" + (eager ? " for eager consumption" : "") + " of shared module " + key + " found in shared scope " + scopeName + ".\n" +
/******/ 				"Available versions: " + Object.keys(versions).map((key) => {
/******/ 				return key + " from " + versions[key].from;
/******/ 			}).join(", ");
/******/ 		};
/******/ 		var fail = (msg) => {
/******/ 			throw new Error(msg);
/******/ 		}
/******/ 		var failAsNotExist = (scopeName, key) => {
/******/ 			return fail("Shared module " + key + " doesn't exist in shared scope " + scopeName);
/******/ 		}
/******/ 		var warn = /*#__PURE__*/ (msg) => {
/******/ 			if (typeof console !== "undefined" && console.warn) console.warn(msg);
/******/ 		};
/******/ 		var init = (fn) => (function(scopeName, key, eager, c, d) {
/******/ 			var promise = __webpack_require__.I(scopeName);
/******/ 			if (promise && promise.then && !eager) {
/******/ 				return promise.then(fn.bind(fn, scopeName, __webpack_require__.S[scopeName], key, false, c, d));
/******/ 			}
/******/ 			return fn(scopeName, __webpack_require__.S[scopeName], key, eager, c, d);
/******/ 		});
/******/ 		
/******/ 		var useFallback = (scopeName, key, fallback) => {
/******/ 			return fallback ? fallback() : failAsNotExist(scopeName, key);
/******/ 		}
/******/ 		var load = /*#__PURE__*/ init((scopeName, scope, key, eager, fallback) => {
/******/ 			if (!exists(scope, key)) return useFallback(scopeName, key, fallback);
/******/ 			return get(findLatestVersion(scope, key, eager));
/******/ 		});
/******/ 		var loadVersion = /*#__PURE__*/ init((scopeName, scope, key, eager, requiredVersion, fallback) => {
/******/ 			if (!exists(scope, key)) return useFallback(scopeName, key, fallback);
/******/ 			var satisfyingVersion = findSatisfyingVersion(scope, key, requiredVersion, eager);
/******/ 			if (satisfyingVersion) return get(satisfyingVersion);
/******/ 			warn(getInvalidVersionMessage(scope, scopeName, key, requiredVersion, eager))
/******/ 			return get(findLatestVersion(scope, key, eager));
/******/ 		});
/******/ 		var loadStrictVersion = /*#__PURE__*/ init((scopeName, scope, key, eager, requiredVersion, fallback) => {
/******/ 			if (!exists(scope, key)) return useFallback(scopeName, key, fallback);
/******/ 			var satisfyingVersion = findSatisfyingVersion(scope, key, requiredVersion, eager);
/******/ 			if (satisfyingVersion) return get(satisfyingVersion);
/******/ 			if (fallback) return fallback();
/******/ 			fail(getInvalidVersionMessage(scope, scopeName, key, requiredVersion, eager));
/******/ 		});
/******/ 		var loadSingleton = /*#__PURE__*/ init((scopeName, scope, key, eager, fallback) => {
/******/ 			if (!exists(scope, key)) return useFallback(scopeName, key, fallback);
/******/ 			var version = findSingletonVersionKey(scope, key, eager);
/******/ 			return get(scope[key][version]);
/******/ 		});
/******/ 		var loadSingletonVersion = /*#__PURE__*/ init((scopeName, scope, key, eager, requiredVersion, fallback) => {
/******/ 			if (!exists(scope, key)) return useFallback(scopeName, key, fallback);
/******/ 			var version = findSingletonVersionKey(scope, key, eager);
/******/ 			if (!satisfy(requiredVersion, version)) {
/******/ 				warn(getInvalidSingletonVersionMessage(scope, key, version, requiredVersion));
/******/ 			}
/******/ 			return get(scope[key][version]);
/******/ 		});
/******/ 		var loadStrictSingletonVersion = /*#__PURE__*/ init((scopeName, scope, key, eager, requiredVersion, fallback) => {
/******/ 			if (!exists(scope, key)) return useFallback(scopeName, key, fallback);
/******/ 			var version = findSingletonVersionKey(scope, key, eager);
/******/ 			if (!satisfy(requiredVersion, version)) {
/******/ 				fail(getInvalidSingletonVersionMessage(scope, key, version, requiredVersion));
/******/ 			}
/******/ 			return get(scope[key][version]);
/******/ 		});
/******/ 		var installedModules = {};
/******/ 		var moduleToHandlerMapping = {
/******/ 			"webpack/sharing/consume/default/react": () => (loadSingletonVersion("default", "react", false, [1,18,2,0])),
/******/ 			"webpack/sharing/consume/default/@emotion/styled/@emotion/styled?5d9f": () => (loadStrictVersion("default", "@emotion/styled", false, [1,11,10,5], () => (Promise.all([__webpack_require__.e("vendors-node_modules_babel_runtime_helpers_esm_extends_js-node_modules_emotion_serialize_dist-ff2f34"), __webpack_require__.e("vendors-node_modules_emotion_styled_dist_emotion-styled_browser_development_esm_js"), __webpack_require__.e("webpack_sharing_consume_default_emotion_react_emotion_react")]).then(() => (() => (__webpack_require__(/*! @emotion/styled */ "./node_modules/@emotion/styled/dist/emotion-styled.browser.development.esm.js"))))))),
/******/ 			"webpack/sharing/consume/default/@emotion/react/@emotion/react?fbe7": () => (loadStrictVersion("default", "@emotion/react", false, [1,11,10,5], () => (Promise.all([__webpack_require__.e("vendors-node_modules_babel_runtime_helpers_esm_extends_js-node_modules_emotion_serialize_dist-ff2f34"), __webpack_require__.e("vendors-node_modules_emotion_react_dist_emotion-react_browser_development_esm_js")]).then(() => (() => (__webpack_require__(/*! @emotion/react */ "./node_modules/@emotion/react/dist/emotion-react.browser.development.esm.js"))))))),
/******/ 			"webpack/sharing/consume/default/@projectstorm/geometry/@projectstorm/geometry?b1e3": () => (loadStrictVersion("default", "@projectstorm/geometry", false, [4,7,0,1], () => (__webpack_require__.e("vendors-node_modules_projectstorm_react-canvas-core_node_modules_projectstorm_geometry_dist_i-aeec94").then(() => (() => (__webpack_require__(/*! @projectstorm/geometry */ "./node_modules/@projectstorm/react-canvas-core/node_modules/@projectstorm/geometry/dist/index.js"))))))),
/******/ 			"webpack/sharing/consume/default/@projectstorm/geometry/@projectstorm/geometry?ae79": () => (loadStrictVersion("default", "@projectstorm/geometry", false, [4,7,0,1], () => (__webpack_require__.e("vendors-node_modules_projectstorm_react-diagrams-core_node_modules_projectstorm_geometry_dist-d6cb54").then(() => (() => (__webpack_require__(/*! @projectstorm/geometry */ "./node_modules/@projectstorm/react-diagrams-core/node_modules/@projectstorm/geometry/dist/index.js"))))))),
/******/ 			"webpack/sharing/consume/default/@jupyterlab/application": () => (loadSingletonVersion("default", "@jupyterlab/application", false, [1,4,4,9])),
/******/ 			"webpack/sharing/consume/default/@jupyterlab/filebrowser": () => (loadSingletonVersion("default", "@jupyterlab/filebrowser", false, [1,4,4,9])),
/******/ 			"webpack/sharing/consume/default/@jupyterlab/apputils": () => (loadSingletonVersion("default", "@jupyterlab/apputils", false, [1,4,5,9])),
/******/ 			"webpack/sharing/consume/default/@jupyterlab/launcher": () => (loadSingletonVersion("default", "@jupyterlab/launcher", false, [1,4,4,9])),
/******/ 			"webpack/sharing/consume/default/@jupyterlab/docregistry": () => (loadVersion("default", "@jupyterlab/docregistry", false, [1,4,4,9])),
/******/ 			"webpack/sharing/consume/default/@lumino/signaling": () => (loadSingletonVersion("default", "@lumino/signaling", false, [1,2,0,0])),
/******/ 			"webpack/sharing/consume/default/@emotion/styled/@emotion/styled?1fc9": () => (loadStrictVersion("default", "@emotion/styled", false, [1,11,3,0], () => (Promise.all([__webpack_require__.e("vendors-node_modules_babel_runtime_helpers_esm_extends_js-node_modules_emotion_serialize_dist-ff2f34"), __webpack_require__.e("vendors-node_modules_emotion_styled_dist_emotion-styled_browser_development_esm_js"), __webpack_require__.e("webpack_sharing_consume_default_emotion_react_emotion_react")]).then(() => (() => (__webpack_require__(/*! @emotion/styled */ "./node_modules/@emotion/styled/dist/emotion-styled.browser.development.esm.js"))))))),
/******/ 			"webpack/sharing/consume/default/@jupyterlab/ui-components": () => (loadSingletonVersion("default", "@jupyterlab/ui-components", false, [1,4,4,9])),
/******/ 			"webpack/sharing/consume/default/@lumino/coreutils": () => (loadSingletonVersion("default", "@lumino/coreutils", false, [1,2,0,0])),
/******/ 			"webpack/sharing/consume/default/@jupyterlab/rendermime": () => (loadSingletonVersion("default", "@jupyterlab/rendermime", false, [1,4,4,9])),
/******/ 			"webpack/sharing/consume/default/@jupyterlab/logconsole": () => (loadSingletonVersion("default", "@jupyterlab/logconsole", false, [1,4,4,9])),
/******/ 			"webpack/sharing/consume/default/@jupyterlab/coreutils": () => (loadSingletonVersion("default", "@jupyterlab/coreutils", false, [1,6,4,9])),
/******/ 			"webpack/sharing/consume/default/@jupyterlab/services": () => (loadSingletonVersion("default", "@jupyterlab/services", false, [1,7,4,9])),
/******/ 			"webpack/sharing/consume/default/@lumino/messaging": () => (loadSingletonVersion("default", "@lumino/messaging", false, [1,2,0,0])),
/******/ 			"webpack/sharing/consume/default/@lumino/widgets": () => (loadSingletonVersion("default", "@lumino/widgets", false, [1,2,3,1,,"alpha",0])),
/******/ 			"webpack/sharing/consume/default/react-switch/react-switch": () => (loadStrictVersion("default", "react-switch", false, [1,7,0,0], () => (Promise.all([__webpack_require__.e("vendors-node_modules_prop-types_index_js"), __webpack_require__.e("vendors-node_modules_react-switch_dist_index_dev_mjs")]).then(() => (() => (__webpack_require__(/*! react-switch */ "./node_modules/react-switch/dist/index.dev.mjs"))))))),
/******/ 			"webpack/sharing/consume/default/react-textarea-autosize/react-textarea-autosize": () => (loadStrictVersion("default", "react-textarea-autosize", false, [1,8,5,3], () => (__webpack_require__.e("node_modules_react-textarea-autosize_dist_react-textarea-autosize_browser_development_esm_js-_6d7d1").then(() => (() => (__webpack_require__(/*! react-textarea-autosize */ "./node_modules/react-textarea-autosize/dist/react-textarea-autosize.browser.development.esm.js"))))))),
/******/ 			"webpack/sharing/consume/default/@projectstorm/react-diagrams/@projectstorm/react-diagrams": () => (loadStrictVersion("default", "@projectstorm/react-diagrams", false, [4,7,0,2], () => (Promise.all([__webpack_require__.e("vendors-node_modules_lodash__baseFlatten_js-node_modules_lodash_forEach_js-node_modules_lodas-1d1d9b"), __webpack_require__.e("vendors-node_modules_projectstorm_react-diagrams_dist_index_js"), __webpack_require__.e("webpack_sharing_consume_default_emotion_styled_emotion_styled-webpack_sharing_consume_default-cef64d")]).then(() => (() => (__webpack_require__(/*! @projectstorm/react-diagrams */ "./node_modules/@projectstorm/react-diagrams/dist/index.js"))))))),
/******/ 			"webpack/sharing/consume/default/react-numeric-input/react-numeric-input": () => (loadStrictVersion("default", "react-numeric-input", false, [1,2,2,3], () => (Promise.all([__webpack_require__.e("vendors-node_modules_prop-types_index_js"), __webpack_require__.e("vendors-node_modules_react-numeric-input_index_js")]).then(() => (() => (__webpack_require__(/*! react-numeric-input */ "./node_modules/react-numeric-input/index.js"))))))),
/******/ 			"webpack/sharing/consume/default/react-collapsed/react-collapsed": () => (loadStrictVersion("default", "react-collapsed", false, [1,4,2,0], () => (__webpack_require__.e("vendors-node_modules_react-collapsed_dist_index_mjs").then(() => (() => (__webpack_require__(/*! react-collapsed */ "./node_modules/react-collapsed/dist/index.mjs"))))))),
/******/ 			"webpack/sharing/consume/default/react-accessible-accordion/react-accessible-accordion": () => (loadStrictVersion("default", "react-accessible-accordion", false, [1,5,0,0], () => (__webpack_require__.e("vendors-node_modules_react-accessible-accordion_dist_es_index_js").then(() => (() => (__webpack_require__(/*! react-accessible-accordion */ "./node_modules/react-accessible-accordion/dist/es/index.js"))))))),
/******/ 			"webpack/sharing/consume/default/@projectstorm/geometry/@projectstorm/geometry?2db1": () => (loadStrictVersion("default", "@projectstorm/geometry", false, [1,7,0,2], () => (Promise.all([__webpack_require__.e("vendors-node_modules_lodash__baseFlatten_js-node_modules_lodash_forEach_js-node_modules_lodas-1d1d9b"), __webpack_require__.e("vendors-node_modules_projectstorm_geometry_dist_index_js")]).then(() => (() => (__webpack_require__(/*! @projectstorm/geometry */ "./node_modules/@projectstorm/geometry/dist/index.js"))))))),
/******/ 			"webpack/sharing/consume/default/react-toggle/react-toggle": () => (loadStrictVersion("default", "react-toggle", false, [1,4,1,3], () => (Promise.all([__webpack_require__.e("vendors-node_modules_prop-types_index_js"), __webpack_require__.e("vendors-node_modules_react-toggle_dist_component_index_js")]).then(() => (() => (__webpack_require__(/*! react-toggle */ "./node_modules/react-toggle/dist/component/index.js"))))))),
/******/ 			"webpack/sharing/consume/default/colorjs.io/colorjs.io": () => (loadStrictVersion("default", "colorjs.io", false, [2,0,4,5], () => (__webpack_require__.e("vendors-node_modules_colorjs_io_dist_color_js").then(() => (() => (__webpack_require__(/*! colorjs.io */ "./node_modules/colorjs.io/dist/color.js"))))))),
/******/ 			"webpack/sharing/consume/default/react-tooltip/react-tooltip": () => (loadStrictVersion("default", "react-tooltip", false, [1,4,2,21], () => (Promise.all([__webpack_require__.e("vendors-node_modules_prop-types_index_js"), __webpack_require__.e("vendors-node_modules_react-tooltip_dist_index_es_js")]).then(() => (() => (__webpack_require__(/*! react-tooltip */ "./node_modules/react-tooltip/dist/index.es.js"))))))),
/******/ 			"webpack/sharing/consume/default/marked/marked": () => (loadStrictVersion("default", "marked", false, [1,11,0,0], () => (__webpack_require__.e("vendors-node_modules_marked_lib_marked_esm_js").then(() => (() => (__webpack_require__(/*! marked */ "./node_modules/marked/lib/marked.esm.js"))))))),
/******/ 			"webpack/sharing/consume/default/@emotion/react/@emotion/react?f02c": () => (loadStrictVersion("default", "@emotion/react", false, [1,11,13,3], () => (Promise.all([__webpack_require__.e("vendors-node_modules_babel_runtime_helpers_esm_extends_js-node_modules_emotion_serialize_dist-ff2f34"), __webpack_require__.e("vendors-node_modules_emotion_react_dist_emotion-react_browser_development_esm_js")]).then(() => (() => (__webpack_require__(/*! @emotion/react */ "./node_modules/@emotion/react/dist/emotion-react.browser.development.esm.js"))))))),
/******/ 			"webpack/sharing/consume/default/react-dom": () => (loadSingletonVersion("default", "react-dom", false, [1,18,2,0])),
/******/ 			"webpack/sharing/consume/default/@jupyterlab/docmanager": () => (loadSingletonVersion("default", "@jupyterlab/docmanager", false, [1,4,4,9])),
/******/ 			"webpack/sharing/consume/default/@jupyterlab/translation": () => (loadSingletonVersion("default", "@jupyterlab/translation", false, [1,4,4,9])),
/******/ 			"webpack/sharing/consume/default/@jupyterlab/outputarea": () => (loadVersion("default", "@jupyterlab/outputarea", false, [1,4,4,9])),
/******/ 			"webpack/sharing/consume/default/@jupyterlab/fileeditor": () => (loadSingletonVersion("default", "@jupyterlab/fileeditor", false, [1,4,4,9])),
/******/ 			"webpack/sharing/consume/default/@jupyterlab/mainmenu": () => (loadSingletonVersion("default", "@jupyterlab/mainmenu", false, [1,4,4,9])),
/******/ 			"webpack/sharing/consume/default/@jupyterlab/settingregistry": () => (loadSingletonVersion("default", "@jupyterlab/settingregistry", false, [1,4,4,9])),
/******/ 			"webpack/sharing/consume/default/@emotion/react/@emotion/react?6a66": () => (loadStrictVersion("default", "@emotion/react", false, [1,11,0,0,,"rc",0], () => (__webpack_require__.e("vendors-node_modules_emotion_react_dist_emotion-react_browser_development_esm_js").then(() => (() => (__webpack_require__(/*! @emotion/react */ "./node_modules/@emotion/react/dist/emotion-react.browser.development.esm.js"))))))),
/******/ 			"webpack/sharing/consume/default/@emotion/styled/@emotion/styled?37bb": () => (loadStrictVersion("default", "@emotion/styled", false, [1,11], () => (Promise.all([__webpack_require__.e("vendors-node_modules_babel_runtime_helpers_esm_extends_js-node_modules_emotion_serialize_dist-ff2f34"), __webpack_require__.e("vendors-node_modules_emotion_styled_dist_emotion-styled_browser_development_esm_js"), __webpack_require__.e("webpack_sharing_consume_default_emotion_react_emotion_react")]).then(() => (() => (__webpack_require__(/*! @emotion/styled */ "./node_modules/@emotion/styled/dist/emotion-styled.browser.development.esm.js"))))))),
/******/ 			"webpack/sharing/consume/default/@projectstorm/geometry/@projectstorm/geometry?5711": () => (loadStrictVersion("default", "@projectstorm/geometry", false, [4,7,0,1], () => (__webpack_require__.e("vendors-node_modules_projectstorm_react-diagrams-defaults_node_modules_projectstorm_geometry_-6256fb").then(() => (() => (__webpack_require__(/*! @projectstorm/geometry */ "./node_modules/@projectstorm/react-diagrams-defaults/node_modules/@projectstorm/geometry/dist/index.js"))))))),
/******/ 			"webpack/sharing/consume/default/@projectstorm/geometry/@projectstorm/geometry?9d8d": () => (loadStrictVersion("default", "@projectstorm/geometry", false, [4,7,0,1], () => (__webpack_require__.e("vendors-node_modules_projectstorm_react-diagrams-routing_node_modules_projectstorm_geometry_d-b38dc1").then(() => (() => (__webpack_require__(/*! @projectstorm/geometry */ "./node_modules/@projectstorm/react-diagrams-routing/node_modules/@projectstorm/geometry/dist/index.js")))))))
/******/ 		};
/******/ 		// no consumes in initial chunks
/******/ 		var chunkMapping = {
/******/ 			"webpack_sharing_consume_default_react": [
/******/ 				"webpack/sharing/consume/default/react"
/******/ 			],
/******/ 			"webpack_sharing_consume_default_emotion_react_emotion_react-webpack_sharing_consume_default_e-5b0e13": [
/******/ 				"webpack/sharing/consume/default/@emotion/styled/@emotion/styled?5d9f",
/******/ 				"webpack/sharing/consume/default/@emotion/react/@emotion/react?fbe7",
/******/ 				"webpack/sharing/consume/default/@projectstorm/geometry/@projectstorm/geometry?b1e3",
/******/ 				"webpack/sharing/consume/default/@projectstorm/geometry/@projectstorm/geometry?ae79"
/******/ 			],
/******/ 			"lib_index_js": [
/******/ 				"webpack/sharing/consume/default/@jupyterlab/application",
/******/ 				"webpack/sharing/consume/default/@jupyterlab/filebrowser",
/******/ 				"webpack/sharing/consume/default/@jupyterlab/apputils",
/******/ 				"webpack/sharing/consume/default/@jupyterlab/launcher",
/******/ 				"webpack/sharing/consume/default/@jupyterlab/docregistry",
/******/ 				"webpack/sharing/consume/default/@lumino/signaling",
/******/ 				"webpack/sharing/consume/default/@emotion/styled/@emotion/styled?1fc9",
/******/ 				"webpack/sharing/consume/default/@jupyterlab/ui-components",
/******/ 				"webpack/sharing/consume/default/@lumino/coreutils",
/******/ 				"webpack/sharing/consume/default/@jupyterlab/rendermime",
/******/ 				"webpack/sharing/consume/default/@jupyterlab/logconsole",
/******/ 				"webpack/sharing/consume/default/@jupyterlab/coreutils",
/******/ 				"webpack/sharing/consume/default/@jupyterlab/services",
/******/ 				"webpack/sharing/consume/default/@lumino/messaging",
/******/ 				"webpack/sharing/consume/default/@lumino/widgets",
/******/ 				"webpack/sharing/consume/default/react-switch/react-switch",
/******/ 				"webpack/sharing/consume/default/react-textarea-autosize/react-textarea-autosize",
/******/ 				"webpack/sharing/consume/default/@projectstorm/react-diagrams/@projectstorm/react-diagrams",
/******/ 				"webpack/sharing/consume/default/react-numeric-input/react-numeric-input",
/******/ 				"webpack/sharing/consume/default/react-collapsed/react-collapsed",
/******/ 				"webpack/sharing/consume/default/react-accessible-accordion/react-accessible-accordion",
/******/ 				"webpack/sharing/consume/default/@projectstorm/geometry/@projectstorm/geometry?2db1",
/******/ 				"webpack/sharing/consume/default/react-toggle/react-toggle",
/******/ 				"webpack/sharing/consume/default/colorjs.io/colorjs.io",
/******/ 				"webpack/sharing/consume/default/react-tooltip/react-tooltip",
/******/ 				"webpack/sharing/consume/default/marked/marked",
/******/ 				"webpack/sharing/consume/default/@emotion/react/@emotion/react?f02c",
/******/ 				"webpack/sharing/consume/default/react-dom",
/******/ 				"webpack/sharing/consume/default/@jupyterlab/docmanager",
/******/ 				"webpack/sharing/consume/default/@jupyterlab/translation",
/******/ 				"webpack/sharing/consume/default/@jupyterlab/outputarea",
/******/ 				"webpack/sharing/consume/default/@jupyterlab/fileeditor",
/******/ 				"webpack/sharing/consume/default/@jupyterlab/mainmenu",
/******/ 				"webpack/sharing/consume/default/@jupyterlab/settingregistry"
/******/ 			],
/******/ 			"webpack_sharing_consume_default_emotion_react_emotion_react": [
/******/ 				"webpack/sharing/consume/default/@emotion/react/@emotion/react?6a66"
/******/ 			],
/******/ 			"webpack_sharing_consume_default_emotion_styled_emotion_styled-webpack_sharing_consume_default-cef64d": [
/******/ 				"webpack/sharing/consume/default/@emotion/styled/@emotion/styled?37bb",
/******/ 				"webpack/sharing/consume/default/@projectstorm/geometry/@projectstorm/geometry?5711",
/******/ 				"webpack/sharing/consume/default/@projectstorm/geometry/@projectstorm/geometry?9d8d"
/******/ 			]
/******/ 		};
/******/ 		var startedInstallModules = {};
/******/ 		__webpack_require__.f.consumes = (chunkId, promises) => {
/******/ 			if(__webpack_require__.o(chunkMapping, chunkId)) {
/******/ 				chunkMapping[chunkId].forEach((id) => {
/******/ 					if(__webpack_require__.o(installedModules, id)) return promises.push(installedModules[id]);
/******/ 					if(!startedInstallModules[id]) {
/******/ 					var onFactory = (factory) => {
/******/ 						installedModules[id] = 0;
/******/ 						__webpack_require__.m[id] = (module) => {
/******/ 							delete __webpack_require__.c[id];
/******/ 							module.exports = factory();
/******/ 						}
/******/ 					};
/******/ 					startedInstallModules[id] = true;
/******/ 					var onError = (error) => {
/******/ 						delete installedModules[id];
/******/ 						__webpack_require__.m[id] = (module) => {
/******/ 							delete __webpack_require__.c[id];
/******/ 							throw error;
/******/ 						}
/******/ 					};
/******/ 					try {
/******/ 						var promise = moduleToHandlerMapping[id]();
/******/ 						if(promise.then) {
/******/ 							promises.push(installedModules[id] = promise.then(onFactory)['catch'](onError));
/******/ 						} else onFactory(promise);
/******/ 					} catch(e) { onError(e); }
/******/ 					}
/******/ 				});
/******/ 			}
/******/ 		}
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/jsonp chunk loading */
/******/ 	(() => {
/******/ 		__webpack_require__.b = (typeof document !== 'undefined' && document.baseURI) || self.location.href;
/******/ 		
/******/ 		// object to store loaded and loading chunks
/******/ 		// undefined = chunk not loaded, null = chunk preloaded/prefetched
/******/ 		// [resolve, reject, Promise] = chunk loading, 0 = chunk loaded
/******/ 		var installedChunks = {
/******/ 			"tvb-ext-xircuits": 0
/******/ 		};
/******/ 		
/******/ 		__webpack_require__.f.j = (chunkId, promises) => {
/******/ 				// JSONP chunk loading for javascript
/******/ 				var installedChunkData = __webpack_require__.o(installedChunks, chunkId) ? installedChunks[chunkId] : undefined;
/******/ 				if(installedChunkData !== 0) { // 0 means "already installed".
/******/ 		
/******/ 					// a Promise means "currently loading".
/******/ 					if(installedChunkData) {
/******/ 						promises.push(installedChunkData[2]);
/******/ 					} else {
/******/ 						if(!/^webpack_sharing_consume_default_(emotion_(react_emotion_react(|\-webpack_sharing_consume_default_e\-5b0e13)|styled_emotion_styled\-webpack_sharing_consume_default\-cef64d)|react)$/.test(chunkId)) {
/******/ 							// setup Promise in chunk cache
/******/ 							var promise = new Promise((resolve, reject) => (installedChunkData = installedChunks[chunkId] = [resolve, reject]));
/******/ 							promises.push(installedChunkData[2] = promise);
/******/ 		
/******/ 							// start chunk loading
/******/ 							var url = __webpack_require__.p + __webpack_require__.u(chunkId);
/******/ 							// create error before stack unwound to get useful stacktrace later
/******/ 							var error = new Error();
/******/ 							var loadingEnded = (event) => {
/******/ 								if(__webpack_require__.o(installedChunks, chunkId)) {
/******/ 									installedChunkData = installedChunks[chunkId];
/******/ 									if(installedChunkData !== 0) installedChunks[chunkId] = undefined;
/******/ 									if(installedChunkData) {
/******/ 										var errorType = event && (event.type === 'load' ? 'missing' : event.type);
/******/ 										var realSrc = event && event.target && event.target.src;
/******/ 										error.message = 'Loading chunk ' + chunkId + ' failed.\n(' + errorType + ': ' + realSrc + ')';
/******/ 										error.name = 'ChunkLoadError';
/******/ 										error.type = errorType;
/******/ 										error.request = realSrc;
/******/ 										installedChunkData[1](error);
/******/ 									}
/******/ 								}
/******/ 							};
/******/ 							__webpack_require__.l(url, loadingEnded, "chunk-" + chunkId, chunkId);
/******/ 						} else installedChunks[chunkId] = 0;
/******/ 					}
/******/ 				}
/******/ 		};
/******/ 		
/******/ 		// no prefetching
/******/ 		
/******/ 		// no preloaded
/******/ 		
/******/ 		// no HMR
/******/ 		
/******/ 		// no HMR manifest
/******/ 		
/******/ 		// no on chunks loaded
/******/ 		
/******/ 		// install a JSONP callback for chunk loading
/******/ 		var webpackJsonpCallback = (parentChunkLoadingFunction, data) => {
/******/ 			var [chunkIds, moreModules, runtime] = data;
/******/ 			// add "moreModules" to the modules object,
/******/ 			// then flag all "chunkIds" as loaded and fire callback
/******/ 			var moduleId, chunkId, i = 0;
/******/ 			if(chunkIds.some((id) => (installedChunks[id] !== 0))) {
/******/ 				for(moduleId in moreModules) {
/******/ 					if(__webpack_require__.o(moreModules, moduleId)) {
/******/ 						__webpack_require__.m[moduleId] = moreModules[moduleId];
/******/ 					}
/******/ 				}
/******/ 				if(runtime) var result = runtime(__webpack_require__);
/******/ 			}
/******/ 			if(parentChunkLoadingFunction) parentChunkLoadingFunction(data);
/******/ 			for(;i < chunkIds.length; i++) {
/******/ 				chunkId = chunkIds[i];
/******/ 				if(__webpack_require__.o(installedChunks, chunkId) && installedChunks[chunkId]) {
/******/ 					installedChunks[chunkId][0]();
/******/ 				}
/******/ 				installedChunks[chunkId] = 0;
/******/ 			}
/******/ 		
/******/ 		}
/******/ 		
/******/ 		var chunkLoadingGlobal = self["webpackChunktvb_ext_xircuits"] = self["webpackChunktvb_ext_xircuits"] || [];
/******/ 		chunkLoadingGlobal.forEach(webpackJsonpCallback.bind(null, 0));
/******/ 		chunkLoadingGlobal.push = webpackJsonpCallback.bind(null, chunkLoadingGlobal.push.bind(chunkLoadingGlobal));
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/nonce */
/******/ 	(() => {
/******/ 		__webpack_require__.nc = undefined;
/******/ 	})();
/******/ 	
/************************************************************************/
/******/ 	
/******/ 	// module cache are used so entry inlining is disabled
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	var __webpack_exports__ = __webpack_require__("webpack/container/entry/tvb-ext-xircuits");
/******/ 	(_JUPYTERLAB = typeof _JUPYTERLAB === "undefined" ? {} : _JUPYTERLAB)["tvb-ext-xircuits"] = __webpack_exports__;
/******/ 	
/******/ })()
;
//# sourceMappingURL=remoteEntry.b95f3f48fa8e727406a4.js.map