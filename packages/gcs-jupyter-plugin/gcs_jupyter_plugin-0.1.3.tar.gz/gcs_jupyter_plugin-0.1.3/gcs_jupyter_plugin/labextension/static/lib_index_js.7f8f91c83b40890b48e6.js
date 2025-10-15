"use strict";
(self["webpackChunkgcs_jupyter_plugin"] = self["webpackChunkgcs_jupyter_plugin"] || []).push([["lib_index_js"],{

/***/ "./lib/controls/SidePanelTitleWidget.js":
/*!**********************************************!*\
  !*** ./lib/controls/SidePanelTitleWidget.js ***!
  \**********************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   TitleComponent: () => (/* binding */ TitleComponent),
/* harmony export */   TitleWidget: () => (/* binding */ TitleWidget)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! react */ "webpack/sharing/consume/default/react");
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @jupyterlab/apputils */ "webpack/sharing/consume/default/@jupyterlab/apputils");
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__);
/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */


const TitleComponent = function ({ titleStr, isPreview, styles }) {
    return (react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div", { style: {
            padding: '10px 14px',
            textTransform: 'none',
            fontFamily: 'Roboto',
            fontSize: '15px',
            fontWeight: 600,
            letterSpacing: 0,
            borderBottom: 'var(--jp-border-width) solid var(--jp-border-color2)',
            background: 'var(--jp-layout-color1)',
            ...styles
        } },
        react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div", { className: "gcs-explorer-refresh-container" },
            react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div", null,
                react__WEBPACK_IMPORTED_MODULE_0___default().createElement("span", null, titleStr),
                isPreview ? (react__WEBPACK_IMPORTED_MODULE_0___default().createElement("span", { style: {
                        marginLeft: '5px',
                        fontSize: '13px',
                        padding: '2px',
                        backgroundColor: 'var(--jp-inverse-layout-color2)',
                        color: 'var(--jp-ui-inverse-font-color1)'
                    } }, "PREVIEW")) : null))));
};
class TitleWidget extends _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.ReactWidget {
    constructor(titleStr, isPreview) {
        super();
        this.titleStr = titleStr;
        this.isPreview = isPreview;
        this.node.style.flexShrink = '0';
    }
    render() {
        return (react__WEBPACK_IMPORTED_MODULE_0___default().createElement(TitleComponent, { titleStr: this.titleStr, isPreview: this.isPreview }));
    }
}


/***/ }),

/***/ "./lib/gcs/ProgressBarWidget.js":
/*!**************************************!*\
  !*** ./lib/gcs/ProgressBarWidget.js ***!
  \**************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   ProgressBarWidget: () => (/* binding */ ProgressBarWidget)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! react */ "webpack/sharing/consume/default/react");
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @jupyterlab/apputils */ "webpack/sharing/consume/default/@jupyterlab/apputils");
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__);
/**
 * @license
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */


const IndeterminateProgressBarComponent = () => {
    return (react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div", { style: {
            height: '1px',
            backgroundColor: 'rgba(5, 114, 206, 0.2)',
            width: '100%',
            overflow: 'hidden',
            position: 'relative',
            display: 'block',
            visibility: 'visible',
            opacity: 1,
            border: 'none',
            boxShadow: 'none',
            margin: 0,
            padding: 0
        } },
        react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div", { style: {
                height: '100%',
                width: '100%',
                backgroundColor: 'rgb(25, 118, 210)',
                animation: 'customIndeterminateAnimation 1s infinite linear',
                transformOrigin: '0% 50%',
                display: 'block',
                visibility: 'visible',
                opacity: 1,
                margin: 0,
                padding: 0
            } }),
        react__WEBPACK_IMPORTED_MODULE_0___default().createElement("style", null, `
        @keyframes customIndeterminateAnimation {
          0% {
            transform: translateX(0) scaleX(0);
          }
          40% {
            transform: translateX(0) scaleX(0.4);
          }
          100% {
            transform: translateX(100%) scaleX(0.5);
          }
        }
      `)));
};
class ProgressBarWidget extends _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.ReactWidget {
    constructor() {
        super();
        this.node.style.flexShrink = '0';
        this.node.style.display = 'none'; // Initially hidden
    }
    render() {
        return react__WEBPACK_IMPORTED_MODULE_0___default().createElement(IndeterminateProgressBarComponent, null);
    }
    show() {
        this.node.classList.remove('lm-mod-hidden');
        this.node.style.display = 'flex';
    }
    hide() {
        this.node.classList.add('lm-mod-hidden');
        this.node.style.display = 'none';
    }
}


/***/ }),

/***/ "./lib/gcs/gcsBrowserWidget.js":
/*!*************************************!*\
  !*** ./lib/gcs/gcsBrowserWidget.js ***!
  \*************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   GcsBrowserWidget: () => (/* binding */ GcsBrowserWidget)
/* harmony export */ });
/* harmony import */ var _lumino_widgets__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @lumino/widgets */ "webpack/sharing/consume/default/@lumino/widgets");
/* harmony import */ var _lumino_widgets__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_lumino_widgets__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @jupyterlab/apputils */ "webpack/sharing/consume/default/@jupyterlab/apputils");
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _gcsService__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./gcsService */ "./lib/gcs/gcsService.js");
/* harmony import */ var _controls_SidePanelTitleWidget__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ../controls/SidePanelTitleWidget */ "./lib/controls/SidePanelTitleWidget.js");
/* harmony import */ var _ProgressBarWidget__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./ProgressBarWidget */ "./lib/gcs/ProgressBarWidget.js");
/* harmony import */ var _utils_utils__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! ../utils/utils */ "./lib/utils/utils.js");
/* harmony import */ var _utils_icon__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ../utils/icon */ "./lib/utils/icon.js");
/* harmony import */ var _utils_const__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../utils/const */ "./lib/utils/const.js");
/* harmony import */ var _utils_message__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../utils/message */ "./lib/utils/message.js");
/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */









class GcsBrowserWidget extends _lumino_widgets__WEBPACK_IMPORTED_MODULE_0__.Widget {
    constructor(drive, browser, themeManager) {
        super();
        this.onThemeChanged = () => {
            const isLight = this._themeManager.theme
                ? this._themeManager.isLight(this._themeManager.theme)
                : true;
            const newFolderEnabled = this.newFolder.enabled;
            const gcsUploadEnabled = this.gcsUpload.enabled;
            const refreshButtonEnabled = this.refreshButton.enabled;
            const toggleFileFilterEnabled = this.toggleFileFilter.enabled;
            const browserToolbar = this._browser.toolbar;
            if (this.newFolder && !this.newFolder.isDisposed) {
                this.newFolder.dispose();
            }
            if (this.gcsUpload && !this.gcsUpload.isDisposed) {
                this.gcsUpload.dispose();
            }
            if (this.refreshButton && !this.refreshButton.isDisposed) {
                this.refreshButton.dispose();
            }
            if (this.toggleFileFilter && !this.toggleFileFilter.isDisposed) {
                this.toggleFileFilter.dispose();
            }
            // Re-create buttons with new icons
            this.newFolder = this.createNewFolderButton(isLight);
            this.gcsUpload = this.createUploadButton(isLight);
            this.refreshButton = this.createRefreshButton(isLight);
            this.toggleFileFilter = this.createToggleFileFilterButton(isLight);
            // Restore the enabled state
            this.newFolder.enabled = newFolderEnabled;
            this.gcsUpload.enabled = gcsUploadEnabled;
            this.refreshButton.enabled = refreshButtonEnabled;
            this.toggleFileFilter.enabled = toggleFileFilterEnabled;
            // Add the new buttons back to the toolbar using their original IDs
            if (typeof browserToolbar.addItem === 'function') {
                browserToolbar.addItem(_utils_const__WEBPACK_IMPORTED_MODULE_2__.NEW_FOLDER, this.newFolder);
                browserToolbar.addItem(_utils_const__WEBPACK_IMPORTED_MODULE_2__.FILE_UPLOAD, this.gcsUpload);
                browserToolbar.addItem(_utils_const__WEBPACK_IMPORTED_MODULE_2__.REFRESH, this.refreshButton);
                browserToolbar.addItem(_utils_const__WEBPACK_IMPORTED_MODULE_2__.TOGGLE_FILE_FILTER, this.toggleFileFilter);
            }
            else {
                console.error('Toolbar addItem method not found at runtime. Cannot re-add buttons.');
            }
        };
        // Function to trigger file input dialog when the upload button is clicked
        this.onUploadButtonClick = () => {
            if (this._browser.model.path.split(':')[1] !== '') {
                this.fileInput.click();
            }
            else {
                (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.showDialog)({
                    title: _utils_message__WEBPACK_IMPORTED_MODULE_3__.UPLOAD_ERROR_TITLE,
                    body: _utils_message__WEBPACK_IMPORTED_MODULE_3__.BUCKET_LEVEL_UPLOAD_MESSAGE,
                    buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.Dialog.okButton()]
                });
            }
        };
        this.handleFolderCreation = () => {
            if (this._browser.model.path.split(':')[1] !== '') {
                this._browser.createNewDirectory();
            }
            else {
                (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.showDialog)({
                    title: _utils_message__WEBPACK_IMPORTED_MODULE_3__.FOLDER_CREATION_ERROR_TITLE,
                    body: _utils_message__WEBPACK_IMPORTED_MODULE_3__.BUCKET_LEVEL_FOLDER_CREATION_MESSAGE,
                    buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.Dialog.okButton()]
                });
            }
        };
        // Function to handle file upload
        this.handleFileUpload = async (event) => {
            const input = event.target;
            const files = Array.from(input.files || []);
            // Clear the input element's value to force the 'change' event on subsequent selections
            input.value = '';
            if (files && files.length > 0) {
                files.forEach((fileData) => {
                    const file = fileData;
                    const reader = new FileReader();
                    this.showProgressBar(); // Show spinner for file upload
                    reader.onloadend = async () => {
                        // Upload the file content to Google Cloud Storage
                        const gcsPath = this._browser.model.path.split(':')[1];
                        const path = _gcsService__WEBPACK_IMPORTED_MODULE_4__.GcsService.pathParser(gcsPath);
                        let filePath;
                        if (path.path === '') {
                            filePath = file.name;
                        }
                        else {
                            filePath = path.path + '/' + file.name;
                        }
                        const content = await _gcsService__WEBPACK_IMPORTED_MODULE_4__.GcsService.listFiles({
                            prefix: filePath,
                            bucket: path.bucket
                        });
                        if (content.files && content.files.length > 0) {
                            const result = await (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.showDialog)({
                                title: _utils_message__WEBPACK_IMPORTED_MODULE_3__.FILE_EXIST_TITLE,
                                body: file.name + _utils_message__WEBPACK_IMPORTED_MODULE_3__.FILE_OVERWRITE_MESSAGE,
                                buttons: [
                                    _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.Dialog.cancelButton(),
                                    _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.Dialog.okButton({ label: _utils_message__WEBPACK_IMPORTED_MODULE_3__.OVERWRITE_BUTTON_TEXT })
                                ]
                            });
                            if (result.button.accept) {
                                await _gcsService__WEBPACK_IMPORTED_MODULE_4__.GcsService.saveFile({
                                    bucket: path.bucket,
                                    path: filePath,
                                    contents: reader.result,
                                    upload: false
                                });
                            }
                        }
                        else {
                            await _gcsService__WEBPACK_IMPORTED_MODULE_4__.GcsService.saveFile({
                                bucket: path.bucket,
                                path: filePath,
                                contents: reader.result,
                                upload: true
                            });
                        }
                        await this._browser.model.refresh();
                    };
                    reader.readAsDataURL(file); // Read as Data URL for binary files
                    this.hideProgressBar();
                });
            }
        };
        this.onRefreshButtonClick = async () => {
            this.showProgressBar(); // Show spinner for explicit refresh
            try {
                await this._browser.model.refresh();
            }
            finally {
                this.hideProgressBar(); // Hide after refresh completes
            }
        };
        this.onPathChanged = () => {
            // The below 2 lines of code is added as a workaround for resetting the file filter
            if (this._browser.showFileFilter) {
                this._browser.showFileFilter = false;
                this._browser.showFileFilter = true;
            }
            const currentPath = this._browser.model.path.split(':')[1];
            // Check if the current path is the root (empty string or just '/')
            const isRootPath = currentPath === '' || currentPath === '/';
            // Freeze upload button if path is root
            if (this.gcsUpload) {
                this.gcsUpload.enabled = !isRootPath;
            }
            // Freeze new folder button if path is root
            if (this.newFolder) {
                this.newFolder.enabled = !isRootPath;
            }
        };
        this._browser = browser;
        this._themeManager = themeManager;
        this._browser.showLastModifiedColumn = false;
        this._browser.showFileFilter = false;
        this._browser.showHiddenFiles = true;
        // Create an empty panel layout initially
        this.layout = new _lumino_widgets__WEBPACK_IMPORTED_MODULE_0__.PanelLayout();
        this.node.style.height = '100%';
        this.node.style.display = 'flex';
        this.node.style.flexDirection = 'column';
        this._browser.node.style.overflowY = 'auto'; // Ensure vertical scrolling is enabled if needed
        this._browser.node.style.flexShrink = '1';
        this._browser.node.style.flexGrow = '1';
        // Title widget for the GCS Browser
        this._titleWidget = new _controls_SidePanelTitleWidget__WEBPACK_IMPORTED_MODULE_5__.TitleWidget(_utils_const__WEBPACK_IMPORTED_MODULE_2__.GCS_PLUGIN_TITLE, false);
        this.layout.addWidget(this._titleWidget);
        this._progressBarWidget = new _ProgressBarWidget__WEBPACK_IMPORTED_MODULE_6__.ProgressBarWidget();
        this.layout.addWidget(this._progressBarWidget);
        // Listen for changes in the FileBrowser's path
        this._browser.model.pathChanged.connect(this.onPathChanged, this);
        const originalCd = this._browser.model.cd;
        this._browser.model.cd = async (path) => {
            this.showProgressBar();
            try {
                const result = await originalCd.call(this._browser.model, path);
                return result;
            }
            finally {
                this.hideProgressBar();
            }
        };
        this._browser.showFileCheckboxes = false;
        this.layout.addWidget(this._browser);
        this._browser.node.style.flexShrink = '1';
        this._browser.node.style.flexGrow = '1';
        // Create a file input element
        this.fileInput = document.createElement('input');
        this.fileInput.type = 'file';
        this.fileInput.multiple = true; // Enable multiple file selection
        this.fileInput.style.display = 'none';
        // Attach event listener for file selection
        this.fileInput.addEventListener('change', this.handleFileUpload);
        // Append the file input element to the widget's node
        this.node.appendChild(this.fileInput);
        this.newFolder = this.createNewFolderButton(true);
        this.gcsUpload = this.createUploadButton(true);
        this.refreshButton = this.createRefreshButton(true);
        this.toggleFileFilter = this.createToggleFileFilterButton(true);
        // Since the default location is root. disabling upload and new folder buttons
        this.newFolder.enabled = false;
        this.gcsUpload.enabled = false;
        this._browser.toolbar.addItem(_utils_const__WEBPACK_IMPORTED_MODULE_2__.NEW_FOLDER, this.newFolder);
        this._browser.toolbar.addItem(_utils_const__WEBPACK_IMPORTED_MODULE_2__.FILE_UPLOAD, this.gcsUpload);
        this._browser.toolbar.addItem(_utils_const__WEBPACK_IMPORTED_MODULE_2__.REFRESH, this.refreshButton);
        this._browser.toolbar.addItem(_utils_const__WEBPACK_IMPORTED_MODULE_2__.TOGGLE_FILE_FILTER, this.toggleFileFilter);
        this._themeManager.themeChanged.connect(this.onThemeChanged, this);
        this.onThemeChanged();
    }
    onAfterAttach(msg) {
        super.onAfterAttach(msg);
        // Call initialize asynchronously after widget is attached
        void this.initialize();
    }
    createNewFolderButton(isLight) {
        return new _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.ToolbarButton({
            icon: isLight ? _utils_icon__WEBPACK_IMPORTED_MODULE_7__.iconGCSNewFolder : _utils_icon__WEBPACK_IMPORTED_MODULE_7__.iconGCSNewFolderDark,
            className: 'icon-white',
            onClick: this.handleFolderCreation,
            tooltip: _utils_const__WEBPACK_IMPORTED_MODULE_2__.NEW_FOLDER
        });
    }
    createUploadButton(isLight) {
        return new _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.ToolbarButton({
            icon: isLight ? _utils_icon__WEBPACK_IMPORTED_MODULE_7__.iconGCSUpload : _utils_icon__WEBPACK_IMPORTED_MODULE_7__.iconGCSUploadDark,
            className: 'icon-white jp-UploadIcon',
            onClick: this.onUploadButtonClick,
            tooltip: _utils_const__WEBPACK_IMPORTED_MODULE_2__.FILE_UPLOAD
        });
    }
    createRefreshButton(isLight) {
        return new _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.ToolbarButton({
            icon: isLight ? _utils_icon__WEBPACK_IMPORTED_MODULE_7__.iconGCSRefresh : _utils_icon__WEBPACK_IMPORTED_MODULE_7__.iconGCSRefreshDark,
            className: 'icon-white',
            onClick: () => {
                void this.onRefreshButtonClick();
            },
            tooltip: _utils_const__WEBPACK_IMPORTED_MODULE_2__.REFRESH
        });
    }
    createToggleFileFilterButton(isLight) {
        return new _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.ToolbarButton({
            icon: isLight ? _utils_icon__WEBPACK_IMPORTED_MODULE_7__.iconFileFilter : _utils_icon__WEBPACK_IMPORTED_MODULE_7__.iconFileFilterDark,
            className: 'icon-white',
            onClick: () => {
                this._browser.showFileFilter = !this._browser.showFileFilter;
            },
            tooltip: _utils_const__WEBPACK_IMPORTED_MODULE_2__.TOGGLE_FILE_FILTER
        });
    }
    async initialize() {
        try {
            const credentials = await (0,_utils_utils__WEBPACK_IMPORTED_MODULE_8__.authApi)();
            if ((credentials === null || credentials === void 0 ? void 0 : credentials.login_error) || (credentials === null || credentials === void 0 ? void 0 : credentials.config_error)) {
                this._browser.hide();
                if (credentials) {
                    if (credentials.config_error === 1) {
                        // Config error
                        const errorMessageNode = this.createErrorContainer(_utils_message__WEBPACK_IMPORTED_MODULE_3__.GCLOUD_CONFIG_ERROR);
                        this.node.appendChild(errorMessageNode);
                        return;
                    }
                    if (credentials.login_error === 1) {
                        // Login error
                        const loginContainer = this.createErrorContainer();
                        const loginText = this._createLoginErrorTextElement();
                        const loginButton = this._createLoginButton();
                        loginButton.onclick = () => {
                            // Assuming `login` is globally available
                            (0,_utils_utils__WEBPACK_IMPORTED_MODULE_8__.login)((value) => {
                                if (typeof value === 'boolean' && !value) {
                                    // Retry initialization after successful login
                                    this.initialize();
                                }
                            });
                        };
                        loginButton.appendChild(this._createGoogleIconContainer());
                        loginContainer.appendChild(loginText);
                        loginContainer.appendChild(loginButton);
                        this.node.appendChild(loginContainer);
                        return;
                    }
                }
            }
        }
        catch (error) {
            console.error('Error during initialization:', error);
        }
    }
    createErrorContainer(text) {
        const container = document.createElement('div');
        container.className = 'gcs-error-message'; // Can keep this class or make it more generic
        container.style.textAlign = 'center';
        container.style.marginTop = '20px';
        container.style.alignItems = 'center';
        container.style.justifyContent = 'center';
        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.fontSize = '15px';
        container.style.fontWeight = '600';
        container.style.padding = '11px';
        if (text) {
            container.textContent = text;
        }
        return container;
    }
    _createLoginErrorTextElement() {
        const loginText = document.createElement('div');
        loginText.className = 'login-error';
        loginText.textContent = 'Please login to continue';
        return loginText;
    }
    _createGoogleIconContainer() {
        const googleIconContainer = document.createElement('div');
        googleIconContainer.style.marginTop = '20px';
        googleIconContainer.innerHTML = _utils_icon__WEBPACK_IMPORTED_MODULE_7__.iconSigninGoogle.svgstr;
        return googleIconContainer;
    }
    _createLoginButton() {
        const loginButton = document.createElement('div');
        loginButton.className = 'signin-google-icon logo-alignment-style';
        loginButton.setAttribute('role', 'button');
        loginButton.style.cursor = 'pointer';
        return loginButton;
    }
    async refreshContents() {
        await this._browser.model.refresh();
    }
    showProgressBar() {
        if (this._progressBarWidget) {
            this._progressBarWidget.show();
        }
    }
    hideProgressBar() {
        if (this._progressBarWidget) {
            this._progressBarWidget.hide();
        }
    }
    dispose() {
        this._browser.model.pathChanged.disconnect(this.onPathChanged, this);
        this._browser.dispose();
        this.fileInput.removeEventListener('change', this.handleFileUpload);
        this._themeManager.themeChanged.disconnect(this.onThemeChanged, this);
        this.hideProgressBar();
        super.dispose();
    }
    get browser() {
        return this._browser;
    }
}


