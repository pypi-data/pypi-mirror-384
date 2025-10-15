"use strict";
(self["webpackChunk_amzn_amazon_sagemaker_jupyter_ai_q_developer"] = self["webpackChunk_amzn_amazon_sagemaker_jupyter_ai_q_developer"] || []).push([["lib_index_js"],{

/***/ "./lib/components/CustomJAIHeader.js":
/*!*******************************************!*\
  !*** ./lib/components/CustomJAIHeader.js ***!
  \*******************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (/* binding */ CustomJAIHeader)
/* harmony export */ });
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyterlab/ui-components */ "webpack/sharing/consume/default/@jupyterlab/ui-components");
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! react */ "webpack/sharing/consume/default/react");
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _utils_environmentUtils__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../utils/environmentUtils */ "./lib/utils/environmentUtils.js");
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../constants */ "./lib/constants.js");




var QTier;
(function (QTier) {
    QTier["FREE"] = "Free Tier";
    QTier["Q_DEV"] = "Pro Tier";
})(QTier || (QTier = {}));
function CustomJAIHeaderComponent() {
    return (react__WEBPACK_IMPORTED_MODULE_1___default().createElement("div", { style: { display: 'flex' } },
        react__WEBPACK_IMPORTED_MODULE_1___default().createElement(QHeader, null),
        react__WEBPACK_IMPORTED_MODULE_1___default().createElement(QTierChip, null)));
}
function QHeader() {
    return react__WEBPACK_IMPORTED_MODULE_1___default().createElement("div", { className: "jp-RenderedHTMLCommon", style: { fontSize: '1.1rem', fontWeight: 700 } }, "Amazon Q");
}
function QTierChip() {
    // Use state to handle async data
    const [qTier, setQTier] = react__WEBPACK_IMPORTED_MODULE_1___default().useState(null);
    // Use useEffect to fetch data
    react__WEBPACK_IMPORTED_MODULE_1___default().useEffect(() => {
        const fetchData = async () => {
            try {
                const environment = await (0,_utils_environmentUtils__WEBPACK_IMPORTED_MODULE_2__.fetchCurrentEnvironment)();
                if (!environment) {
                    return;
                }
                const tier = getQTier(environment.env, environment.isQDeveloperEnabled);
                setQTier(tier);
            }
            catch (error) {
                console.error('Error fetching data to set Q tier:', error);
            }
        };
        fetchData();
    }, []); // Empty dependency array means this runs once on mount
    if (!qTier) {
        return null;
    }
    return (react__WEBPACK_IMPORTED_MODULE_1___default().createElement("div", { style: getChipStyles(qTier) }, qTier));
}
const getChipStyles = (qTier) => {
    const baseStyles = {
        zIndex: 5,
        borderRadius: '4px',
        padding: '2px 8px 2px 8px',
        textAlign: 'center',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
    };
    if (QTier.FREE === qTier) {
        return {
            ...baseStyles,
            color: 'white',
            backgroundColor: _constants__WEBPACK_IMPORTED_MODULE_3__.Q_CHIP_BACKGROUND_COLOR_FREE_TIER,
        };
    }
    else {
        return {
            ...baseStyles,
            color: 'white',
            background: _constants__WEBPACK_IMPORTED_MODULE_3__.Q_CHIP_BACKGROUND_COLOR_PAID_TIER_GRADIENT,
            fontWeight: '500',
        };
    }
};
// Note that IDC below refers to the authentication mode we use with Q and not the mode to login to 
// MD portal.
// MD_IDC = MaxDome environment using IDC access token for authentication with Q (Paid tier)
// MD_IAM = MaxDome environment using IAM for authentication with Q (Free tier)
// Logic for how the environment is set can be found here
// https://tiny.amazon.com/kg0njiyt/codeamazpackblob2789utilenvi
function getQTier(env, qDeveloperStatus) {
    // Return Q_DEV for MD_IDC or if it's SMStudioSSO with qDeveloperStatus
    if (env === _utils_environmentUtils__WEBPACK_IMPORTED_MODULE_2__.AppEnvironment.MD_IDC || (env === _utils_environmentUtils__WEBPACK_IMPORTED_MODULE_2__.AppEnvironment.SMStudioSSO && qDeveloperStatus)) {
        return QTier.Q_DEV;
    }
    // All other cases return FREE
    return QTier.FREE;
}
class CustomJAIHeader extends _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__.ReactWidget {
    render() {
        return (react__WEBPACK_IMPORTED_MODULE_1___default().createElement(CustomJAIHeaderComponent, null));
    }
}