/***/ }),

/***/ "./lib/gcs/gcsDrive.js":
/*!*****************************!*\
  !*** ./lib/gcs/gcsDrive.js ***!
  \*****************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   GCSDrive: () => (/* binding */ GCSDrive)
/* harmony export */ });
/* harmony import */ var _jupyterlab_services__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyterlab/services */ "webpack/sharing/consume/default/@jupyterlab/services");
/* harmony import */ var _jupyterlab_services__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_services__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _lumino_signaling__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @lumino/signaling */ "webpack/sharing/consume/default/@lumino/signaling");
/* harmony import */ var _lumino_signaling__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_lumino_signaling__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _gcsService__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./gcsService */ "./lib/gcs/gcsService.js");
/* harmony import */ var react_toastify_dist_ReactToastify_css__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! react-toastify/dist/ReactToastify.css */ "./node_modules/react-toastify/dist/ReactToastify.css");
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @jupyterlab/apputils */ "webpack/sharing/consume/default/@jupyterlab/apputils");
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__);
/* harmony import */ var mime_types__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! mime-types */ "webpack/sharing/consume/default/mime-types/mime-types");
/* harmony import */ var mime_types__WEBPACK_IMPORTED_MODULE_4___default = /*#__PURE__*/__webpack_require__.n(mime_types__WEBPACK_IMPORTED_MODULE_4__);
/* harmony import */ var _utils_const__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ../utils/const */ "./lib/utils/const.js");
/* harmony import */ var _utils_message__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ../utils/message */ "./lib/utils/message.js");
/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */








// Template for an empty Directory IModel.
const DIRECTORY_IMODEL = {
    type: _utils_const__WEBPACK_IMPORTED_MODULE_5__.DIRECTORY,
    path: '',
    name: '',
    format: null,
    content: null,
    created: '',
    writable: true,
    last_modified: '',
    mimetype: ''
};
let untitledFolderSuffix = '';
class GCSDrive {
    constructor(app) {
        this._browserWidget = null;
        this._isDisposed = false;
        this._fileChanged = new _lumino_signaling__WEBPACK_IMPORTED_MODULE_1__.Signal(this);
        this._saveSpinner = null;
        this.selected_panel = null;
        // Not actually used, but the Contents.IDrive interface requires one.
        this.serverSettings = _jupyterlab_services__WEBPACK_IMPORTED_MODULE_0__.ServerConnection.makeSettings();
        this._app = app;
    }
    setBrowserWidget(widget) {
        this._browserWidget = widget;
    }
    get fileChanged() {
        return this._fileChanged;
    }
    get name() {
        return 'gs';
    }
    get isDisposed() {
        return this._isDisposed;
    }
    dispose() {
        if (this.isDisposed) {
            return;
        }
        this._isDisposed = true;
        _lumino_signaling__WEBPACK_IMPORTED_MODULE_1__.Signal.clearData(this);
        if (this._saveSpinner) {
            this._saveSpinner.dispose();
            this._saveSpinner = null;
        }
        this._browserWidget = null;
    }
    showSaveSpinner() {
        const activeWidget = this._app.shell.currentWidget;
        if (!activeWidget) {
            console.warn('No active widget found to show save spinner.');
            return;
        }
        if (!this._saveSpinner) {
            this._saveSpinner = new _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.Spinner();
            this._saveSpinner.addClass('gcs-save-spinner-overlay');
        }
        this._saveSpinner.node.style.backgroundColor = 'transparent';
        activeWidget.node.appendChild(this._saveSpinner.node);
        this._saveSpinner.show();
        activeWidget.node.style.opacity = '0.5';
        activeWidget.node.style.pointerEvents = 'none';
    }
    hideSaveSpinner() {
        if (this._saveSpinner) {
            this._saveSpinner.hide();
            if (this._saveSpinner.node.parentElement) {
                this._saveSpinner.node.parentElement.removeChild(this._saveSpinner.node);
            }
            this._saveSpinner.dispose();
            this._saveSpinner = null;
            const activeWidget = this._app.shell.currentWidget;
            if (activeWidget) {
                activeWidget.node.style.opacity = '';
                activeWidget.node.style.pointerEvents = '';
            }
        }
    }
    async get(localPath, options) {
        /**
         * Logic here is kind of complicated, we have 3 cases that
         * the IDrive interface uses this call for.
         * 1) If path is the root node, list the buckets
         * 2) If path is a directory in a bucket, list all of it's directory and files.
         * 3) If path is a file, return it's metadata and contents.
         */
        if (localPath.length === 0) {
            // Case 1: Return the buckets.
            return await this.getBuckets();
        }
        const request = options || {};
        if (request.type === _utils_const__WEBPACK_IMPORTED_MODULE_5__.FILE || request.type === _utils_const__WEBPACK_IMPORTED_MODULE_5__.NOTEBOOK) {
            return await this.getFile(localPath, options);
        }
        else {
            return await this.getDirectory(localPath);
        }
    }
    /**
     * @returns IModel directory containing all the GCS buckets for the current project.
     */
    async getBuckets() {
        var _a;
        const content = await _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.listBuckets();
        if (!content) {
            throw new Error(`Error Listing Buckets ${content}`);
        }
        return {
            ...DIRECTORY_IMODEL,
            content: (_a = content.map((bucket) => {
                var _a;
                return ({
                    ...DIRECTORY_IMODEL,
                    path: bucket.items.name,
                    name: bucket.items.name,
                    last_modified: (_a = bucket.items.updated) !== null && _a !== void 0 ? _a : new Date().toISOString()
                });
            })) !== null && _a !== void 0 ? _a : []
        };
    }
    /**
     * @returns IModel directory for the given local path.
     */
    async getDirectory(localPath) {
        var _a;
        const path = _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.pathParser(localPath);
        const prefix = path.path.length > 0 ? `${path.path}/` : path.path;
        const content = await _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.listFiles({
            prefix: prefix,
            bucket: path.bucket
        });
        if (!content) {
            throw 'Error Listing Objects';
        }
        let directory_contents = [];
        if (content.prefixes && content.prefixes.length > 0) {
            directory_contents = directory_contents.concat(content.prefixes.map((item) => {
                var _a;
                const pref = item.prefixes.name;
                const path = pref.split('/');
                const name = (_a = path.at(-2)) !== null && _a !== void 0 ? _a : prefix;
                return {
                    ...DIRECTORY_IMODEL,
                    path: `${localPath}/${name}`,
                    name: name,
                    created: new Date().toISOString(),
                    last_modified: new Date().toISOString()
                };
            }));
        }
        if (content.files && content.files.length > 0) {
            directory_contents = directory_contents.concat(content.files.map((item) => {
                var _a, _b, _c, _d;
                const itemName = item.items.name;
                const pathParts = itemName.split('/');
                const name = (_a = pathParts.at(-1)) !== null && _a !== void 0 ? _a : itemName;
                return {
                    type: _utils_const__WEBPACK_IMPORTED_MODULE_5__.FILE,
                    path: `${localPath}/${name}`,
                    name: name,
                    format: 'base64',
                    content: null,
                    created: (_b = item.items.timeCreated) !== null && _b !== void 0 ? _b : new Date().toISOString(),
                    writable: true,
                    last_modified: (_c = item.items.updated) !== null && _c !== void 0 ? _c : new Date().toISOString(),
                    mimetype: (_d = item.items.content_type) !== null && _d !== void 0 ? _d : new Date().toISOString(),
                    size: item.items.size
                };
            }));
        }
        return {
            ...DIRECTORY_IMODEL,
            path: localPath,
            name: (_a = localPath.split('\\').at(-1)) !== null && _a !== void 0 ? _a : '',
            content: directory_contents
        };
    }
    /**
     * @returns IModel file for the given local path.
     */
    async getFile(localPath, options) {
        var _a, _b, _c;
        let fileContent;
        const format = (_a = options === null || options === void 0 ? void 0 : options.format) !== null && _a !== void 0 ? _a : 'text';
        const path = _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.pathParser(localPath);
        const content = await _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.loadFile({
            path: path.path,
            bucket: path.bucket,
            format: format
        });
        if (content === null || typeof content === 'undefined') {
            throw 'File Loading Error';
        }
        if (format === 'text') {
            if (typeof content === 'object') {
                try {
                    fileContent = JSON.stringify(content, null, 2);
                }
                catch (e) {
                    console.error('Failed to stringify content as JSON:', e);
                    fileContent = String(content);
                }
            }
            else {
                fileContent = String(content);
            }
        }
        else {
            fileContent = content;
        }
        return {
            type: _utils_const__WEBPACK_IMPORTED_MODULE_5__.FILE,
            path: localPath,
            name: (_b = localPath.split('\\').at(-1)) !== null && _b !== void 0 ? _b : '',
            format: (_c = options === null || options === void 0 ? void 0 : options.format) !== null && _c !== void 0 ? _c : 'text',
            content: fileContent,
            created: new Date().toISOString(),
            writable: true,
            last_modified: new Date().toISOString(),
            mimetype: ''
        };
    }
    async newUntitled(options) {
        var _a, _b;
        if (this.selected_panel !== _utils_const__WEBPACK_IMPORTED_MODULE_5__.GCS_PLUGIN_TITLE) {
            return Promise.reject(new Error(_utils_message__WEBPACK_IMPORTED_MODULE_7__.NOTEBOOK_CREATION_GCS_CONTEXT_MESSAGE));
        }
        if (!options) {
            console.error(_utils_message__WEBPACK_IMPORTED_MODULE_7__.NO_DATA_PROVIDED_ERROR, options);
            return Promise.reject(new Error(_utils_message__WEBPACK_IMPORTED_MODULE_7__.NO_DATA_PROVIDED_ERROR));
        }
        else if (!options.path) {
            if (options.type === _utils_const__WEBPACK_IMPORTED_MODULE_5__.DIRECTORY) {
                await (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.showDialog)({
                    title: _utils_message__WEBPACK_IMPORTED_MODULE_7__.FOLDER_CREATION_ERROR_TITLE,
                    body: _utils_message__WEBPACK_IMPORTED_MODULE_7__.BUCKET_LEVEL_FOLDER_CREATION_MESSAGE,
                    buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.Dialog.okButton()]
                });
                return Promise.reject();
            }
            else if (options.type === _utils_const__WEBPACK_IMPORTED_MODULE_5__.FILE) {
                await (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.showDialog)({
                    title: _utils_message__WEBPACK_IMPORTED_MODULE_7__.FILE_CREATION_ERROR_TITLE,
                    body: _utils_message__WEBPACK_IMPORTED_MODULE_7__.BUCKET_LEVEL_FILE_CREATION_MESSAGE,
                    buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.Dialog.okButton()]
                });
                return Promise.reject();
            }
            else if (options.type === _utils_const__WEBPACK_IMPORTED_MODULE_5__.NOTEBOOK) {
                return Promise.reject(new Error(_utils_message__WEBPACK_IMPORTED_MODULE_7__.BUCKET_LEVEL_NOTEBOOK_CREATION_MESSAGE));
            }
            else {
                await (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.showDialog)({
                    title: _utils_message__WEBPACK_IMPORTED_MODULE_7__.UNSUPPORTED_CREATE_TITLE,
                    body: _utils_message__WEBPACK_IMPORTED_MODULE_7__.UNSUPPORTED_CREATE_ERROR + options.type,
                    buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.Dialog.okButton()]
                });
                return Promise.reject();
            }
        }
        const localPath = typeof (options === null || options === void 0 ? void 0 : options.path) === 'string' ? options === null || options === void 0 ? void 0 : options.path : '';
        if (localPath === '/' || localPath === '') {
            console.error(_utils_message__WEBPACK_IMPORTED_MODULE_7__.OBJECT_CREATION_AT_ROOT_ERROR_MESSAGE);
            return Promise.reject(new Error(_utils_message__WEBPACK_IMPORTED_MODULE_7__.OBJECT_CREATION_AT_ROOT_ERROR_MESSAGE));
        }
        const parsedPath = _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.pathParser(localPath);
        try {
            (_a = this._browserWidget) === null || _a === void 0 ? void 0 : _a.showProgressBar();
            switch (options.type) {
                case _utils_const__WEBPACK_IMPORTED_MODULE_5__.DIRECTORY:
                    return await this.createNewDirectory(localPath, parsedPath);
                case _utils_const__WEBPACK_IMPORTED_MODULE_5__.FILE:
                    return await this.createNewFile(localPath, parsedPath);
                case _utils_const__WEBPACK_IMPORTED_MODULE_5__.NOTEBOOK:
                    return await this.createNewNotebook(localPath, parsedPath);
                default:
                    console.warn(`Unsupported creation type: ${options.type}`);
                    await (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.showDialog)({
                        title: _utils_message__WEBPACK_IMPORTED_MODULE_7__.UNSUPPORTED_CREATE_TITLE,
                        body: _utils_message__WEBPACK_IMPORTED_MODULE_7__.UNSUPPORTED_CREATE_ERROR + options.type,
                        buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.Dialog.okButton()]
                    });
                    return DIRECTORY_IMODEL;
            }
        }
        finally {
            (_b = this._browserWidget) === null || _b === void 0 ? void 0 : _b.hideProgressBar();
        }
    }
    async createNewDirectory(localPath, parsedPath) {
        const content = await _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.listFiles({
            prefix: parsedPath.path === ''
                ? parsedPath.path + _utils_const__WEBPACK_IMPORTED_MODULE_5__.UNTITLED_DIRECTORY_NAME
                : parsedPath.path + '/' + _utils_const__WEBPACK_IMPORTED_MODULE_5__.UNTITLED_DIRECTORY_NAME,
            bucket: parsedPath.bucket
        });
        if (content.prefixes) {
            let maxSuffix = 1;
            content.prefixes.forEach((data) => {
                const parts = data.prefixes.name.split('/');
                if (parts.length >= 2) {
                    const potentialSuffix = parts[parts.length - 2];
                    const suffixElement = potentialSuffix.match(/\d+$/);
                    if (suffixElement !== null &&
                        parseInt(suffixElement[0]) >= maxSuffix) {
                        maxSuffix = parseInt(suffixElement[0]) + 1;
                    }
                }
                untitledFolderSuffix = maxSuffix.toString();
            });
        }
        else {
            untitledFolderSuffix = '';
        }
        const folderName = _utils_const__WEBPACK_IMPORTED_MODULE_5__.UNTITLED_DIRECTORY_NAME + untitledFolderSuffix;
        const response = await _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.createFolder({
            bucket: parsedPath.bucket,
            path: parsedPath.path,
            folderName: folderName
        });
        if (response) {
            const result = {
                type: _utils_const__WEBPACK_IMPORTED_MODULE_5__.DIRECTORY,
                path: localPath + (localPath.endsWith('/') ? folderName : '/' + folderName),
                name: folderName,
                format: null,
                created: new Date().toISOString(),
                writable: true,
                last_modified: new Date().toISOString(),
                mimetype: '',
                content: null
            };
            return result;
        }
        else {
            console.error('Failed to create folder.');
            await (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.showDialog)({
                title: _utils_message__WEBPACK_IMPORTED_MODULE_7__.FOLDER_CREATION_ERROR_TITLE,
                body: `Folder ${folderName} creation is failed.`,
                buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.Dialog.okButton()]
            });
            return DIRECTORY_IMODEL;
        }
    }
    async createNewFile(localPath, parsedPath) {
        const content = await _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.listFiles({
            prefix: parsedPath.path === ''
                ? parsedPath.path + _utils_const__WEBPACK_IMPORTED_MODULE_5__.UNTITLED_FILE_NAME
                : parsedPath.path + '/' + _utils_const__WEBPACK_IMPORTED_MODULE_5__.UNTITLED_FILE_NAME,
            bucket: parsedPath.bucket
        });
        let maxSuffix = 1;
        const baseFileName = _utils_const__WEBPACK_IMPORTED_MODULE_5__.UNTITLED_FILE_NAME;
        const fileExtension = _utils_const__WEBPACK_IMPORTED_MODULE_5__.UNTITLED_FILE_EXT;
        if (content.files) {
            content.files.forEach((file) => {
                var _a;
                const nameParts = file.items.name.split('/');
                const fileName = (_a = nameParts.at(-1)) !== null && _a !== void 0 ? _a : '';
                const baseNameMatch = fileName.match(/^untitled(\d*)(\..*)?$/);
                if (baseNameMatch) {
                    const suffix = baseNameMatch[1];
                    const ext = baseNameMatch[2] || _utils_const__WEBPACK_IMPORTED_MODULE_5__.UNTITLED_FILE_EXT;
                    if (ext === fileExtension && suffix) {
                        const num = parseInt(suffix);
                        if (!isNaN(num) && num >= maxSuffix) {
                            maxSuffix = num + 1;
                        }
                    }
                    else if (ext === fileExtension &&
                        maxSuffix === 1 &&
                        fileName === `${_utils_const__WEBPACK_IMPORTED_MODULE_5__.UNTITLED_FILE_NAME}${_utils_const__WEBPACK_IMPORTED_MODULE_5__.UNTITLED_FILE_EXT}`) {
                        maxSuffix = 2;
                    }
                }
            });
        }
        const newFileName = maxSuffix > 1
            ? `${baseFileName}${maxSuffix}${fileExtension}`
            : `${baseFileName}${fileExtension}`;
        const filePathInGCS = parsedPath.path === ''
            ? newFileName
            : `${parsedPath.path}/${newFileName}`;
        const response = await _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.saveFile({
            bucket: parsedPath.bucket,
            path: filePathInGCS,
            contents: ''
        });
        if (response) {
            const parts = newFileName.split('.');
            const ext = parts.length > 1 ? `.${parts.slice(1).join('.')}` : '';
            const mimetype = ext === '.json' ? 'application/json' : 'text/plain';
            return {
                type: _utils_const__WEBPACK_IMPORTED_MODULE_5__.FILE,
                path: `${localPath}/${newFileName}`,
                name: newFileName,
                format: 'text',
                content: '',
                created: new Date().toISOString(),
                writable: true,
                last_modified: new Date().toISOString(),
                mimetype: mimetype
            };
        }
        else {
            console.error('Failed to create file.');
            await (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.showDialog)({
                title: _utils_message__WEBPACK_IMPORTED_MODULE_7__.FILE_CREATION_ERROR_TITLE,
                body: `File ${newFileName} creation is failed.`,
                buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.Dialog.okButton()]
            });
            return DIRECTORY_IMODEL;
        }
    }
    async createNewNotebook(localPath, parsedPath) {
        const notebookExtension = _utils_const__WEBPACK_IMPORTED_MODULE_5__.UNTITLED_NOTEBOOK_EXT;
        const baseNotebookName = _utils_const__WEBPACK_IMPORTED_MODULE_5__.UNTITLED_NOTEBOOK_NAME;
        const content = await _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.listFiles({
            prefix: parsedPath.path === ''
                ? parsedPath.path + baseNotebookName
                : parsedPath.path + '/' + baseNotebookName,
            bucket: parsedPath.bucket
        });
        let maxSuffix = 1;
        if (content.files) {
            content.files.forEach((file) => {
                var _a;
                const nameParts = file.items.name.split('/');
                const fileName = (_a = nameParts.at(-1)) !== null && _a !== void 0 ? _a : '';
                const baseNameMatch = fileName.match(/^Untitled(\d*)(\.ipynb)?$/);
                if (baseNameMatch) {
                    const suffix = baseNameMatch[1];
                    const ext = baseNameMatch[2];
                    if (ext === notebookExtension && suffix) {
                        const num = parseInt(suffix);
                        if (!isNaN(num) && num >= maxSuffix) {
                            maxSuffix = num + 1;
                        }
                    }
                    else if (ext === notebookExtension &&
                        maxSuffix === 1 &&
                        fileName === `${_utils_const__WEBPACK_IMPORTED_MODULE_5__.UNTITLED_NOTEBOOK_NAME}${_utils_const__WEBPACK_IMPORTED_MODULE_5__.UNTITLED_NOTEBOOK_EXT}`) {
                        maxSuffix = 2;
                    }
                }
            });
        }
        const newNotebookName = maxSuffix > 1
            ? `${baseNotebookName}${maxSuffix}${notebookExtension}`
            : `${baseNotebookName}${notebookExtension}`;
        const filePathInGCS = parsedPath.path === ''
            ? newNotebookName
            : `${parsedPath.path}/${newNotebookName}`;
        const response = await _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.saveFile({
            bucket: parsedPath.bucket,
            path: filePathInGCS,
            contents: JSON.stringify({
                cells: [],
                metadata: {
                    kernelspec: {
                        display_name: 'Python 3',
                        language: 'python',
                        name: 'python3'
                    },
                    language_info: {
                        codemirror_mode: {
                            name: 'ipython',
                            version: 3
                        },
                        file_extension: '.py',
                        mimetype: 'text/x-python',
                        name: 'python',
                        nbconvert_exporter: 'python',
                        pygments_lexer: 'ipython3',
                        version: '3.x.x'
                    }
                },
                nbformat: 4,
                nbformat_minor: 5
            })
        });
        if (response) {
            return {
                type: _utils_const__WEBPACK_IMPORTED_MODULE_5__.NOTEBOOK,
                path: `${localPath}/${newNotebookName}`,
                name: newNotebookName,
                format: 'json',
                content: null,
                created: new Date().toISOString(),
                writable: true,
                last_modified: new Date().toISOString(),
                mimetype: 'application/x-ipynb+json'
            };
        }
        else {
            console.error('Failed to create notebook.');
            await (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.showDialog)({
                title: _utils_message__WEBPACK_IMPORTED_MODULE_7__.NOTEBOOK_CREATION_ERROR_TITLE,
                body: `Notebook ${newNotebookName} creation failed.`,
                buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.Dialog.okButton()]
            });
            return DIRECTORY_IMODEL;
        }
    }
    async save(localPath, options) {
        var _a, _b;
        try {
            this.showSaveSpinner();
            const path = _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.pathParser(localPath);
            const content = (options === null || options === void 0 ? void 0 : options.format) === 'json'
                ? JSON.stringify(options.content)
                : options === null || options === void 0 ? void 0 : options.content;
            const resp = await _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.saveFile({
                bucket: path.bucket,
                path: path.path,
                contents: content
            });
            return {
                type: _utils_const__WEBPACK_IMPORTED_MODULE_5__.FILE,
                path: localPath,
                name: (_a = localPath.split('\\').at(-1)) !== null && _a !== void 0 ? _a : '',
                format: 'text',
                created: new Date().toISOString(),
                content: '',
                writable: true,
                last_modified: (_b = resp.updated) !== null && _b !== void 0 ? _b : new Date().toISOString(),
                mimetype: '',
                ...options
            };
        }
        finally {
            this.hideSaveSpinner();
        }
    }
    async delete(path) {
        var _a, _b, _c;
        try {
            const localPath = _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.pathParser(path);
            (_a = this._browserWidget) === null || _a === void 0 ? void 0 : _a.showProgressBar();
            const response = await _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.deleteFile({
                bucket: localPath.bucket,
                path: localPath.path
            });
            if (response.status === 200 || response.status === 204) {
                this._fileChanged.emit({
                    type: _utils_const__WEBPACK_IMPORTED_MODULE_5__.DELETE_SIGNAL,
                    oldValue: { path },
                    newValue: null
                });
            }
            else {
                await (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.showDialog)({
                    title: _utils_message__WEBPACK_IMPORTED_MODULE_7__.DELETION_ERROR_TITLE,
                    body: response.error,
                    buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.Dialog.okButton()]
                });
            }
        }
        finally {
            await ((_b = this._browserWidget) === null || _b === void 0 ? void 0 : _b.refreshContents());
            (_c = this._browserWidget) === null || _c === void 0 ? void 0 : _c.hideProgressBar();
        }
    }
    async _preventRootLevelPaste() {
        await (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.showDialog)({
            title: _utils_message__WEBPACK_IMPORTED_MODULE_7__.PASTE_BUCKET_TITLE,
            body: _utils_message__WEBPACK_IMPORTED_MODULE_7__.PASTE_BUCKET_ERROR_MESSAGE,
            buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.Dialog.okButton()]
        });
        return DIRECTORY_IMODEL;
    }
    async rename(path, newLocalPath, options) {
        var _a, _b, _c, _d, _e, _f, _g;
        const oldPath = _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.pathParser(path);
        const newPath = _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.pathParser(newLocalPath);
        if (newPath.path === '') {
            // In the rename operation, it is not possible to get empty path from jupyter.
            // Only while user performs cut/paste operation, it is possible to get empty path.
            return this._preventRootLevelPaste();
        }
        const oldName = (_a = path.split('/').pop()) !== null && _a !== void 0 ? _a : '';
        const isOldPathMeetsFilename = oldName.includes('.') && oldName.lastIndexOf('.') > 0;
        const newName = (_b = newLocalPath.split('/').pop()) !== null && _b !== void 0 ? _b : '';
        const isNewPathMeetsFilename = newName.includes('.') && newName.lastIndexOf('.') > 0;
        if (newLocalPath.split('/')[newLocalPath.split('/').length - 1].length >= 1024) {
            await (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.showDialog)({
                title: _utils_message__WEBPACK_IMPORTED_MODULE_7__.RENAME_ERROR_TITLE,
                body: _utils_message__WEBPACK_IMPORTED_MODULE_7__.NAME_EXCEEDS_MAX_LENGTH_ERROR,
                buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.Dialog.okButton()]
            });
            return DIRECTORY_IMODEL;
        }
        if (!isOldPathMeetsFilename && oldPath.path === '') {
            await (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.showDialog)({
                title: _utils_message__WEBPACK_IMPORTED_MODULE_7__.RENAME_ERROR_TITLE,
                body: _utils_message__WEBPACK_IMPORTED_MODULE_7__.BUCKET_RENAME_ERROR,
                buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.Dialog.okButton()]
            });
            return DIRECTORY_IMODEL;
        }
        else if (isOldPathMeetsFilename && !isNewPathMeetsFilename) {
            // Old path has file name and New file name given dont have extension
            await (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.showDialog)({
                title: _utils_message__WEBPACK_IMPORTED_MODULE_7__.RENAME_ERROR_TITLE,
                body: _utils_message__WEBPACK_IMPORTED_MODULE_7__.INVALID_FILE_NAME_ERROR,
                buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.Dialog.okButton()]
            });
            return DIRECTORY_IMODEL;
        }
        else {
            try {
                (_c = this._browserWidget) === null || _c === void 0 ? void 0 : _c.showProgressBar();
                if (oldPath.path.includes(_utils_const__WEBPACK_IMPORTED_MODULE_5__.UNTITLED_DIRECTORY_NAME + untitledFolderSuffix)) {
                    oldPath.path = oldPath.path + '/';
                    newPath.path = newPath.path + '/';
                    path = path + '/';
                }
                const response = await _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.renameFile({
                    oldBucket: oldPath.bucket,
                    oldPath: oldPath.path,
                    newBucket: newPath.bucket,
                    newPath: newPath.path
                });
                if ((response === null || response === void 0 ? void 0 : response.status) === 200) {
                    await _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.deleteFile({
                        bucket: oldPath.bucket,
                        path: oldPath.path
                    });
                    if (isOldPathMeetsFilename) {
                        // Emitting the Signal ( If file is opened, JupyterLab updates name in the editor. )
                        this._fileChanged.emit({
                            type: _utils_const__WEBPACK_IMPORTED_MODULE_5__.RENAME_SIGNAL,
                            // Creating Model Obj for Both Source and Destination (renamed)
                            oldValue: this.ModelObject(path, isOldPathMeetsFilename),
                            newValue: this.ModelObject(newLocalPath, isNewPathMeetsFilename)
                        });
                        return {
                            type: _utils_const__WEBPACK_IMPORTED_MODULE_5__.FILE,
                            path: newLocalPath,
                            name: (_d = newLocalPath.split('\\').at(-1)) !== null && _d !== void 0 ? _d : '',
                            format: (_e = options === null || options === void 0 ? void 0 : options.format) !== null && _e !== void 0 ? _e : 'text',
                            content: '',
                            created: new Date().toISOString(),
                            writable: true,
                            last_modified: new Date().toISOString(),
                            mimetype: ''
                        };
                    }
                    else {
                        return {
                            type: _utils_const__WEBPACK_IMPORTED_MODULE_5__.DIRECTORY,
                            path: newLocalPath +
                                (newLocalPath.endsWith('/')
                                    ? newLocalPath
                                    : newLocalPath + '/'),
                            name: newName,
                            format: null,
                            created: new Date().toISOString(),
                            writable: true,
                            last_modified: new Date().toISOString(),
                            mimetype: '',
                            content: null
                        };
                    }
                }
                else {
                    await (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.showDialog)({
                        title: _utils_message__WEBPACK_IMPORTED_MODULE_7__.RENAME_ERROR_TITLE,
                        body: response === null || response === void 0 ? void 0 : response.error,
                        buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.Dialog.okButton()]
                    });
                    return DIRECTORY_IMODEL;
                }
            }
            finally {
                await ((_f = this._browserWidget) === null || _f === void 0 ? void 0 : _f.refreshContents());
                (_g = this._browserWidget) === null || _g === void 0 ? void 0 : _g.hideProgressBar();
            }
        }
    }
    ModelObject(path, isPathMeetsFileName) {
        const now = new Date().toISOString();
        const name = path.split('/').at(-1) || '';
        return {
            name: name,
            path: path,
            type: isPathMeetsFileName ? _utils_const__WEBPACK_IMPORTED_MODULE_5__.FILE : _utils_const__WEBPACK_IMPORTED_MODULE_5__.DIRECTORY,
            writable: true,
            created: now,
            last_modified: now,
            content: null,
            format: isPathMeetsFileName ? 'text' : null,
            mimetype: ''
        };
    }
    async getDownloadUrl(localPath, options) {
        var _a, _b, _c, _d;
        const path = _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.pathParser(localPath);
        (_a = this._browserWidget) === null || _a === void 0 ? void 0 : _a.showProgressBar();
        const fileContent = await _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.downloadFile({
            path: path.path,
            bucket: path.bucket,
            name: path.name ? path.name : '',
            format: (_b = options === null || options === void 0 ? void 0 : options.format) !== null && _b !== void 0 ? _b : 'text'
        });
        const fileName = (_c = localPath.split('/').pop()) !== null && _c !== void 0 ? _c : '';
        // if mime not available, then taking default binary type
        const mimeType = typeof mime_types__WEBPACK_IMPORTED_MODULE_4___default().lookup(fileName) === 'string'
            ? String(mime_types__WEBPACK_IMPORTED_MODULE_4___default().lookup(fileName))
            : 'application/octet-stream';
        let blobData;
        if (fileName.endsWith('.ipynb')) {
            blobData = JSON.stringify(fileContent, null, 2);
        }
        else {
            blobData = fileContent;
        }
        const blob = new Blob([blobData], { type: mimeType });
        const url = URL.createObjectURL(blob);
        // Create a temporary anchor element to trigger the download
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        (_d = this._browserWidget) === null || _d === void 0 ? void 0 : _d.hideProgressBar();
        return Promise.reject('Download initiated successfully through alternative approach.');
    }
    async copy(localPath, toLocalDir) {
        var _a, _b, _c, _d;
        (_a = this._browserWidget) === null || _a === void 0 ? void 0 : _a.showProgressBar();
        try {
            if (toLocalDir === '') {
                // empty path means user is trying to paste at bucket level.
                return this._preventRootLevelPaste();
            }
            const parsedSource = _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.pathParser(localPath);
            const parsedDestinationDir = _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.pathParser(toLocalDir);
            const sourceName = (_b = localPath.split('/').pop()) !== null && _b !== void 0 ? _b : '';
            const expectedDestinationPath = `${toLocalDir}/${sourceName}`;
            if (localPath === expectedDestinationPath) {
                await (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.showDialog)({
                    title: _utils_message__WEBPACK_IMPORTED_MODULE_7__.COPY_ERROR_TITLE,
                    body: _utils_message__WEBPACK_IMPORTED_MODULE_7__.COPY_FILE_TO_SAME_LOCATION_ERROR,
                    buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.Dialog.okButton()]
                });
                return DIRECTORY_IMODEL;
            }
            let newFullPathInDestination;
            let copiedModel;
            let sourceGcsPath = parsedSource.path;
            newFullPathInDestination = `${parsedDestinationDir.bucket}/${parsedDestinationDir.path}/${sourceName}`;
            const response = await _gcsService__WEBPACK_IMPORTED_MODULE_6__.GcsService.copyFile({
                sourceBucket: parsedSource.bucket,
                sourcePath: sourceGcsPath,
                destinationBucket: parsedDestinationDir.bucket,
                destinationPath: `${parsedDestinationDir.path}/${sourceName}`
            });
            // Construct the IModel for the newly copied item
            copiedModel = this.ModelObject(newFullPathInDestination, response.isFolder);
            this._fileChanged.emit({
                type: 'new',
                oldValue: null,
                newValue: copiedModel
            });
            return copiedModel;
        }
        catch (error) {
            await (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.showDialog)({
                title: _utils_message__WEBPACK_IMPORTED_MODULE_7__.COPY_ERROR_TITLE,
                body: `${error.message || 'An unknown error occurred.'}`,
                buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.Dialog.okButton()]
            });
            // Return a default value to satisfy the return type
            return DIRECTORY_IMODEL;
        }
        finally {
            // Refresh the browser widget contents to show the newly copied item
            await ((_c = this._browserWidget) === null || _c === void 0 ? void 0 : _c.refreshContents());
            (_d = this._browserWidget) === null || _d === void 0 ? void 0 : _d.hideProgressBar();
        }
    }
    // Checkpoint APIs, not currently supported.
    async createCheckpoint(localPath) {
        return {
            id: '',
            last_modified: ''
        };
    }
    async listCheckpoints(localPath) {
        return [];
    }
    async restoreCheckpoint(localPath, checkpointID) { }
    async deleteCheckpoint(localPath, checkpointID) { }
}