/***/ }),

/***/ "./lib/components/Icons/icons.js":
/*!***************************************!*\
  !*** ./lib/components/Icons/icons.js ***!
  \***************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   downvoteIcon: () => (/* binding */ downvoteIcon),
/* harmony export */   upvoteIcon: () => (/* binding */ upvoteIcon)
/* harmony export */ });
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyterlab/ui-components */ "webpack/sharing/consume/default/@jupyterlab/ui-components");
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../../constants */ "./lib/constants.js");


const upvoteIconSvgstr = `<svg class="jp-icon3" width="32" height="32" viewBox="0 0 36 36" fill="#616161" xmlns="http://www.w3.org/2000/svg">
  <path
        clipRule="evenodd"
        d="M18.522 12.173l-2.486 4.14v5.723h5.44a1 1 0 00.969-.76l1.01-4.049a1 1 0 00-.97-1.24h-2.44a1 1 0 01-1-1v-2.67a.276.276 0 00-.28-.28.293.293 0 00-.243.136zm-4.486 9.863v-5h-1v5h1zm.434-7l2.338-3.895.002-.003a2.293 2.293 0 011.956-1.102 2.276 2.276 0 012.28 2.28v1.67h1.44a3 3 0 012.91 3.719v.003l-1.01 4.048v.001a3 3 0 01-2.91 2.28h-9.44a1 1 0 01-1-1v-7a1 1 0 011-1h2.434z"
        fillRule="evenodd"
      />
</svg>`;
const downvoteIconSvgstr = `<svg class="jp-icon3" transform="scale(-1,-1)" width="32" height="32" viewBox="0 0 36 36" fill="#616161" xmlns="http://www.w3.org/2000/svg">
  <path
        clipRule="evenodd"
        d="M18.522 12.173l-2.486 4.14v5.723h5.44a1 1 0 00.969-.76l1.01-4.049a1 1 0 00-.97-1.24h-2.44a1 1 0 01-1-1v-2.67a.276.276 0 00-.28-.28.293.293 0 00-.243.136zm-4.486 9.863v-5h-1v5h1zm.434-7l2.338-3.895.002-.003a2.293 2.293 0 011.956-1.102 2.276 2.276 0 012.28 2.28v1.67h1.44a3 3 0 012.91 3.719v.003l-1.01 4.048v.001a3 3 0 01-2.91 2.28h-9.44a1 1 0 01-1-1v-7a1 1 0 011-1h2.434z"
        fillRule="evenodd"
      />
</svg>`;
const upvoteIcon = new _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__.LabIcon({
    name: `${_constants__WEBPACK_IMPORTED_MODULE_1__.EXTENSION_ID}:upvote-icon`,
    svgstr: upvoteIconSvgstr
});
const downvoteIcon = new _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__.LabIcon({
    name: `${_constants__WEBPACK_IMPORTED_MODULE_1__.EXTENSION_ID}:downvote-icon`,
    svgstr: downvoteIconSvgstr
});


/***/ }),

/***/ "./lib/components/MessageFooter/messageFooter.js":
/*!*******************************************************!*\
  !*** ./lib/components/MessageFooter/messageFooter.js ***!
  \*******************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   MessageFooter: () => (/* binding */ MessageFooter)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! react */ "webpack/sharing/consume/default/react");
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _ResponseFeedbackButtons_ResponseFeedbackButtons__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../ResponseFeedbackButtons/ResponseFeedbackButtons */ "./lib/components/ResponseFeedbackButtons/ResponseFeedbackButtons.js");


const MessageFooter = (props) => {
    /* Do not render the feedback controls if:
    1. Not an AI message
    2. The message streaming is still in-progress
    3. q_conversation_id is not defined
    4. q_message_id is not defined
    */
    if ((props.message.type !== 'agent' && props.message.type !== 'agent-stream') ||
        (props.message.type === 'agent-stream' && !props.message.complete) ||
        props.message.metadata.q_conversation_id === undefined ||
        props.message.metadata.q_message_id === undefined) {
        return null;
    }
    return react__WEBPACK_IMPORTED_MODULE_0___default().createElement(_ResponseFeedbackButtons_ResponseFeedbackButtons__WEBPACK_IMPORTED_MODULE_1__.ResponseFeedbackButton, { message: props.message });
};