/***/ }),

/***/ "./lib/gcs/gcsService.js":
/*!*******************************!*\
  !*** ./lib/gcs/gcsService.js ***!
  \*******************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   GcsService: () => (/* binding */ GcsService)
/* harmony export */ });
/* harmony import */ var _handler__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../handler */ "./lib/handler.js");
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyterlab/apputils */ "webpack/sharing/consume/default/@jupyterlab/apputils");
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _utils_const__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../utils/const */ "./lib/utils/const.js");
/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */



class GcsService {
    /**
     * Translate a Jupyter Lab file path into tokens.  IE.
     *   gs:bucket-name/directory/file.ipynb
     * (Note that this isn't exactly a gsutil compatible URI)
     * Would translate to:
     * {
     *   bucket: 'bucket-name',
     *   path: 'directory/file.ipynb',
     *   name: 'file.ipynb'
     * }
     * @param localPath The absolute Jupyter file path
     * @returns Object containing the GCS bucket and object ID
     */
    static pathParser(localPath) {
        var _a;
        const matches = (_a = /^(?<bucket>[\w\-\_\.]+)\/?(?<path>.*)/.exec(localPath)) === null || _a === void 0 ? void 0 : _a.groups;
        if (!matches) {
            throw new Error('Invalid Path');
        }
        const path = matches['path'];
        return {
            path: path,
            bucket: matches['bucket'],
            name: path.split('/').at(-1)
        };
    }
    /**
     * Thin wrapper around storage.bucket.list
     * @see https://cloud.google.com/storage/docs/listing-buckets#rest-list-buckets
     */
    static async listBuckets() {
        var _a;
        try {
            const data = (await (0,_handler__WEBPACK_IMPORTED_MODULE_1__.requestAPI)(_utils_const__WEBPACK_IMPORTED_MODULE_2__.LIST_BUCKETS_ENDPOINT));
            return data;
        }
        catch (error) {
            console.error((_a = error === null || error === void 0 ? void 0 : error.message) !== null && _a !== void 0 ? _a : 'Error fetching Buckets');
        }
    }
    /**
     * Thin wrapper around storage.object.list
     * @see https://cloud.google.com/storage/docs/listing-objects
     */
    static async listFiles({ prefix, bucket }) {
        const url = `${_utils_const__WEBPACK_IMPORTED_MODULE_2__.LIST_FILES_ENDPOINT}?prefix=${encodeURIComponent(prefix)}&bucket=${encodeURIComponent(bucket)}`;
        const data = (await (0,_handler__WEBPACK_IMPORTED_MODULE_1__.requestAPI)(url));
        return data;
    }
    /**
     * Thin wrapper around storage.object.download-into-memory
     * @see https://cloud.google.com/storage/docs/downloading-objects-into-memory
     */
    static async loadFile({ bucket, path, format }) {
        const data = (await (0,_handler__WEBPACK_IMPORTED_MODULE_1__.requestAPI)(_utils_const__WEBPACK_IMPORTED_MODULE_2__.LOAD_FILE_ENDPOINT, {
            method: 'POST',
            body: JSON.stringify({
                bucket,
                path,
                format
            })
        }));
        return data;
    }
    /**
     * Thin wrapper around storage.folder.create
     * @see https://cloud.google.com/storage/docs/create-folders
     */
    static async createFolder({ bucket, path, folderName }) {
        const data = await (0,_handler__WEBPACK_IMPORTED_MODULE_1__.requestAPI)(_utils_const__WEBPACK_IMPORTED_MODULE_2__.CREATE_FOLDER_ENDPOINT, {
            method: 'POST',
            body: JSON.stringify({
                bucket,
                path,
                folderName
            })
        });
        return data;
    }
    /**
     * Thin wrapper around storage.object.upload
     * @see https://cloud.google.com/storage/docs/uploading-objects-from-memory
     */
    static async saveFile({ bucket, path, contents, upload = false }) {
        var _a;
        try {
            // Create form data to send the file
            const formData = new FormData();
            formData.append('bucket', bucket);
            formData.append('path', path);
            formData.append('contents', contents);
            formData.append('upload', String(upload));
            const response = await (0,_handler__WEBPACK_IMPORTED_MODULE_1__.requestAPI)(_utils_const__WEBPACK_IMPORTED_MODULE_2__.SAVE_ENDPOINT, {
                method: 'POST',
                body: formData
            });
            return response;
        }
        catch (error) {
            console.error((_a = error === null || error === void 0 ? void 0 : error.message) !== null && _a !== void 0 ? _a : 'Error saving file');
        }
    }
    /**
     * Thin wrapper around storage.object.delete
     * @see https://cloud.google.com/storage/docs/deleting-objects
     */
    static async deleteFile({ bucket, path }) {
        try {
            const response = await (0,_handler__WEBPACK_IMPORTED_MODULE_1__.requestAPI)(_utils_const__WEBPACK_IMPORTED_MODULE_2__.DELETE_ENDPOINT +
                '?bucket=' +
                encodeURIComponent(bucket) +
                '&path=' +
                encodeURIComponent(path), {
                method: 'DELETE'
            });
            return response;
        }
        catch (error) {
            if (typeof error === 'string') {
                throw error;
            }
            else {
                throw new Error('Error deleting file');
            }
        }
    }
    /**
     * Thin wrapper around storage.object.rename
     * @see https://cloud.google.com/storage/docs/copying-renaming-moving-objects
     */
    static async renameFile({ oldBucket, oldPath, newBucket, newPath }) {
        try {
            const response = await (0,_handler__WEBPACK_IMPORTED_MODULE_1__.requestAPI)(_utils_const__WEBPACK_IMPORTED_MODULE_2__.RENAME_ENDPOINT, {
                method: 'PATCH',
                body: JSON.stringify({
                    oldBucket,
                    oldPath,
                    newBucket,
                    newPath
                })
            });
            return response;
        }
        catch (error) {
            await (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.showDialog)({
                title: 'Rename Error',
                body: 'Error renaming file',
                buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.Dialog.okButton()]
            });
            console.error('Error during rename operation:', error);
        }
    }
    /**
     * Thin wrapper around storage.object.copy
     * @see https://cloud.google.com/storage/docs/copying-objects
     */
    static async copyFile({ sourceBucket, sourcePath, destinationBucket, destinationPath }) {
        const response = await (0,_handler__WEBPACK_IMPORTED_MODULE_1__.requestAPI)(_utils_const__WEBPACK_IMPORTED_MODULE_2__.COPY_ENDPOINT, {
            method: 'POST',
            body: JSON.stringify({
                sourceBucket,
                sourcePath,
                destinationBucket,
                destinationPath
            })
        });
        return response;
    }
    /**
     * Thin wrapper around storage.object.download
     * @see https://cloud.google.com/storage/docs/downloading-objects#rest-download-object
     */
    static async downloadFile({ bucket, path, name, format }) {
        const response = (await (0,_handler__WEBPACK_IMPORTED_MODULE_1__.requestAPI)(_utils_const__WEBPACK_IMPORTED_MODULE_2__.LOAD_FILE_ENDPOINT, {
            method: 'POST',
            body: JSON.stringify({
                bucket,
                path,
                name,
                format
            })
        }));
        return response;
    }
}


/***/ }),

/***/ "./lib/handler.js":
/*!************************!*\
  !*** ./lib/handler.js ***!
  \************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   requestAPI: () => (/* binding */ requestAPI)
/* harmony export */ });
/* harmony import */ var _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyterlab/coreutils */ "webpack/sharing/consume/default/@jupyterlab/coreutils");
/* harmony import */ var _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _jupyterlab_services__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @jupyterlab/services */ "webpack/sharing/consume/default/@jupyterlab/services");
/* harmony import */ var _jupyterlab_services__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_services__WEBPACK_IMPORTED_MODULE_1__);
/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */


/**
 * Call the API extension
 *
 * @param endPoint API REST end point for the extension
 * @param init Initial values for the request
 * @returns The response body interpreted as JSON
 */
async function requestAPI(endPoint = '', init = {}) {
    // Make request to Jupyter API
    const settings = _jupyterlab_services__WEBPACK_IMPORTED_MODULE_1__.ServerConnection.makeSettings();
    const requestUrl = _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_0__.URLExt.join(settings.baseUrl, 'gcs-jupyter-plugin', // API Namespace
    endPoint);
    let response;
    try {
        response = await _jupyterlab_services__WEBPACK_IMPORTED_MODULE_1__.ServerConnection.makeRequest(requestUrl, init, settings);
    }
    catch (error) {
        throw new _jupyterlab_services__WEBPACK_IMPORTED_MODULE_1__.ServerConnection.NetworkError(error);
    }
    const rawResponseText = await response.text();
    const contentType = response.headers.get('Content-Type');
    if (!response.ok) {
        // If the response is not ok, throw an error with the response status
        let errorData = undefined;
        if (rawResponseText) {
            try {
                errorData = JSON.parse(rawResponseText);
            }
            catch (parseError) {
                console.warn('Parse Error Occurred: ' + parseError);
                throw new _jupyterlab_services__WEBPACK_IMPORTED_MODULE_1__.ServerConnection.ResponseError(response, `API request failed with status ${response.status}: ${response.statusText}`, response.status + '');
            }
            if (errorData === null || errorData === void 0 ? void 0 : errorData.error) {
                throw new _jupyterlab_services__WEBPACK_IMPORTED_MODULE_1__.ServerConnection.ResponseError(response, errorData.error, errorData.status || response.status);
            }
        }
        // If no error message is found, throw a generic error
        throw new _jupyterlab_services__WEBPACK_IMPORTED_MODULE_1__.ServerConnection.ResponseError(response, `API request failed with status ${response.status}: ${response.statusText}`);
    }
    if (!(contentType === null || contentType === void 0 ? void 0 : contentType.includes('application/json'))) {
        return rawResponseText;
    }
    // If content type is JSON, attempting to parse it
    try {
        return JSON.parse(rawResponseText);
    }
    catch (parseError) {
        console.warn('Parse Error Occurred: ' + parseError);
        return rawResponseText;
    }
}


/***/ }),

/***/ "./lib/index.js":
/*!**********************!*\
  !*** ./lib/index.js ***!
  \**********************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _gcs_gcsDrive__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./gcs/gcsDrive */ "./lib/gcs/gcsDrive.js");
/* harmony import */ var _lumino_widgets__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @lumino/widgets */ "webpack/sharing/consume/default/@lumino/widgets");
/* harmony import */ var _lumino_widgets__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_lumino_widgets__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _utils_loggingService__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! ./utils/loggingService */ "./lib/utils/loggingService.js");
/* harmony import */ var _gcs_gcsBrowserWidget__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ./gcs/gcsBrowserWidget */ "./lib/gcs/gcsBrowserWidget.js");
/* harmony import */ var _jupyterlab_docmanager__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @jupyterlab/docmanager */ "webpack/sharing/consume/default/@jupyterlab/docmanager");
/* harmony import */ var _jupyterlab_docmanager__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_docmanager__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _jupyterlab_filebrowser__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @jupyterlab/filebrowser */ "webpack/sharing/consume/default/@jupyterlab/filebrowser");
/* harmony import */ var _jupyterlab_filebrowser__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_filebrowser__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @jupyterlab/apputils */ "webpack/sharing/consume/default/@jupyterlab/apputils");
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__);
/* harmony import */ var _utils_icon__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./utils/icon */ "./lib/utils/icon.js");
/* harmony import */ var _utils_const__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./utils/const */ "./lib/utils/const.js");
/* harmony import */ var _handler__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(/*! ./handler */ "./lib/handler.js");
/* harmony import */ var _utils_message__WEBPACK_IMPORTED_MODULE_10__ = __webpack_require__(/*! ./utils/message */ "./lib/utils/message.js");
/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */











/**
 * Initialization data for the gcs-jupyter-plugin extension.
 */