/***/ }),

/***/ "./lib/components/ResponseFeedbackButtons/ResponseFeedbackButtons.js":
/*!***************************************************************************!*\
  !*** ./lib/components/ResponseFeedbackButtons/ResponseFeedbackButtons.js ***!
  \***************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   ResponseFeedbackButton: () => (/* binding */ ResponseFeedbackButton)
/* harmony export */ });
/* harmony import */ var immer__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! immer */ "webpack/sharing/consume/default/immer/immer");
/* harmony import */ var immer__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(immer__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! react */ "webpack/sharing/consume/default/react");
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _mui_material__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @mui/material */ "./node_modules/@mui/material/Box/Box.js");
/* harmony import */ var _mui_material_IconButton__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! @mui/material/IconButton */ "./node_modules/@mui/material/IconButton/IconButton.js");
/* harmony import */ var _jupyter_ai_core__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @jupyter-ai/core */ "webpack/sharing/consume/default/@jupyter-ai/core");
/* harmony import */ var _jupyter_ai_core__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_jupyter_ai_core__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _Icons_icons__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ../Icons/icons */ "./lib/components/Icons/icons.js");






var FeedbackType;
(function (FeedbackType) {
    FeedbackType["Upvote"] = "upvote";
    FeedbackType["Downvote"] = "downvote";
})(FeedbackType || (FeedbackType = {}));
const buildTelemetryEvent = (type, message) => {
    return {
        type,
        message: {
            id: message.id,
            type: message.type,
            time: message.time,
            metadata: 'metadata' in message ? message.metadata : {}
        }
    };
};
const ResponseFeedbackButton = ({ message }) => {
    const telemetry = (0,_jupyter_ai_core__WEBPACK_IMPORTED_MODULE_2__.useTelemetry)();
    const [feedbackState, setFeedbackState] = react__WEBPACK_IMPORTED_MODULE_1___default().useState({
        submitted: false,
        likeDisabled: false,
        dislikeDisabled: false
    });
    const handleFeedbackSubmit = (feedbackType) => {
        if (feedbackState.submitted) {
            return;
        }
        telemetry.onEvent(buildTelemetryEvent(feedbackType, message));
        setFeedbackState(immer__WEBPACK_IMPORTED_MODULE_0___default()((draft) => {
            draft.submitted = true;
            if (feedbackType === FeedbackType.Upvote) {
                draft.dislikeDisabled = true;
            }
            else {
                draft.likeDisabled = true;
            }
        }));
    };
    return (react__WEBPACK_IMPORTED_MODULE_1___default().createElement(_mui_material__WEBPACK_IMPORTED_MODULE_3__["default"], { sx: {
            display: 'flex',
            justifyContent: 'flex-end',
            alignItems: 'center',
            padding: '6px 2px',
            marginBottom: '1em'
        } },
        react__WEBPACK_IMPORTED_MODULE_1___default().createElement(_mui_material_IconButton__WEBPACK_IMPORTED_MODULE_4__["default"], { sx: {
                padding: '4px',
                ...(feedbackState.likeDisabled && { opacity: 0.5 })
            }, onClick: () => handleFeedbackSubmit(FeedbackType.Upvote), "data-testid": 'upvote-button', disabled: feedbackState.likeDisabled, title: feedbackState.dislikeDisabled
                ? 'Thank you for your feedback'
                : feedbackState.likeDisabled
                    ? undefined
                    : 'Good response' },
            react__WEBPACK_IMPORTED_MODULE_1___default().createElement(_Icons_icons__WEBPACK_IMPORTED_MODULE_5__.upvoteIcon.react, { elementPosition: "center", tag: "span" })),
        react__WEBPACK_IMPORTED_MODULE_1___default().createElement(_mui_material_IconButton__WEBPACK_IMPORTED_MODULE_4__["default"], { sx: {
                padding: '4px',
                ...(feedbackState.dislikeDisabled && { opacity: 0.5 })
            }, onClick: () => handleFeedbackSubmit(FeedbackType.Downvote), "data-testid": 'downvote-button', disabled: feedbackState.dislikeDisabled, title: feedbackState.likeDisabled
                ? 'Thank you for your feedback'
                : feedbackState.dislikeDisabled
                    ? undefined
                    : 'Bad response' },
            react__WEBPACK_IMPORTED_MODULE_1___default().createElement(_Icons_icons__WEBPACK_IMPORTED_MODULE_5__.downvoteIcon.react, { elementPosition: "center", tag: "span" }))));
};