const plugin = {
    id: _utils_const__WEBPACK_IMPORTED_MODULE_4__.PLUGIN_ID,
    description: 'A JupyterLab extension.',
    autoStart: true,
    requires: [
        _jupyterlab_filebrowser__WEBPACK_IMPORTED_MODULE_2__.IFileBrowserFactory,
        _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.IThemeManager,
        _jupyterlab_docmanager__WEBPACK_IMPORTED_MODULE_1__.IDocumentManager,
        _jupyterlab_filebrowser__WEBPACK_IMPORTED_MODULE_2__.IDefaultFileBrowser
    ],
    activate: async (app, factory, themeManager, documentManager, defaultBrowser) => {
        console.log('JupyterLab extension gcs-jupyter-plugin is activated!');
        const onThemeChanged = () => {
            const isLightTheme = themeManager.theme
                ? themeManager.isLight(themeManager.theme)
                : true;
            panelGcs.title.icon = isLightTheme ? _utils_icon__WEBPACK_IMPORTED_MODULE_5__.iconStorage : _utils_icon__WEBPACK_IMPORTED_MODULE_5__.iconStorageDark;
        };
        const gcsDrive = new _gcs_gcsDrive__WEBPACK_IMPORTED_MODULE_6__.GCSDrive(app);
        const gcsBrowser = factory.createFileBrowser(_utils_const__WEBPACK_IMPORTED_MODULE_4__.NAMESPACE, {
            driveName: gcsDrive.name,
            refreshInterval: 300000 // 5 mins
        });
        const gcsBrowserWidget = new _gcs_gcsBrowserWidget__WEBPACK_IMPORTED_MODULE_7__.GcsBrowserWidget(gcsDrive, gcsBrowser, themeManager);
        gcsDrive.setBrowserWidget(gcsBrowserWidget);
        documentManager.services.contents.addDrive(gcsDrive);
        const panelGcs = new _lumino_widgets__WEBPACK_IMPORTED_MODULE_0__.Panel();
        panelGcs.id = 'GCS-bucket-tab';
        panelGcs.title.caption = _utils_const__WEBPACK_IMPORTED_MODULE_4__.GCS_PLUGIN_TITLE;
        panelGcs.title.className = 'panel-icons-custom-style';
        panelGcs.addWidget(gcsBrowserWidget);
        defaultBrowser.model.restored.then(() => {
            defaultBrowser.showFileFilter = true;
            defaultBrowser.showFileFilter = false;
        });
        onThemeChanged();
        app.shell.add(panelGcs, 'left', { rank: 1002 });
        _utils_loggingService__WEBPACK_IMPORTED_MODULE_8__.CloudStorageLoggingService.log('Cloud storage is enabled', _utils_loggingService__WEBPACK_IMPORTED_MODULE_8__.LOG_LEVEL.INFO);
        // Filter enabling and disabling when left sidebar changes to streamline notebook creation from launcher.
        app.restored
            .then(async () => {
            var _a, _b;
            try {
                const url = _utils_const__WEBPACK_IMPORTED_MODULE_4__.HEALTH_ENDPOINT;
                await (0,_handler__WEBPACK_IMPORTED_MODULE_9__.requestAPI)(url);
            }
            catch (error) {
                console.error('GCS backend health check failed:', error);
                await (0,_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.showDialog)({
                    title: _utils_message__WEBPACK_IMPORTED_MODULE_10__.JUPYTER_SERVER_ERROR_TITLE,
                    body: _utils_message__WEBPACK_IMPORTED_MODULE_10__.JUPYTER_SERVER_ERROR_MESSAGE,
                    buttons: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_3__.Dialog.okButton()]
                });
            }
            themeManager.themeChanged.connect(onThemeChanged);
            const shellAny = app.shell;
            if ((_b = (_a = shellAny === null || shellAny === void 0 ? void 0 : shellAny._leftHandler) === null || _a === void 0 ? void 0 : _a._sideBar) === null || _b === void 0 ? void 0 : _b.currentChanged) {
                shellAny._leftHandler._sideBar.currentChanged.connect((sender, args) => {
                    if (args.currentTitle._caption === _utils_const__WEBPACK_IMPORTED_MODULE_4__.GCS_PLUGIN_TITLE) {
                        gcsDrive.selected_panel = args.currentTitle._caption;
                        gcsBrowserWidget.browser.showFileFilter = true;
                        gcsBrowserWidget.browser.showFileFilter = false;
                    }
                    else {
                        gcsDrive.selected_panel = args.currentTitle._caption;
                        defaultBrowser.showFileFilter = true;
                        defaultBrowser.showFileFilter = false;
                    }
                });
            }
        })
            .catch(error => {
            console.error('Error during app restoration:', error);
        });
    }
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (plugin);


/***/ }),

/***/ "./lib/utils/const.js":
/*!****************************!*\
  !*** ./lib/utils/const.js ***!
  \****************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   API_HEADER_CONTENT_TYPE: () => (/* binding */ API_HEADER_CONTENT_TYPE),
/* harmony export */   COPY_ENDPOINT: () => (/* binding */ COPY_ENDPOINT),
/* harmony export */   CREATE_FOLDER_ENDPOINT: () => (/* binding */ CREATE_FOLDER_ENDPOINT),
/* harmony export */   CREDENTIAL_ENDPOINT: () => (/* binding */ CREDENTIAL_ENDPOINT),
/* harmony export */   DELETE_ENDPOINT: () => (/* binding */ DELETE_ENDPOINT),
/* harmony export */   DELETE_SIGNAL: () => (/* binding */ DELETE_SIGNAL),
/* harmony export */   DIRECTORY: () => (/* binding */ DIRECTORY),
/* harmony export */   DOWNLOAD_ENDPOINT: () => (/* binding */ DOWNLOAD_ENDPOINT),
/* harmony export */   FILE: () => (/* binding */ FILE),
/* harmony export */   FILE_UPLOAD: () => (/* binding */ FILE_UPLOAD),
/* harmony export */   GCS_PLUGIN_TITLE: () => (/* binding */ GCS_PLUGIN_TITLE),
/* harmony export */   HEALTH_ENDPOINT: () => (/* binding */ HEALTH_ENDPOINT),
/* harmony export */   LIST_BUCKETS_ENDPOINT: () => (/* binding */ LIST_BUCKETS_ENDPOINT),
/* harmony export */   LIST_FILES_ENDPOINT: () => (/* binding */ LIST_FILES_ENDPOINT),
/* harmony export */   LOAD_FILE_ENDPOINT: () => (/* binding */ LOAD_FILE_ENDPOINT),
/* harmony export */   LOGIN_ENDPOINT: () => (/* binding */ LOGIN_ENDPOINT),
/* harmony export */   LOG_ENDPOINT: () => (/* binding */ LOG_ENDPOINT),
/* harmony export */   NAMESPACE: () => (/* binding */ NAMESPACE),
/* harmony export */   NEW_FOLDER: () => (/* binding */ NEW_FOLDER),
/* harmony export */   NOTEBOOK: () => (/* binding */ NOTEBOOK),
/* harmony export */   PLUGIN_ID: () => (/* binding */ PLUGIN_ID),
/* harmony export */   REFRESH: () => (/* binding */ REFRESH),
/* harmony export */   RENAME_ENDPOINT: () => (/* binding */ RENAME_ENDPOINT),
/* harmony export */   RENAME_SIGNAL: () => (/* binding */ RENAME_SIGNAL),
/* harmony export */   SAVE_ENDPOINT: () => (/* binding */ SAVE_ENDPOINT),
/* harmony export */   STATUS_SUCCESS: () => (/* binding */ STATUS_SUCCESS),
/* harmony export */   TOGGLE_FILE_FILTER: () => (/* binding */ TOGGLE_FILE_FILTER),
/* harmony export */   UNTITLED_DIRECTORY_NAME: () => (/* binding */ UNTITLED_DIRECTORY_NAME),
/* harmony export */   UNTITLED_FILE_EXT: () => (/* binding */ UNTITLED_FILE_EXT),
/* harmony export */   UNTITLED_FILE_NAME: () => (/* binding */ UNTITLED_FILE_NAME),
/* harmony export */   UNTITLED_NOTEBOOK_EXT: () => (/* binding */ UNTITLED_NOTEBOOK_EXT),
/* harmony export */   UNTITLED_NOTEBOOK_NAME: () => (/* binding */ UNTITLED_NOTEBOOK_NAME),
/* harmony export */   VERSION_DETAIL: () => (/* binding */ VERSION_DETAIL)
/* harmony export */ });
/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
const { version } = __webpack_require__(/*! ../../package.json */ "./package.json");
const VERSION_DETAIL = version;
/** gcs extension */
const GCS_PLUGIN_TITLE = 'Google Cloud Storage';
const NAMESPACE = 'gcs-jupyter-plugin:gcsBrowser';
const PLUGIN_ID = 'gcs-jupyter-plugin:plugin';
/** auth */
const API_HEADER_CONTENT_TYPE = 'application/json';
const STATUS_SUCCESS = 'SUCCEEDED';
/** API endpoints */
const CREDENTIAL_ENDPOINT = 'credentials';
const LOG_ENDPOINT = 'log';
const LOGIN_ENDPOINT = 'login';
const HEALTH_ENDPOINT = 'health';
const LIST_BUCKETS_ENDPOINT = 'api/storage/listBuckets';
const LIST_FILES_ENDPOINT = 'api/storage/listFiles';
const LOAD_FILE_ENDPOINT = 'api/storage/loadFile';
const CREATE_FOLDER_ENDPOINT = 'api/storage/createFolder';
const SAVE_ENDPOINT = 'api/storage/saveFile';
const DELETE_ENDPOINT = 'api/storage/deleteFile';
const RENAME_ENDPOINT = 'api/storage/renameFile';
const COPY_ENDPOINT = 'api/storage/copyFile';
const DOWNLOAD_ENDPOINT = 'api/storage/downloadFile';
/** toolbar items ( Used in Name and tooltip ) */
const NEW_FOLDER = 'New Folder';
const FILE_UPLOAD = 'File Upload';
const REFRESH = 'Refresh';
const TOGGLE_FILE_FILTER = 'Toggle File Filter';
/** folder creation */
const DIRECTORY = 'directory';
const UNTITLED_DIRECTORY_NAME = 'UntitledFolder';
/** file creation */
const FILE = 'file';
const UNTITLED_FILE_NAME = 'untitled';
const UNTITLED_FILE_EXT = '.txt';
/** notebook creation */
const NOTEBOOK = 'notebook';
const UNTITLED_NOTEBOOK_NAME = 'Untitled';
const UNTITLED_NOTEBOOK_EXT = '.ipynb';
/** Jupyter signals */
const DELETE_SIGNAL = 'delete';
const RENAME_SIGNAL = 'rename';


/***/ }),

/***/ "./lib/utils/icon.js":
/*!***************************!*\
  !*** ./lib/utils/icon.js ***!
  \***************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   iconFileFilter: () => (/* binding */ iconFileFilter),
/* harmony export */   iconFileFilterDark: () => (/* binding */ iconFileFilterDark),
/* harmony export */   iconGCSNewFolder: () => (/* binding */ iconGCSNewFolder),
/* harmony export */   iconGCSNewFolderDark: () => (/* binding */ iconGCSNewFolderDark),
/* harmony export */   iconGCSRefresh: () => (/* binding */ iconGCSRefresh),
/* harmony export */   iconGCSRefreshDark: () => (/* binding */ iconGCSRefreshDark),
/* harmony export */   iconGCSUpload: () => (/* binding */ iconGCSUpload),
/* harmony export */   iconGCSUploadDark: () => (/* binding */ iconGCSUploadDark),
/* harmony export */   iconSigninGoogle: () => (/* binding */ iconSigninGoogle),
/* harmony export */   iconStorage: () => (/* binding */ iconStorage),
/* harmony export */   iconStorageDark: () => (/* binding */ iconStorageDark)
/* harmony export */ });
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyterlab/ui-components */ "webpack/sharing/consume/default/@jupyterlab/ui-components");
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _style_icons_storage_icon_svg__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../../style/icons/storage_icon.svg */ "./style/icons/storage_icon.svg");
/* harmony import */ var _style_icons_Storage_icon_dark_svg__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../style/icons/Storage-icon-dark.svg */ "./style/icons/Storage-icon-dark.svg");
/* harmony import */ var _style_icons_gcs_folder_new_icon_svg__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../../style/icons/gcs_folder_new_icon.svg */ "./style/icons/gcs_folder_new_icon.svg");
/* harmony import */ var _style_icons_gcs_folder_new_icon_dark_theme_svg__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ../../style/icons/gcs_folder_new_icon_dark_theme.svg */ "./style/icons/gcs_folder_new_icon_dark_theme.svg");
/* harmony import */ var _style_icons_gcs_upload_icon_svg__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ../../style/icons/gcs_upload_icon.svg */ "./style/icons/gcs_upload_icon.svg");
/* harmony import */ var _style_icons_gcs_upload_icon_dark_theme_svg__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! ../../style/icons/gcs_upload_icon_dark_theme.svg */ "./style/icons/gcs_upload_icon_dark_theme.svg");
/* harmony import */ var _style_icons_gcs_refresh_button_icon_svg__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ../../style/icons/gcs_refresh_button_icon.svg */ "./style/icons/gcs_refresh_button_icon.svg");
/* harmony import */ var _style_icons_gcs_refresh_button_icon_dark_theme_svg__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(/*! ../../style/icons/gcs_refresh_button_icon_dark_theme.svg */ "./style/icons/gcs_refresh_button_icon_dark_theme.svg");
/* harmony import */ var _style_icons_gcs_filter_icon_svg__WEBPACK_IMPORTED_MODULE_10__ = __webpack_require__(/*! ../../style/icons/gcs_filter_icon.svg */ "./style/icons/gcs_filter_icon.svg");
/* harmony import */ var _style_icons_gcs_filter_icon_dark_theme_svg__WEBPACK_IMPORTED_MODULE_11__ = __webpack_require__(/*! ../../style/icons/gcs_filter_icon_dark_theme.svg */ "./style/icons/gcs_filter_icon_dark_theme.svg");
/* harmony import */ var _style_icons_signin_google_icon_svg__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ../../style/icons/signin_google_icon.svg */ "./style/icons/signin_google_icon.svg");
/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */












const iconStorage = new _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__.LabIcon({
    name: 'launcher:storage-icon',
    svgstr: _style_icons_storage_icon_svg__WEBPACK_IMPORTED_MODULE_1__
});
const iconStorageDark = new _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__.LabIcon({
    name: 'launcher:storage-icon-dark',
    svgstr: _style_icons_Storage_icon_dark_svg__WEBPACK_IMPORTED_MODULE_2__
});
const iconGCSNewFolder = new _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__.LabIcon({
    name: 'gcs-toolbar:gcs-folder-new-icon',
    svgstr: _style_icons_gcs_folder_new_icon_svg__WEBPACK_IMPORTED_MODULE_3__
});
const iconGCSUpload = new _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__.LabIcon({
    name: 'gcs-toolbar:gcs-upload-icon',
    svgstr: _style_icons_gcs_upload_icon_svg__WEBPACK_IMPORTED_MODULE_4__
});
const iconSigninGoogle = new _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__.LabIcon({
    name: 'launcher:signin_google_icon',
    svgstr: _style_icons_signin_google_icon_svg__WEBPACK_IMPORTED_MODULE_5__
});
const iconGCSRefresh = new _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__.LabIcon({
    name: 'gcs-toolbar:gcs-refresh-custom-icon',
    svgstr: _style_icons_gcs_refresh_button_icon_svg__WEBPACK_IMPORTED_MODULE_6__
});
const iconGCSNewFolderDark = new _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__.LabIcon({
    name: 'gcs-toolbar:gcs-folder-new-icon-dark',
    svgstr: _style_icons_gcs_folder_new_icon_dark_theme_svg__WEBPACK_IMPORTED_MODULE_7__
});
const iconGCSUploadDark = new _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__.LabIcon({
    name: 'gcs-toolbar:gcs-upload-icon-dark',
    svgstr: _style_icons_gcs_upload_icon_dark_theme_svg__WEBPACK_IMPORTED_MODULE_8__
});
const iconGCSRefreshDark = new _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__.LabIcon({
    name: 'gcs-toolbar:gcs-refresh-custom-icon-dark',
    svgstr: _style_icons_gcs_refresh_button_icon_dark_theme_svg__WEBPACK_IMPORTED_MODULE_9__
});
const iconFileFilter = new _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__.LabIcon({
    name: 'gcs-toolbar:gcs-filter-icon',
    svgstr: _style_icons_gcs_filter_icon_svg__WEBPACK_IMPORTED_MODULE_10__
});
const iconFileFilterDark = new _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__.LabIcon({
    name: 'gcs-toolbar:gcs-filter-icon-dark',
    svgstr: _style_icons_gcs_filter_icon_dark_theme_svg__WEBPACK_IMPORTED_MODULE_11__
});


/***/ }),

/***/ "./lib/utils/loggingService.js":
/*!*************************************!*\
  !*** ./lib/utils/loggingService.js ***!
  \*************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   CloudStorageLoggingService: () => (/* binding */ CloudStorageLoggingService),
/* harmony export */   LOG_LEVEL: () => (/* binding */ LOG_LEVEL)
/* harmony export */ });
/* harmony import */ var _handler__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../handler */ "./lib/handler.js");
/* harmony import */ var _const__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./const */ "./lib/utils/const.js");
/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */


/**
 * Enum of python log levels.
 */
var LOG_LEVEL;
(function (LOG_LEVEL) {
    LOG_LEVEL[LOG_LEVEL["NOTSET"] = 0] = "NOTSET";
    LOG_LEVEL[LOG_LEVEL["DEBUG"] = 10] = "DEBUG";
    LOG_LEVEL[LOG_LEVEL["INFO"] = 20] = "INFO";
    LOG_LEVEL[LOG_LEVEL["WARN"] = 30] = "WARN";
    LOG_LEVEL[LOG_LEVEL["ERROR"] = 40] = "ERROR";
    LOG_LEVEL[LOG_LEVEL["CRITICAL"] = 50] = "CRITICAL";
})(LOG_LEVEL || (LOG_LEVEL = {}));
class CloudStorageLoggingService {
    /**
     * Helper method to attach a log listener to the toplevel handler.
     */
    static attach() {
        window.addEventListener('error', (e) => {
            try {
                if (e instanceof ErrorEvent) {
                    const { message, filename, lineno, colno, error } = e;
                    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Error/stack
                    const stack = error.stack;
                    const formattedMessage = `Error: ${filename}:${lineno}:${colno}\n${stack}\n${message}\n${JSON.stringify(error)}`;
                    CloudStorageLoggingService.log(formattedMessage, LOG_LEVEL.ERROR);
                    return;
                }
                // TODO: Add fallback if e is not an errorevent.
            }
            catch (e) {
                // Catch everything, because if we throw here
                // we might infinite loop.
            }
        });
    }
    /**
     * Helper method to log fetch request / response to Jupyter Server.
     */
    static async logFetch(input, init, response) {
        var _a;
        const method = (_a = init === null || init === void 0 ? void 0 : init.method) !== null && _a !== void 0 ? _a : 'GET';
        return this.log(`${method} ${input.toString()} ${response.status} ${response.statusText} `, LOG_LEVEL.DEBUG);
    }
    /**
     * Helper method to log a message to Jupyter Server.
     * @param message Message to be logged
     * @param level Python log level
     * @returns Status message OK or Error.
     */
    static async log(message, level = LOG_LEVEL.INFO) {
        const resp = await (0,_handler__WEBPACK_IMPORTED_MODULE_0__.requestAPI)(_const__WEBPACK_IMPORTED_MODULE_1__.LOG_ENDPOINT, {
            body: JSON.stringify({
                message: message,
                level: level
            }),
            method: 'POST'
        });
        return resp['status'];
    }
}


/***/ }),

/***/ "./lib/utils/message.js":
/*!******************************!*\
  !*** ./lib/utils/message.js ***!
  \******************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   BUCKET_LEVEL_FILE_CREATION_MESSAGE: () => (/* binding */ BUCKET_LEVEL_FILE_CREATION_MESSAGE),
/* harmony export */   BUCKET_LEVEL_FOLDER_CREATION_MESSAGE: () => (/* binding */ BUCKET_LEVEL_FOLDER_CREATION_MESSAGE),
/* harmony export */   BUCKET_LEVEL_NOTEBOOK_CREATION_MESSAGE: () => (/* binding */ BUCKET_LEVEL_NOTEBOOK_CREATION_MESSAGE),
/* harmony export */   BUCKET_LEVEL_UPLOAD_MESSAGE: () => (/* binding */ BUCKET_LEVEL_UPLOAD_MESSAGE),
/* harmony export */   BUCKET_RENAME_ERROR: () => (/* binding */ BUCKET_RENAME_ERROR),
/* harmony export */   COPY_ERROR_TITLE: () => (/* binding */ COPY_ERROR_TITLE),
/* harmony export */   COPY_FILE_EXISTS_ERROR: () => (/* binding */ COPY_FILE_EXISTS_ERROR),
/* harmony export */   COPY_FILE_TO_SAME_LOCATION_ERROR: () => (/* binding */ COPY_FILE_TO_SAME_LOCATION_ERROR),
/* harmony export */   COPY_FOLDER_EXISTS_ERROR: () => (/* binding */ COPY_FOLDER_EXISTS_ERROR),
/* harmony export */   COPY_GENERAL_FILE_ERROR: () => (/* binding */ COPY_GENERAL_FILE_ERROR),
/* harmony export */   COPY_GENERAL_FOLDER_ERROR: () => (/* binding */ COPY_GENERAL_FOLDER_ERROR),
/* harmony export */   DELETION_ERROR_TITLE: () => (/* binding */ DELETION_ERROR_TITLE),
/* harmony export */   FILE_CREATION_ERROR_TITLE: () => (/* binding */ FILE_CREATION_ERROR_TITLE),
/* harmony export */   FILE_EXIST_TITLE: () => (/* binding */ FILE_EXIST_TITLE),
/* harmony export */   FILE_OVERWRITE_MESSAGE: () => (/* binding */ FILE_OVERWRITE_MESSAGE),
/* harmony export */   FOLDER_CREATION_ERROR_TITLE: () => (/* binding */ FOLDER_CREATION_ERROR_TITLE),
/* harmony export */   GCLOUD_CONFIG_ERROR: () => (/* binding */ GCLOUD_CONFIG_ERROR),
/* harmony export */   INVALID_FILE_NAME_ERROR: () => (/* binding */ INVALID_FILE_NAME_ERROR),
/* harmony export */   JUPYTER_SERVER_ERROR_MESSAGE: () => (/* binding */ JUPYTER_SERVER_ERROR_MESSAGE),
/* harmony export */   JUPYTER_SERVER_ERROR_TITLE: () => (/* binding */ JUPYTER_SERVER_ERROR_TITLE),
/* harmony export */   NAME_EXCEEDS_MAX_LENGTH_ERROR: () => (/* binding */ NAME_EXCEEDS_MAX_LENGTH_ERROR),
/* harmony export */   NOTEBOOK_CREATION_ERROR_TITLE: () => (/* binding */ NOTEBOOK_CREATION_ERROR_TITLE),
/* harmony export */   NOTEBOOK_CREATION_GCS_CONTEXT_MESSAGE: () => (/* binding */ NOTEBOOK_CREATION_GCS_CONTEXT_MESSAGE),
/* harmony export */   NO_DATA_PROVIDED_ERROR: () => (/* binding */ NO_DATA_PROVIDED_ERROR),
/* harmony export */   OBJECT_CREATION_AT_ROOT_ERROR_MESSAGE: () => (/* binding */ OBJECT_CREATION_AT_ROOT_ERROR_MESSAGE),
/* harmony export */   OVERWRITE_BUTTON_TEXT: () => (/* binding */ OVERWRITE_BUTTON_TEXT),
/* harmony export */   PASTE_BUCKET_ERROR_MESSAGE: () => (/* binding */ PASTE_BUCKET_ERROR_MESSAGE),
/* harmony export */   PASTE_BUCKET_TITLE: () => (/* binding */ PASTE_BUCKET_TITLE),
/* harmony export */   RENAME_ERROR_TITLE: () => (/* binding */ RENAME_ERROR_TITLE),
/* harmony export */   UNSUPPORTED_CREATE_ERROR: () => (/* binding */ UNSUPPORTED_CREATE_ERROR),
/* harmony export */   UNSUPPORTED_CREATE_TITLE: () => (/* binding */ UNSUPPORTED_CREATE_TITLE),
/* harmony export */   UPLOAD_ERROR_TITLE: () => (/* binding */ UPLOAD_ERROR_TITLE)
/* harmony export */ });
/**
 * @license
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
/** config */
const GCLOUD_CONFIG_ERROR = 'Please configure gcloud with account, project-id and region.';
/** jupyter server */
const JUPYTER_SERVER_ERROR_TITLE = 'Jupyter Server Error';
const JUPYTER_SERVER_ERROR_MESSAGE = 'Google Cloud Storage Extension is installed. Please restart your Jupyter Server for the changes to take effect.';
/** Upload */
const UPLOAD_ERROR_TITLE = 'Upload Error';
const BUCKET_LEVEL_UPLOAD_MESSAGE = 'Uploading files at bucket level is not allowed';
const FILE_EXIST_TITLE = 'Upload file';
const FILE_OVERWRITE_MESSAGE = ' already exists. Do you want to overwrite?'; // File Name added as prefix
const OVERWRITE_BUTTON_TEXT = 'Overwrite';
/** Folder Creation */
const FOLDER_CREATION_ERROR_TITLE = 'Error creating folder';
const BUCKET_LEVEL_FOLDER_CREATION_MESSAGE = 'Folders cannot be created outside of a bucket.';
/** File Creation */
const FILE_CREATION_ERROR_TITLE = 'Error Creating File';
const BUCKET_LEVEL_FILE_CREATION_MESSAGE = 'Files cannot be created outside of a bucket.';
/** Notebook Creation */
const NOTEBOOK_CREATION_ERROR_TITLE = 'Error Creating Notebook';
const BUCKET_LEVEL_NOTEBOOK_CREATION_MESSAGE = 'Notebooks have to be created inside a bucket. Open a bucket in the Cloud Storage Browser to create a new notebook.';
const NOTEBOOK_CREATION_GCS_CONTEXT_MESSAGE = 'Cloud Storage Browser has the file system context. To create a notebook in your local file system, switch the file system context by selecting a folder in File Browser.';
/** Object Creation */
const OBJECT_CREATION_AT_ROOT_ERROR_MESSAGE = 'Cannot create new objects in the root directory.';
/** Unsupported Type Creation */
const UNSUPPORTED_CREATE_TITLE = 'Unsupported Type Error';
const UNSUPPORTED_CREATE_ERROR = 'Unsupported creation type : '; // Type added as suffix
/** file operation */
/** Common */
const NO_DATA_PROVIDED_ERROR = 'No data provided for this operation.';
/** deletion */
const DELETION_ERROR_TITLE = 'Deletion Error';
/** rename */
const RENAME_ERROR_TITLE = 'Rename Error';
const NAME_EXCEEDS_MAX_LENGTH_ERROR = 'The maximum object length is 1024 characters.';
const BUCKET_RENAME_ERROR = 'Renaming Bucket is not allowed.';
const INVALID_FILE_NAME_ERROR = 'Invalid File Name Provided.';
/** Pasting in root folder (Bucket) */
const PASTE_BUCKET_TITLE = 'Invalid Destination';
const PASTE_BUCKET_ERROR_MESSAGE = 'Cannot paste files or folders into buckets directory.';
/** Copy Operation */
const COPY_ERROR_TITLE = 'Error Copying File';
const COPY_GENERAL_FILE_ERROR = 'An error occurred while copying the file.';
const COPY_GENERAL_FOLDER_ERROR = 'An error occurred while copying the folder.';
const COPY_FILE_EXISTS_ERROR = 'File already exists in the destination directory.';
const COPY_FOLDER_EXISTS_ERROR = 'Folder already exists.';
const COPY_FILE_TO_SAME_LOCATION_ERROR = 'Cannot copy file to its original location.';


/***/ }),

/***/ "./lib/utils/utils.js":
/*!****************************!*\
  !*** ./lib/utils/utils.js ***!
  \****************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   authApi: () => (/* binding */ authApi),
/* harmony export */   loggedFetch: () => (/* binding */ loggedFetch),
/* harmony export */   login: () => (/* binding */ login),
/* harmony export */   toastifyCustomStyle: () => (/* binding */ toastifyCustomStyle)
/* harmony export */ });
/* harmony import */ var _handler__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../handler */ "./lib/handler.js");
/* harmony import */ var react_toastify__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! react-toastify */ "webpack/sharing/consume/default/react-toastify/react-toastify");
/* harmony import */ var react_toastify__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(react_toastify__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _loggingService__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./loggingService */ "./lib/utils/loggingService.js");
/* harmony import */ var _const__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./const */ "./lib/utils/const.js");
/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */




const toastifyCustomStyle = {
    hideProgressBar: true,
    autoClose: 60000,
    theme: 'dark',
    position: react_toastify__WEBPACK_IMPORTED_MODULE_0__.toast.POSITION.BOTTOM_CENTER
};
const authApi = async () => {
    try {
        const data = await (0,_handler__WEBPACK_IMPORTED_MODULE_1__.requestAPI)(_const__WEBPACK_IMPORTED_MODULE_2__.CREDENTIAL_ENDPOINT, {
            method: 'POST'
        });
        if (typeof data === 'object' && data !== null) {
            const credentials = {
                access_token: data.access_token,
                project_id: data.project_id,
                region_id: data.region_id,
                config_error: data.config_error,
                login_error: data.login_error
            };
            return credentials;
        }
    }
    catch (reason) {
        console.error(`Error on GET credentials.\n${reason}`);
    }
};
const login = async (setLoginError) => {
    const data = await (0,_handler__WEBPACK_IMPORTED_MODULE_1__.requestAPI)(_const__WEBPACK_IMPORTED_MODULE_2__.LOGIN_ENDPOINT, {
        method: 'POST'
    });
    if (typeof data === 'object' && data !== null) {
        const loginStatus = data.login;
        if (loginStatus === _const__WEBPACK_IMPORTED_MODULE_2__.STATUS_SUCCESS) {
            setLoginError(false);
            window.location.reload();
        }
        else {
            setLoginError(true);
        }
    }
};
/**
 * Wraps a fetch call with initial authentication to pass credentials to the request
 *
 * @param uri the endpoint to call e.g. "/clusters"
 * @param method the HTTP method used for the request
 * @param regionIdentifier option param to define what region identifier (location, region) to use
 * @param queryParams
 * @returns a promise of the fetch result
 */
/**
 * Helper method that wraps fetch and logs the request uri and status codes to
 * jupyter server.
 */
async function loggedFetch(input, init) {
    const resp = await fetch(input, init);
    // Intentionally not waiting for log response.
    _loggingService__WEBPACK_IMPORTED_MODULE_3__.CloudStorageLoggingService.logFetch(input, init, resp);
    return resp;
}


/***/ }),

/***/ "./package.json":
/*!**********************!*\
  !*** ./package.json ***!
  \**********************/
/***/ ((module) => {

module.exports = /*#__PURE__*/JSON.parse('{"name":"gcs-jupyter-plugin","version":"0.1.3","description":"A JupyterLab extension.","keywords":["jupyter","jupyterlab","jupyterlab-extension"],"homepage":"https://github.com/GoogleCloudDataproc/gcs-jupyter-plugin","bugs":{"url":"https://github.com/GoogleCloudDataproc/gcs-jupyter-plugin/issues"},"license":"Apache-2.0","author":{"name":"Google","email":"gcs-plugins@google.com"},"files":["lib/**/*.{d.ts,eot,gif,html,jpg,js,js.map,json,png,svg,woff2,ttf}","style/**/*.{css,js,eot,gif,html,jpg,json,png,svg,woff2,ttf}","src/**/*.{ts,tsx}","schema/*.json"],"main":"lib/index.js","types":"lib/index.d.ts","style":"style/index.css","repository":{"type":"git","url":"https://github.com/GoogleCloudDataproc/gcs-jupyter-plugin.git"},"scripts":{"build":"jlpm build:lib && jlpm build:labextension:dev","build:prod":"jlpm clean && jlpm build:lib:prod && jlpm build:labextension","build:labextension":"jupyter labextension build .","build:labextension:dev":"jupyter labextension build --development True .","build:lib":"tsc --sourceMap","build:lib:prod":"tsc","clean":"jlpm clean:lib","clean:lib":"rimraf lib tsconfig.tsbuildinfo","clean:lintcache":"rimraf .eslintcache .stylelintcache","clean:labextension":"rimraf gcs_jupyter_plugin/labextension gcs_jupyter_plugin/_version.py","clean:all":"jlpm clean:lib && jlpm clean:labextension && jlpm clean:lintcache","eslint":"jlpm eslint:check --fix","eslint:check":"eslint . --cache --ext .ts,.tsx","install:extension":"jlpm build","lint":"jlpm stylelint && jlpm prettier && jlpm eslint","lint:check":"jlpm stylelint:check && jlpm prettier:check && jlpm eslint:check","prettier":"jlpm prettier:base --write --list-different","prettier:base":"prettier \\"**/*{.ts,.tsx,.js,.jsx,.css,.json,.md}\\"","prettier:check":"jlpm prettier:base --check","stylelint":"jlpm stylelint:check --fix","stylelint:check":"stylelint --cache \\"style/**/*.css\\"","test":"jest --coverage","watch":"run-p watch:src watch:labextension","watch:src":"tsc -w --sourceMap","watch:labextension":"jupyter labextension watch ."},"dependencies":{"@jupyterlab/application":"^4.0.0","@jupyterlab/coreutils":"^6.0.0","@jupyterlab/services":"^7.0.0","@jupyterlab/settingregistry":"^4.0.0","mime-types":"^3.0.1","react-toastify":"^9.1.3"},"devDependencies":{"@googleapis/storage":"^6.0.0","@jupyterlab/builder":"^4.0.0","@jupyterlab/testutils":"^4.0.0","@types/jest":"^29.2.0","@types/json-schema":"^7.0.11","@types/mime-types":"^2.1.4","@types/react":"^18.0.26","@types/react-addons-linked-state-mixin":"^0.14.22","@typescript-eslint/eslint-plugin":"^6.1.0","@typescript-eslint/parser":"^6.1.0","css-loader":"^6.7.1","eslint":"^8.36.0","eslint-config-prettier":"^8.8.0","eslint-plugin-prettier":"^5.0.0","generate-license-file":"^4.0.0","jest":"^29.2.0","mkdirp":"^1.0.3","npm-run-all2":"^7.0.1","prettier":"^3.0.0","rimraf":"^5.0.1","source-map-loader":"^1.0.2","style-loader":"^3.3.1","stylelint":"^15.10.1","stylelint-config-recommended":"^13.0.0","stylelint-config-standard":"^34.0.0","stylelint-csstree-validator":"^3.0.0","stylelint-prettier":"^4.0.0","typescript":"~5.0.2","yjs":"^13.5.0"},"sideEffects":["style/*.css","style/index.js"],"styleModule":"style/index.js","publishConfig":{"access":"public"},"jupyterlab":{"discovery":{"server":{"managers":["pip"],"base":{"name":"gcs_jupyter_plugin"}}},"extension":true,"outputDir":"gcs_jupyter_plugin/labextension","schemaDir":"schema"},"eslintIgnore":["node_modules","dist","coverage","**/*.d.ts","tests","**/__tests__","ui-tests"],"eslintConfig":{"extends":["eslint:recommended","plugin:@typescript-eslint/eslint-recommended","plugin:@typescript-eslint/recommended","plugin:prettier/recommended"],"parser":"@typescript-eslint/parser","parserOptions":{"project":"tsconfig.json","sourceType":"module"},"plugins":["@typescript-eslint"],"rules":{"@typescript-eslint/naming-convention":["error",{"selector":"interface","format":["PascalCase"],"custom":{"regex":"^I[A-Z]","match":true}}],"@typescript-eslint/no-unused-vars":["warn",{"args":"none"}],"@typescript-eslint/no-explicit-any":"off","@typescript-eslint/no-namespace":"off","@typescript-eslint/no-use-before-define":"off","@typescript-eslint/quotes":["error","single",{"avoidEscape":true,"allowTemplateLiterals":false}],"curly":["error","all"],"eqeqeq":"error","prefer-arrow-callback":"error"}},"prettier":{"singleQuote":true,"trailingComma":"none","arrowParens":"avoid","endOfLine":"auto","overrides":[{"files":"package.json","options":{"tabWidth":4}}]},"stylelint":{"extends":["stylelint-config-recommended","stylelint-config-standard","stylelint-prettier/recommended"],"plugins":["stylelint-csstree-validator"],"rules":{"csstree/validator":true,"property-no-vendor-prefix":null,"selector-class-pattern":"^([a-z][A-z\\\\d]*)(-[A-z\\\\d]+)*$","selector-no-vendor-prefix":null,"value-no-vendor-prefix":null}}}');

/***/ }),