/***/ }),

/***/ "./lib/constants.js":
/*!**************************!*\
  !*** ./lib/constants.js ***!
  \**************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   EXTENSION_ID: () => (/* binding */ EXTENSION_ID),
/* harmony export */   Q_CHIP_BACKGROUND_COLOR_FREE_TIER: () => (/* binding */ Q_CHIP_BACKGROUND_COLOR_FREE_TIER),
/* harmony export */   Q_CHIP_BACKGROUND_COLOR_PAID_TIER_GRADIENT: () => (/* binding */ Q_CHIP_BACKGROUND_COLOR_PAID_TIER_GRADIENT),
/* harmony export */   Q_DEV_TELEMETRY_ENDPOINT: () => (/* binding */ Q_DEV_TELEMETRY_ENDPOINT),
/* harmony export */   SAGEMAKER_AUTH_DETAILS_ENDPOINT: () => (/* binding */ SAGEMAKER_AUTH_DETAILS_ENDPOINT)
/* harmony export */ });
const EXTENSION_ID = '@amzn/amazon_sagemaker_jupyter_ai_q_developer';
const Q_DEV_TELEMETRY_ENDPOINT = '/amazon_sagemaker_jupyter_ai_q_developer/telemetry';
const Q_CHIP_BACKGROUND_COLOR_FREE_TIER = '#414D5C';
const Q_CHIP_BACKGROUND_COLOR_PAID_TIER_GRADIENT = 'linear-gradient(90deg, #3C1987CC 0%, #5073FECC 100%)';
const SAGEMAKER_AUTH_DETAILS_ENDPOINT = '/aws/sagemaker/api/auth-details';


/***/ }),

/***/ "./lib/handler.js":
/*!************************!*\
  !*** ./lib/handler.js ***!
  \************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   OPTIONS_TYPE: () => (/* binding */ OPTIONS_TYPE),
/* harmony export */   requestAPI: () => (/* binding */ requestAPI)
/* harmony export */ });
/* harmony import */ var _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyterlab/coreutils */ "webpack/sharing/consume/default/@jupyterlab/coreutils");
/* harmony import */ var _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _jupyterlab_services__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @jupyterlab/services */ "webpack/sharing/consume/default/@jupyterlab/services");
/* harmony import */ var _jupyterlab_services__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_services__WEBPACK_IMPORTED_MODULE_1__);


const SUCCESS_RESPONSE_STATUS = [200, 201];
var OPTIONS_TYPE;
(function (OPTIONS_TYPE) {
    OPTIONS_TYPE["POST"] = "POST";
    OPTIONS_TYPE["GET"] = "GET";
    OPTIONS_TYPE["PUT"] = "PUT";
})(OPTIONS_TYPE || (OPTIONS_TYPE = {}));
class ApiError extends Error {
    constructor(message, errorStatus, errorCode, cause) {
        super(message);
        this.errorStatus = errorStatus;
        this.errorCode = errorCode;
        this.cause = cause;
        Object.setPrototypeOf(this, ApiError.prototype);
    }
}
const requestAPI = async (endpoint, type, body, headers) => {
    var _a, _b;
    // @TODO: add in logger
    const serverSettings = _jupyterlab_services__WEBPACK_IMPORTED_MODULE_1__.ServerConnection.makeSettings({});
    const requestUrl = _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_0__.URLExt.join(serverSettings.baseUrl, endpoint);
    const init = { method: type };
    if (body) {
        init['body'] = body;
    }
    if (headers) {
        init['headers'] = headers;
    }
    const response = await _jupyterlab_services__WEBPACK_IMPORTED_MODULE_1__.ServerConnection.makeRequest(requestUrl, init, serverSettings);
    if (!SUCCESS_RESPONSE_STATUS.includes(response.status)) {
        const body = await response.json();
        const errorCode = (_a = body.errorCode) !== null && _a !== void 0 ? _a : undefined;
        const errorMessage = (_b = body.errorMessage) !== null && _b !== void 0 ? _b : 'unable to fetch data';
        throw new ApiError(errorMessage, response.status, errorCode);
    }
    return response;
};


/***/ }),

/***/ "./lib/index.js":
/*!**********************!*\
  !*** ./lib/index.js ***!
  \**********************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   customPlaceholderPlugin: () => (/* binding */ customPlaceholderPlugin),
/* harmony export */   customQHeaderPlugin: () => (/* binding */ customQHeaderPlugin),
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__),
/* harmony export */   footerPlugin: () => (/* binding */ footerPlugin),
/* harmony export */   telemetryPlugin: () => (/* binding */ telemetryPlugin),
/* harmony export */   unifiedStudioConcealedLLMConfigPlugin: () => (/* binding */ unifiedStudioConcealedLLMConfigPlugin)
/* harmony export */ });
/* harmony import */ var _jupyter_ai_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyter-ai/core */ "webpack/sharing/consume/default/@jupyter-ai/core");
/* harmony import */ var _jupyter_ai_core__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyter_ai_core__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _handler__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./handler */ "./lib/handler.js");
/* harmony import */ var _utils_environmentUtils__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./utils/environmentUtils */ "./lib/utils/environmentUtils.js");
/* harmony import */ var _components_MessageFooter_messageFooter__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./components/MessageFooter/messageFooter */ "./lib/components/MessageFooter/messageFooter.js");
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./constants */ "./lib/constants.js");
/* harmony import */ var _lumino_widgets__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @lumino/widgets */ "webpack/sharing/consume/default/@lumino/widgets");
/* harmony import */ var _lumino_widgets__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_lumino_widgets__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _components_CustomJAIHeader__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./components/CustomJAIHeader */ "./lib/components/CustomJAIHeader.js");







const telemetryPlugin = {
    id: `${_constants__WEBPACK_IMPORTED_MODULE_2__.EXTENSION_ID}:custom-telemetry`,
    autoStart: true,
    provides: _jupyter_ai_core__WEBPACK_IMPORTED_MODULE_0__.IJaiTelemetryHandler,
    activate: () => {
        console.log('JupyterLab extension telemetry plugin is activated');
        return {
            onEvent: (e) => {
                (0,_handler__WEBPACK_IMPORTED_MODULE_3__.requestAPI)(_constants__WEBPACK_IMPORTED_MODULE_2__.Q_DEV_TELEMETRY_ENDPOINT, _handler__WEBPACK_IMPORTED_MODULE_3__.OPTIONS_TYPE.POST, JSON.stringify(e));
            }
        };
    }
};
const customPlaceholderPlugin = {
    id: `${_constants__WEBPACK_IMPORTED_MODULE_2__.EXTENSION_ID}:custom-placeholder-plugin`,
    autoStart: true,
    requires: [_jupyter_ai_core__WEBPACK_IMPORTED_MODULE_0__.IJaiCore],
    activate: (app, { chatWidget }) => {
        console.log('JupyterLab custom placeholder plugin is activated');
        app.restored.then(() => {
            var _a;
            (_a = chatWidget === null || chatWidget === void 0 ? void 0 : chatWidget.renderPromise) === null || _a === void 0 ? void 0 : _a.then(() => {
                const placeholderText = chatWidget.node.querySelector('*[placeholder="Ask Amazon Q"]');
                if (placeholderText) {
                    placeholderText.placeholder = 'Ask any question or type "/" for actions';
                }
            });
        });
    }
};
const customQHeaderPlugin = {
    id: '@amzn/amazon_sagemaker_jupyter_ai_q_developer:custom-q-header-plugin',
    autoStart: true,
    requires: [_jupyter_ai_core__WEBPACK_IMPORTED_MODULE_0__.IJaiCore],
    activate: (app, { chatWidget }) => {
        app.restored.then(() => {
            var _a;
            const customHeader = new _components_CustomJAIHeader__WEBPACK_IMPORTED_MODULE_4__["default"]();
            (_a = chatWidget === null || chatWidget === void 0 ? void 0 : chatWidget.renderPromise) === null || _a === void 0 ? void 0 : _a.then(() => {
                var _a;
                /**
                 * Customize JupyterLab AI UI. eg. Adding Q tier information
                 */
                const headerHost = (_a = Array.from(chatWidget.node.querySelectorAll('p')).find(p => p.innerText === 'Amazon Q')) === null || _a === void 0 ? void 0 : _a.parentElement;
                if (headerHost) {
                    headerHost.replaceChildren();
                    _lumino_widgets__WEBPACK_IMPORTED_MODULE_1__.Widget.attach(customHeader, headerHost);
                }
            });
        });
        console.log('amazon_sagemaker_jupyter_ai_q_developer:custom-q-header-plugin is activated!');
    }
};
const footerPlugin = {
    id: `${_constants__WEBPACK_IMPORTED_MODULE_2__.EXTENSION_ID}:custom-footer`,
    autoStart: true,
    provides: _jupyter_ai_core__WEBPACK_IMPORTED_MODULE_0__.IJaiMessageFooter,
    activate: (app) => {
        console.log('JupyterLab extension footer plugin is activated');
        return {
            component: _components_MessageFooter_messageFooter__WEBPACK_IMPORTED_MODULE_5__.MessageFooter
        };
    }
};
/**
 * This plugin removes the settings icon in the Jupyter AI chat widget when
 * rendered in SageMaker Unified Studio. This functionality is not
 * currently supported in SageMaker Unified Studio.
 */