/***/ "./style/icons/Storage-icon-dark.svg":
/*!*******************************************!*\
  !*** ./style/icons/Storage-icon-dark.svg ***!
  \*******************************************/
/***/ ((module) => {

module.exports = "<svg width=\"18\" height=\"18\" viewBox=\"0 0 18 18\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\">\n<path d=\"M2 13.8V11.1H16.4V13.8H2ZM3.35 13.125H4.7V11.775H3.35V13.125ZM2 5.7V3H16.4V5.7H2ZM3.35 5.025H4.7V3.675H3.35V5.025ZM2 9.75V7.05H16.4V9.75H2ZM3.35 9.075H4.7V7.725H3.35V9.075Z\" fill=\"white\"/>\n</svg>\n";

/***/ }),

/***/ "./style/icons/gcs_filter_icon.svg":
/*!*****************************************!*\
  !*** ./style/icons/gcs_filter_icon.svg ***!
  \*****************************************/
/***/ ((module) => {

module.exports = "<?xml version=\"1.0\" encoding=\"utf-8\"?><!-- Uploaded to: SVG Repo, www.svgrepo.com, Generator: SVG Repo Mixer Tools -->\n<svg fill=\"#000000\" width=\"800px\" height=\"800px\" viewBox=\"0 0 24 24\" id=\"filter-alt-3\" data-name=\"Flat Color\" xmlns=\"http://www.w3.org/2000/svg\" class=\"icon flat-color\"><path id=\"primary\" d=\"M20.62,3.17A2,2,0,0,0,18.8,2H5.2A2,2,0,0,0,3.7,5.32L9,11.38V21a1,1,0,0,0,.47.85A1,1,0,0,0,10,22a1,1,0,0,0,.45-.11l4-2A1,1,0,0,0,15,19V11.38l5.3-6.06A2,2,0,0,0,20.62,3.17Z\" style=\"fill: rgb(0, 0, 0);\"></path></svg>";

/***/ }),

/***/ "./style/icons/gcs_filter_icon_dark_theme.svg":
/*!****************************************************!*\
  !*** ./style/icons/gcs_filter_icon_dark_theme.svg ***!
  \****************************************************/
/***/ ((module) => {

module.exports = "<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">\n\r<!-- Uploaded to: SVG Repo, www.svgrepo.com, Transformed by: SVG Repo Mixer Tools -->\n<svg fill=\"#ffffff\" version=\"1.1\" id=\"Layer_1\" xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" width=\"800px\" height=\"800px\" viewBox=\"0 0 100 100\" enable-background=\"new 0 0 100 100\" xml:space=\"preserve\">\n\r<g id=\"SVGRepo_bgCarrier\" stroke-width=\"0\"/>\n\r<g id=\"SVGRepo_tracerCarrier\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n\r<g id=\"SVGRepo_iconCarrier\"> <g> <path d=\"M90,22.292c0-3.508-2.781-6.359-6.258-6.488v-0.012H16.848v0.018c-0.116-0.006-0.231-0.018-0.348-0.018 c-3.59,0-6.5,2.91-6.5,6.5c0,2.045,0.946,3.867,2.423,5.059l30.14,30.139l-0.001,18.599v0.154h0.015 c0.054,1.204,0.727,2.236,1.713,2.8l-0.009,0.016l7.872,4.545c0.066,0.046,0.139,0.079,0.208,0.12l0.028,0.016l0-0.001 c0.502,0.29,1.078,0.469,1.7,0.469c1.887,0,3.417-1.529,3.416-3.416c0-0.09-0.02-0.175-0.026-0.263h0.026l0-23.011l30.417-30.416 l-0.03-0.03C89.185,25.884,90,24.185,90,22.292z M32.249,28.792h0.014l0.001,0.015L32.249,28.792z\"/> </g> </g>\n\r</svg>";

/***/ }),

/***/ "./style/icons/gcs_folder_new_icon.svg":
/*!*********************************************!*\
  !*** ./style/icons/gcs_folder_new_icon.svg ***!
  \*********************************************/
/***/ ((module) => {

module.exports = "<svg width=\"18\" height=\"18\" viewBox=\"0 0 18 18\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\">\n<path fill-rule=\"evenodd\" clip-rule=\"evenodd\" d=\"M9 4.5L7.5 3H3C2.1675 3 1.5075 3.6675 1.5075 4.5L1.5 13.5C1.5 14.3325 2.1675 15 3 15H15C15.8325 15 16.5 14.3325 16.5 13.5V6C16.5 5.1675 15.8325 4.5 15 4.5H9ZM14.25 10.5H12V12.75H10.5V10.5H8.25V9H10.5V6.75H12V9H14.25V10.5Z\" fill=\"black\"/>\n</svg>";

/***/ }),

/***/ "./style/icons/gcs_folder_new_icon_dark_theme.svg":
/*!********************************************************!*\
  !*** ./style/icons/gcs_folder_new_icon_dark_theme.svg ***!
  \********************************************************/
/***/ ((module) => {

module.exports = "<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">\n\r<!-- Uploaded to: SVG Repo, www.svgrepo.com, Transformed by: SVG Repo Mixer Tools -->\n<svg fill=\"#ffffff\" width=\"800px\" height=\"800px\" viewBox=\"0 0 1920 1920\" xmlns=\"http://www.w3.org/2000/svg\" stroke=\"#ffffff\">\n\r<g id=\"SVGRepo_bgCarrier\" stroke-width=\"0\"/>\n\r<g id=\"SVGRepo_tracerCarrier\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n\r<g id=\"SVGRepo_iconCarrier\"> <path d=\"m764.386 112.941 225.882 338.824H225.882v112.94H1920v1072.942c0 93.402-76.01 169.412-169.412 169.412H169.412C76.009 1807.059 0 1731.049 0 1637.647V112.941h764.386ZM1040 858.846H880v240H640v160h240v240h160v-240h240v-160h-240v-240Z\" fill-rule=\"evenodd\"/> </g>\n\r</svg>";

/***/ }),

/***/ "./style/icons/gcs_refresh_button_icon.svg":
/*!*************************************************!*\
  !*** ./style/icons/gcs_refresh_button_icon.svg ***!
  \*************************************************/
/***/ ((module) => {

module.exports = "<?xml version=\"1.0\" encoding=\"utf-8\"?><!-- Uploaded to: SVG Repo, www.svgrepo.com, Generator: SVG Repo Mixer Tools -->\r\n<svg fill=\"#000000\" width=\"800px\" height=\"800px\" viewBox=\"0 0 32 32\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M27.1 14.313V5.396L24.158 8.34c-2.33-2.325-5.033-3.503-8.11-3.503C9.902 4.837 4.901 9.847 4.899 16c.001 6.152 5.003 11.158 11.15 11.16 4.276 0 9.369-2.227 10.836-8.478l.028-.122h-3.23l-.022.068c-1.078 3.242-4.138 5.421-7.613 5.421a8 8 0 0 1-5.691-2.359A7.993 7.993 0 0 1 8 16.001c0-4.438 3.611-8.049 8.05-8.049 2.069 0 3.638.58 5.924 2.573l-3.792 3.789H27.1z\"/></svg>";

/***/ }),

/***/ "./style/icons/gcs_refresh_button_icon_dark_theme.svg":
/*!************************************************************!*\
  !*** ./style/icons/gcs_refresh_button_icon_dark_theme.svg ***!
  \************************************************************/
/***/ ((module) => {

module.exports = "<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">\n\r<!-- Uploaded to: SVG Repo, www.svgrepo.com, Transformed by: SVG Repo Mixer Tools -->\n<svg fill=\"#ffffff\" width=\"800px\" height=\"800px\" viewBox=\"0 0 32 32\" xmlns=\"http://www.w3.org/2000/svg\">\n\r<g id=\"SVGRepo_bgCarrier\" stroke-width=\"0\"/>\n\r<g id=\"SVGRepo_tracerCarrier\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n\r<g id=\"SVGRepo_iconCarrier\">\n\r<path d=\"M27.1 14.313V5.396L24.158 8.34c-2.33-2.325-5.033-3.503-8.11-3.503C9.902 4.837 4.901 9.847 4.899 16c.001 6.152 5.003 11.158 11.15 11.16 4.276 0 9.369-2.227 10.836-8.478l.028-.122h-3.23l-.022.068c-1.078 3.242-4.138 5.421-7.613 5.421a8 8 0 0 1-5.691-2.359A7.993 7.993 0 0 1 8 16.001c0-4.438 3.611-8.049 8.05-8.049 2.069 0 3.638.58 5.924 2.573l-3.792 3.789H27.1z\"/>\n\r</g>\n\r</svg>";

/***/ }),

/***/ "./style/icons/gcs_upload_icon.svg":
/*!*****************************************!*\
  !*** ./style/icons/gcs_upload_icon.svg ***!
  \*****************************************/
/***/ ((module) => {

module.exports = "<svg width=\"18\" height=\"18\" viewBox=\"0 0 18 18\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\">\n<path fill-rule=\"evenodd\" clip-rule=\"evenodd\" d=\"M10.5 9.75V12.75H7.5V9.75H5.25L9 6L12.75 9.75H10.5ZM14.517 7.526C14.006 4.946 11.73 3 9 3C6.833 3 4.954 4.23 4.013 6.026C1.759 6.27 0 8.179 0 10.5C0 12.986 2.014 15 4.5 15H14.25C16.32 15 18 13.32 18 11.25C18 9.27 16.459 7.665 14.517 7.526V7.526Z\" fill=\"black\"/>\n</svg>";

/***/ }),

/***/ "./style/icons/gcs_upload_icon_dark_theme.svg":
/*!****************************************************!*\
  !*** ./style/icons/gcs_upload_icon_dark_theme.svg ***!
  \****************************************************/
/***/ ((module) => {

module.exports = "<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">\n\r<!-- Uploaded to: SVG Repo, www.svgrepo.com, Transformed by: SVG Repo Mixer Tools -->\n<svg width=\"800px\" height=\"800px\" viewBox=\"0 0 48 48\" xmlns=\"http://www.w3.org/2000/svg\" fill=\"#ffffff\">\n\r<g id=\"SVGRepo_bgCarrier\" stroke-width=\"0\"/>\n\r<g id=\"SVGRepo_tracerCarrier\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>\n\r<g id=\"SVGRepo_iconCarrier\"> <title>cloud-upload-solid</title> <g id=\"Layer_2\" data-name=\"Layer 2\"> <g id=\"invisible_box\" data-name=\"invisible box\"> <rect width=\"48\" height=\"48\" fill=\"none\"/> </g> <g id=\"icons_Q2\" data-name=\"icons Q2\"> <path d=\"M40.5,21.8a9.1,9.1,0,0,0-3.4-6.5A9.8,9.8,0,0,0,29.6,13,12.2,12.2,0,0,0,19.5,7a11.6,11.6,0,0,0-8.9,4,12.4,12.4,0,0,0-3.2,8.4,11.8,11.8,0,0,0-5.2,8.2A11.5,11.5,0,0,0,5.3,37.8,12.4,12.4,0,0,0,14,41H34.5c7.7,0,11.3-5.1,11.5-9.9A9.9,9.9,0,0,0,40.5,21.8Zm-7.8,6.4a2,2,0,0,1-3.1.2L26,24.8V36a2,2,0,0,1-4,0V24.8l-3.6,3.6a2,2,0,0,1-3.1-.2,2.1,2.1,0,0,1,.4-2.7l6.9-6.9a1.9,1.9,0,0,1,2.8,0l6.9,6.9A2.1,2.1,0,0,1,32.7,28.2Z\"/> </g> </g> </g>\n\r</svg>";

/***/ }),

/***/ "./style/icons/signin_google_icon.svg":
/*!********************************************!*\
  !*** ./style/icons/signin_google_icon.svg ***!
  \********************************************/