const unifiedStudioConcealedLLMConfigPlugin = {
    id: `${_constants__WEBPACK_IMPORTED_MODULE_2__.EXTENSION_ID}:unified-studio-concealed-llm-config-plugin`,
    autoStart: true,
    requires: [_jupyter_ai_core__WEBPACK_IMPORTED_MODULE_0__.IJaiCore],
    activate: (app, { chatWidget }) => {
        app.restored.then(async () => {
            var _a;
            const environment = await (0,_utils_environmentUtils__WEBPACK_IMPORTED_MODULE_6__.fetchCurrentEnvironment)();
            (_a = chatWidget === null || chatWidget === void 0 ? void 0 : chatWidget.renderPromise) === null || _a === void 0 ? void 0 : _a.then(() => {
                var _a, _b;
                // if not SageMaker Unified Studio - do not update the UI.
                if (!environment || ![_utils_environmentUtils__WEBPACK_IMPORTED_MODULE_6__.AppEnvironment.MD_IAM, _utils_environmentUtils__WEBPACK_IMPORTED_MODULE_6__.AppEnvironment.MD_IDC, _utils_environmentUtils__WEBPACK_IMPORTED_MODULE_6__.AppEnvironment.MD_SAML].includes(environment.env))
                    return;
                const actionsBar = (_a = chatWidget.node.firstChild) === null || _a === void 0 ? void 0 : _a.firstChild;
                const settingsButton = (_b = actionsBar === null || actionsBar === void 0 ? void 0 : actionsBar.lastChild) === null || _b === void 0 ? void 0 : _b.lastChild;
                if (settingsButton) {
                    settingsButton.remove();
                }
            });
        });
    }
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = ([telemetryPlugin, footerPlugin, customPlaceholderPlugin, unifiedStudioConcealedLLMConfigPlugin, customQHeaderPlugin]);


/***/ }),

/***/ "./lib/utils/environmentUtils.js":
/*!***************************************!*\
  !*** ./lib/utils/environmentUtils.js ***!
  \***************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   AppEnvironment: () => (/* binding */ AppEnvironment),
/* harmony export */   fetchCurrentEnvironment: () => (/* binding */ fetchCurrentEnvironment)
/* harmony export */ });
/* harmony import */ var _handler__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../handler */ "./lib/handler.js");
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../constants */ "./lib/constants.js");


var AppEnvironment;
(function (AppEnvironment) {
    AppEnvironment["SMStudio"] = "SageMaker Studio";
    AppEnvironment["SMStudioSSO"] = "SageMaker Studio SSO";
    AppEnvironment["MD_IAM"] = "MD_IAM";
    AppEnvironment["MD_IDC"] = "MD_IDC";
    AppEnvironment["MD_SAML"] = "MD_SAML";
    AppEnvironment["UNKNOWN"] = "UNKNOWN";
})(AppEnvironment || (AppEnvironment = {}));
const fetchCurrentEnvironment = async () => {
    try {
        const response = await (0,_handler__WEBPACK_IMPORTED_MODULE_0__.requestAPI)(_constants__WEBPACK_IMPORTED_MODULE_1__.SAGEMAKER_AUTH_DETAILS_ENDPOINT, _handler__WEBPACK_IMPORTED_MODULE_0__.OPTIONS_TYPE.POST);
        const data = await response.json();
        return {
            env: data.environment,
            isQDeveloperEnabled: data.isQDeveloperEnabled
        };
    }
    catch (err) {
        console.error("Failed to fetch environment: ", err);
    }
};



/***/ })

}]);
//# sourceMappingURL=lib_index_js.7e7ce834abc54a0a9cf4.js.map