/***/ ((module) => {

module.exports = "<svg width=\"172\" height=\"32\" viewBox=\"0 0 172 32\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\">\n<rect x=\"0.5\" y=\"0.5\" width=\"171\" height=\"31\" rx=\"3.5\" fill=\"white\"/>\n<rect x=\"0.5\" y=\"0.5\" width=\"171\" height=\"31\" rx=\"3.5\" stroke=\"#DADCE0\"/>\n<rect x=\"13.5\" y=\"8.5\" width=\"15\" height=\"15\" fill=\"url(#pattern0_8746_115054)\"/>\n<path d=\"M38.3875 21.224C37.8555 21.224 37.3468 21.1213 36.8615 20.916C36.3761 20.7013 35.9468 20.3887 35.5735 19.978C35.2095 19.5673 34.9388 19.0587 34.7615 18.452L36.2175 17.864C36.3668 18.4053 36.6281 18.858 37.0015 19.222C37.3748 19.586 37.8415 19.768 38.4015 19.768C38.7188 19.768 39.0128 19.712 39.2835 19.6C39.5635 19.488 39.7875 19.3247 39.9555 19.11C40.1235 18.886 40.2075 18.6153 40.2075 18.298C40.2075 17.9993 40.1375 17.7473 39.9975 17.542C39.8575 17.3273 39.6335 17.136 39.3255 16.968C39.0175 16.7907 38.6255 16.618 38.1495 16.45L37.5195 16.226C37.2488 16.1233 36.9735 15.9973 36.6935 15.848C36.4135 15.6987 36.1521 15.5167 35.9095 15.302C35.6761 15.078 35.4895 14.8167 35.3495 14.518C35.2095 14.2193 35.1395 13.874 35.1395 13.482C35.1395 12.978 35.2701 12.5207 35.5315 12.11C35.8021 11.6993 36.1708 11.3727 36.6375 11.13C37.1135 10.878 37.6641 10.752 38.2895 10.752C38.9335 10.752 39.4701 10.8687 39.8995 11.102C40.3381 11.326 40.6788 11.5967 40.9215 11.914C41.1735 12.2313 41.3461 12.5347 41.4395 12.824L40.0535 13.412C39.9975 13.216 39.8948 13.0247 39.7455 12.838C39.6055 12.6513 39.4141 12.4973 39.1715 12.376C38.9381 12.2453 38.6488 12.18 38.3035 12.18C38.0048 12.18 37.7295 12.236 37.4775 12.348C37.2348 12.46 37.0388 12.614 36.8895 12.81C36.7401 12.9967 36.6655 13.216 36.6655 13.468C36.6655 13.832 36.8148 14.1307 37.1135 14.364C37.4121 14.588 37.8461 14.7933 38.4155 14.98L39.0595 15.204C39.3861 15.316 39.7081 15.4513 40.0255 15.61C40.3428 15.7593 40.6321 15.9553 40.8935 16.198C41.1548 16.4313 41.3601 16.7207 41.5095 17.066C41.6681 17.402 41.7475 17.8033 41.7475 18.27C41.7475 18.7833 41.6448 19.2313 41.4395 19.614C41.2435 19.9873 40.9775 20.2953 40.6415 20.538C40.3148 20.7713 39.9508 20.944 39.5495 21.056C39.1575 21.168 38.7701 21.224 38.3875 21.224ZM43.1805 21V13.86H44.6925V21H43.1805ZM43.9365 12.81C43.6565 12.81 43.4138 12.712 43.2085 12.516C43.0125 12.3107 42.9145 12.068 42.9145 11.788C42.9145 11.4987 43.0125 11.2607 43.2085 11.074C43.4138 10.878 43.6565 10.78 43.9365 10.78C44.2258 10.78 44.4685 10.878 44.6645 11.074C44.8605 11.2607 44.9585 11.4987 44.9585 11.788C44.9585 12.068 44.8605 12.3107 44.6645 12.516C44.4685 12.712 44.2258 12.81 43.9365 12.81ZM49.6681 24.248C49.0427 24.248 48.5014 24.1453 48.0441 23.94C47.5961 23.744 47.2321 23.4873 46.9521 23.17C46.6721 22.862 46.4714 22.5447 46.3501 22.218L47.7501 21.63C47.8994 22.0033 48.1374 22.3067 48.4641 22.54C48.8001 22.7827 49.2014 22.904 49.6681 22.904C50.3307 22.904 50.8487 22.708 51.2221 22.316C51.5954 21.924 51.7821 21.3687 51.7821 20.65V19.964H51.6981C51.4741 20.2907 51.1661 20.5567 50.7741 20.762C50.3821 20.9673 49.9294 21.07 49.4161 21.07C48.8094 21.07 48.2494 20.916 47.7361 20.608C47.2321 20.3 46.8261 19.8707 46.5181 19.32C46.2194 18.76 46.0701 18.1067 46.0701 17.36C46.0701 16.604 46.2194 15.9507 46.5181 15.4C46.8261 14.84 47.2321 14.406 47.7361 14.098C48.2494 13.79 48.8094 13.636 49.4161 13.636C49.9294 13.636 50.3821 13.7387 50.7741 13.944C51.1661 14.14 51.4741 14.4107 51.6981 14.756H51.7821V13.86H53.2241V20.622C53.2241 21.3967 53.0701 22.0547 52.7621 22.596C52.4634 23.1373 52.0481 23.548 51.5161 23.828C50.9841 24.108 50.3681 24.248 49.6681 24.248ZM49.6821 19.698C50.0554 19.698 50.4007 19.6093 50.7181 19.432C51.0447 19.2453 51.3014 18.9793 51.4881 18.634C51.6841 18.2793 51.7821 17.8547 51.7821 17.36C51.7821 16.8373 51.6841 16.4033 51.4881 16.058C51.3014 15.7127 51.0447 15.4513 50.7181 15.274C50.4007 15.0967 50.0554 15.008 49.6821 15.008C49.3087 15.008 48.9587 15.0967 48.6321 15.274C48.3147 15.4513 48.0581 15.7173 47.8621 16.072C47.6661 16.4173 47.5681 16.8467 47.5681 17.36C47.5681 17.864 47.6661 18.2933 47.8621 18.648C48.0581 18.9933 48.3147 19.2547 48.6321 19.432C48.9587 19.6093 49.3087 19.698 49.6821 19.698ZM54.9657 21V13.86H56.3937V14.84H56.4777C56.683 14.4947 56.9863 14.21 57.3877 13.986C57.7983 13.7527 58.2463 13.636 58.7317 13.636C59.609 13.636 60.267 13.8973 60.7057 14.42C61.1443 14.9333 61.3637 15.624 61.3637 16.492V21H59.8657V16.688C59.8657 16.1093 59.721 15.6893 59.4317 15.428C59.1423 15.1573 58.7643 15.022 58.2977 15.022C57.9337 15.022 57.6163 15.1247 57.3457 15.33C57.075 15.526 56.8603 15.7873 56.7017 16.114C56.5523 16.4407 56.4777 16.7907 56.4777 17.164V21H54.9657ZM66.327 21V13.86H67.839V21H66.327ZM67.083 12.81C66.803 12.81 66.5603 12.712 66.355 12.516C66.159 12.3107 66.061 12.068 66.061 11.788C66.061 11.4987 66.159 11.2607 66.355 11.074C66.5603 10.878 66.803 10.78 67.083 10.78C67.3723 10.78 67.615 10.878 67.811 11.074C68.007 11.2607 68.105 11.4987 68.105 11.788C68.105 12.068 68.007 12.3107 67.811 12.516C67.615 12.712 67.3723 12.81 67.083 12.81ZM69.5946 21V13.86H71.0226V14.84H71.1066C71.3119 14.4947 71.6152 14.21 72.0166 13.986C72.4272 13.7527 72.8752 13.636 73.3606 13.636C74.2379 13.636 74.8959 13.8973 75.3346 14.42C75.7732 14.9333 75.9926 15.624 75.9926 16.492V21H74.4946V16.688C74.4946 16.1093 74.3499 15.6893 74.0606 15.428C73.7712 15.1573 73.3932 15.022 72.9266 15.022C72.5626 15.022 72.2452 15.1247 71.9746 15.33C71.7039 15.526 71.4892 15.7873 71.3306 16.114C71.1812 16.4407 71.1066 16.7907 71.1066 17.164V21H69.5946ZM82.4539 21L80.1719 13.86H81.8099L83.2799 18.998H83.3359L84.9459 13.86H86.4999L88.1099 18.998H88.1659L89.6359 13.86H91.2459L88.9499 21H87.3679L85.7159 15.834H85.6599L84.0219 21H82.4539ZM92.1942 21V13.86H93.7062V21H92.1942ZM92.9502 12.81C92.6702 12.81 92.4275 12.712 92.2222 12.516C92.0262 12.3107 91.9282 12.068 91.9282 11.788C91.9282 11.4987 92.0262 11.2607 92.2222 11.074C92.4275 10.878 92.6702 10.78 92.9502 10.78C93.2395 10.78 93.4822 10.878 93.6782 11.074C93.8742 11.2607 93.9722 11.4987 93.9722 11.788C93.9722 12.068 93.8742 12.3107 93.6782 12.516C93.4822 12.712 93.2395 12.81 92.9502 12.81ZM94.9438 15.176V13.86H96.2038V11.844H97.7018V13.86H99.4518V15.176H97.7018V18.606C97.7018 18.9793 97.7764 19.2547 97.9258 19.432C98.0844 19.6093 98.3224 19.698 98.6398 19.698C98.7891 19.698 98.9291 19.6793 99.0598 19.642C99.1904 19.5953 99.3351 19.5253 99.4938 19.432V20.902C99.3164 20.9673 99.1344 21.0187 98.9478 21.056C98.7704 21.0933 98.5791 21.112 98.3738 21.112C97.7018 21.112 97.1698 20.916 96.7778 20.524C96.3951 20.132 96.2038 19.6 96.2038 18.928V15.176H94.9438ZM100.903 21V10.976H102.415V13.72L102.331 14.84H102.415C102.611 14.4947 102.91 14.21 103.311 13.986C103.722 13.7527 104.174 13.636 104.669 13.636C105.266 13.636 105.761 13.7573 106.153 14C106.554 14.2427 106.853 14.5787 107.049 15.008C107.245 15.428 107.343 15.9227 107.343 16.492V21H105.845V16.688C105.845 16.3053 105.77 15.9927 105.621 15.75C105.481 15.5073 105.294 15.3253 105.061 15.204C104.828 15.0827 104.566 15.022 104.277 15.022C103.913 15.022 103.591 15.1247 103.311 15.33C103.031 15.5353 102.812 15.806 102.653 16.142C102.494 16.4687 102.415 16.8187 102.415 17.192V21H100.903ZM117.304 21.224C116.585 21.224 115.908 21.0933 115.274 20.832C114.639 20.5707 114.079 20.2067 113.594 19.74C113.118 19.264 112.74 18.7087 112.46 18.074C112.189 17.43 112.054 16.7347 112.054 15.988C112.054 15.2413 112.189 14.5507 112.46 13.916C112.74 13.272 113.118 12.7167 113.594 12.25C114.079 11.774 114.639 11.4053 115.274 11.144C115.908 10.8827 116.585 10.752 117.304 10.752C118.069 10.752 118.774 10.8873 119.418 11.158C120.071 11.4287 120.617 11.8067 121.056 12.292L119.992 13.342C119.777 13.0993 119.53 12.894 119.25 12.726C118.979 12.558 118.68 12.432 118.354 12.348C118.027 12.2547 117.677 12.208 117.304 12.208C116.809 12.208 116.338 12.2967 115.89 12.474C115.442 12.6513 115.045 12.908 114.7 13.244C114.364 13.5707 114.098 13.9673 113.902 14.434C113.706 14.8913 113.608 15.4093 113.608 15.988C113.608 16.5667 113.706 17.0893 113.902 17.556C114.107 18.0133 114.378 18.41 114.714 18.746C115.059 19.0727 115.456 19.3247 115.904 19.502C116.352 19.6793 116.823 19.768 117.318 19.768C117.775 19.768 118.2 19.7027 118.592 19.572C118.993 19.4413 119.343 19.2547 119.642 19.012C119.94 18.7693 120.183 18.4753 120.37 18.13C120.556 17.7753 120.673 17.3787 120.72 16.94H117.29V15.582H122.162C122.18 15.694 122.199 15.8247 122.218 15.974C122.236 16.114 122.246 16.2493 122.246 16.38V16.394C122.246 17.1127 122.12 17.7707 121.868 18.368C121.625 18.9653 121.284 19.4787 120.846 19.908C120.407 20.328 119.884 20.6547 119.278 20.888C118.68 21.112 118.022 21.224 117.304 21.224ZM127.205 21.224C126.467 21.224 125.819 21.056 125.259 20.72C124.699 20.384 124.26 19.9313 123.943 19.362C123.625 18.7833 123.467 18.1393 123.467 17.43C123.467 16.7207 123.625 16.0813 123.943 15.512C124.26 14.9333 124.699 14.476 125.259 14.14C125.819 13.804 126.467 13.636 127.205 13.636C127.933 13.636 128.577 13.8087 129.137 14.154C129.697 14.49 130.135 14.9427 130.453 15.512C130.77 16.0813 130.929 16.7207 130.929 17.43C130.929 18.1393 130.77 18.7833 130.453 19.362C130.135 19.9313 129.697 20.384 129.137 20.72C128.577 21.056 127.933 21.224 127.205 21.224ZM127.205 19.838C127.597 19.838 127.961 19.7447 128.297 19.558C128.633 19.362 128.903 19.0867 129.109 18.732C129.323 18.368 129.431 17.934 129.431 17.43C129.431 16.926 129.323 16.4967 129.109 16.142C128.903 15.778 128.633 15.5027 128.297 15.316C127.961 15.12 127.597 15.022 127.205 15.022C126.813 15.022 126.444 15.12 126.099 15.316C125.763 15.5027 125.487 15.778 125.273 16.142C125.067 16.4967 124.965 16.926 124.965 17.43C124.965 17.934 125.067 18.368 125.273 18.732C125.487 19.0867 125.767 19.362 126.113 19.558C126.458 19.7447 126.822 19.838 127.205 19.838ZM135.64 21.224C134.903 21.224 134.254 21.056 133.694 20.72C133.134 20.384 132.695 19.9313 132.378 19.362C132.061 18.7833 131.902 18.1393 131.902 17.43C131.902 16.7207 132.061 16.0813 132.378 15.512C132.695 14.9333 133.134 14.476 133.694 14.14C134.254 13.804 134.903 13.636 135.64 13.636C136.368 13.636 137.012 13.8087 137.572 14.154C138.132 14.49 138.571 14.9427 138.888 15.512C139.205 16.0813 139.364 16.7207 139.364 17.43C139.364 18.1393 139.205 18.7833 138.888 19.362C138.571 19.9313 138.132 20.384 137.572 20.72C137.012 21.056 136.368 21.224 135.64 21.224ZM135.64 19.838C136.032 19.838 136.396 19.7447 136.732 19.558C137.068 19.362 137.339 19.0867 137.544 18.732C137.759 18.368 137.866 17.934 137.866 17.43C137.866 16.926 137.759 16.4967 137.544 16.142C137.339 15.778 137.068 15.5027 136.732 15.316C136.396 15.12 136.032 15.022 135.64 15.022C135.248 15.022 134.879 15.12 134.534 15.316C134.198 15.5027 133.923 15.778 133.708 16.142C133.503 16.4967 133.4 16.926 133.4 17.43C133.4 17.934 133.503 18.368 133.708 18.732C133.923 19.0867 134.203 19.362 134.548 19.558C134.893 19.7447 135.257 19.838 135.64 19.838ZM143.936 24.248C143.31 24.248 142.769 24.1453 142.312 23.94C141.864 23.744 141.5 23.4873 141.22 23.17C140.94 22.862 140.739 22.5447 140.618 22.218L142.018 21.63C142.167 22.0033 142.405 22.3067 142.732 22.54C143.068 22.7827 143.469 22.904 143.936 22.904C144.598 22.904 145.116 22.708 145.49 22.316C145.863 21.924 146.05 21.3687 146.05 20.65V19.964H145.966C145.742 20.2907 145.434 20.5567 145.042 20.762C144.65 20.9673 144.197 21.07 143.684 21.07C143.077 21.07 142.517 20.916 142.004 20.608C141.5 20.3 141.094 19.8707 140.786 19.32C140.487 18.76 140.338 18.1067 140.338 17.36C140.338 16.604 140.487 15.9507 140.786 15.4C141.094 14.84 141.5 14.406 142.004 14.098C142.517 13.79 143.077 13.636 143.684 13.636C144.197 13.636 144.65 13.7387 145.042 13.944C145.434 14.14 145.742 14.4107 145.966 14.756H146.05V13.86H147.492V20.622C147.492 21.3967 147.338 22.0547 147.03 22.596C146.731 23.1373 146.316 23.548 145.784 23.828C145.252 24.108 144.636 24.248 143.936 24.248ZM143.95 19.698C144.323 19.698 144.668 19.6093 144.986 19.432C145.312 19.2453 145.569 18.9793 145.756 18.634C145.952 18.2793 146.05 17.8547 146.05 17.36C146.05 16.8373 145.952 16.4033 145.756 16.058C145.569 15.7127 145.312 15.4513 144.986 15.274C144.668 15.0967 144.323 15.008 143.95 15.008C143.576 15.008 143.226 15.0967 142.9 15.274C142.582 15.4513 142.326 15.7173 142.13 16.072C141.934 16.4173 141.836 16.8467 141.836 17.36C141.836 17.864 141.934 18.2933 142.13 18.648C142.326 18.9933 142.582 19.2547 142.9 19.432C143.226 19.6093 143.576 19.698 143.95 19.698ZM149.233 21V10.976H150.745V21H149.233ZM155.763 21.224C155.063 21.224 154.437 21.0607 153.887 20.734C153.336 20.4073 152.902 19.9593 152.585 19.39C152.277 18.8207 152.123 18.172 152.123 17.444C152.123 16.7627 152.272 16.1327 152.571 15.554C152.869 14.9753 153.285 14.5133 153.817 14.168C154.358 13.8133 154.979 13.636 155.679 13.636C156.416 13.636 157.041 13.7947 157.555 14.112C158.077 14.4293 158.474 14.8633 158.745 15.414C159.015 15.9647 159.151 16.5853 159.151 17.276C159.151 17.3787 159.146 17.472 159.137 17.556C159.137 17.64 159.132 17.7053 159.123 17.752H153.607C153.644 18.144 153.742 18.4847 153.901 18.774C154.106 19.138 154.377 19.4133 154.713 19.6C155.049 19.7867 155.413 19.88 155.805 19.88C156.281 19.88 156.677 19.7727 156.995 19.558C157.321 19.334 157.578 19.0587 157.765 18.732L159.011 19.334C158.703 19.894 158.283 20.3513 157.751 20.706C157.219 21.0513 156.556 21.224 155.763 21.224ZM153.691 16.618H157.653C157.643 16.4407 157.597 16.254 157.513 16.058C157.429 15.8527 157.307 15.666 157.149 15.498C156.99 15.33 156.789 15.1947 156.547 15.092C156.304 14.98 156.019 14.924 155.693 14.924C155.282 14.924 154.918 15.0313 154.601 15.246C154.283 15.4513 154.036 15.7407 153.859 16.114C153.784 16.2727 153.728 16.4407 153.691 16.618Z\" fill=\"black\" fill-opacity=\"0.66\"/>\n<defs>\n<pattern id=\"pattern0_8746_115054\" patternContentUnits=\"objectBoundingBox\" width=\"1\" height=\"1\">\n<use xlink:href=\"#image0_8746_115054\" transform=\"scale(0.00195312)\"/>\n</pattern>\n<image id=\"image0_8746_115054\" width=\"512\" height=\"512\" preserveAspectRatio=\"none\" xlink:href=\"data:image/png;base64,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\"/>\n</defs>\n</svg>\n";

/***/ }),

/***/ "./style/icons/storage_icon.svg":
/*!**************************************!*\
  !*** ./style/icons/storage_icon.svg ***!
  \**************************************/
/***/ ((module) => {

module.exports = "<svg width=\"18\" height=\"18\" viewBox=\"0 0 18 18\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\">\n<path d=\"M2 13.8V11.1H16.4V13.8H2ZM3.35 13.125H4.7V11.775H3.35V13.125ZM2 5.7V3H16.4V5.7H2ZM3.35 5.025H4.7V3.675H3.35V5.025ZM2 9.75V7.05H16.4V9.75H2ZM3.35 9.075H4.7V7.725H3.35V9.075Z\" fill=\"#616161\" class=\"jp-icon3 jp-icon-selectable\"/>\n</svg>\n";

/***/ })

}]);
//# sourceMappingURL=lib_index_js.7f8f91c83b40890b48e6.js.map