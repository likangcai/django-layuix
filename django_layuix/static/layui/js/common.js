/**
 * 公共JS工具 - django-layuix
 */

// ==================== Token管理 ====================

// 获取存储的token
function getToken() {
    try {
        return sessionStorage.getItem('admin_token') || localStorage.getItem('admin_token') || '';
    } catch(e) {
        return '';
    }
}

// 保存token
function setToken(token) {
    try {
        sessionStorage.setItem('admin_token', token);
        localStorage.setItem('admin_token', token);
    } catch(e) {}
}

// 清除token
function clearToken() {
    try {
        sessionStorage.removeItem('admin_token');
        localStorage.removeItem('admin_token');
    } catch(e) {}
}

// ==================== API请求封装 ====================

function handleLoginExpired(payload, callback) {
    clearToken();
    if (window.LayuiUI && typeof window.LayuiUI.realtime === 'object') {
        window.LayuiUI.realtime.disconnect();
    }
    if (window.layer) {
        window.layer.msg((typeof t === 'function' ? t('login.expired') : '登录已过期，请重新登录'), {icon: 2});
    }
    setTimeout(function() {
        var loginUrl = window.ADMIN_LOGIN_URL || '/admin/login/';
        if (window.top) {
            window.top.location.href = loginUrl;
        } else {
            window.location.href = loginUrl;
        }
    }, 1200);
    if (callback) callback(payload || {code: 401, msg: '未登录'});
}

// 获取layui模块的引用（延迟获取，因为子页面可能在iframe中）
function _getLayui() {
    try {
        if (typeof layui !== 'undefined') {
            return layui;
        }
        if (window.parent && window.parent.layui) {
            return window.parent.layui;
        }
    } catch(e) {}
    return null;
}

// 统一弹窗关闭行为：确保 X、底部取消按钮以及只有单个取消按钮的场景都能关闭。
// layui 模块可能在 common.js 之后异步加载，因此这里做有限次探测。
function patchLayerCloseDefaults() {
    var api = _getLayui();
    if (!api || !api.layer || api.layer.__layuiCloseDefaultsPatched) return false;

    var layer = api.layer;
    var originalOpen = layer.open;
    layer.open = function(options) {
        options = options || {};
        if (options.closeBtn === undefined) options.closeBtn = 1;

        if (Array.isArray(options.btn) && typeof options.yes !== 'function') {
            options.yes = function(index) { layer.close(index); };
        }
        if (Array.isArray(options.btn) && options.btn.length > 1 && typeof options.btn2 !== 'function') {
            options.btn2 = function(index) { layer.close(index); };
        }

        var originalCancel = options.cancel;
        options.cancel = function(index) {
            if (typeof originalCancel === 'function' && originalCancel(index) === false) {
                return false;
            }
            layer.close(index);
        };

        return originalOpen.call(layer, options);
    };
    layer.__layuiCloseDefaultsPatched = true;
    return true;
}

// Layui 2.13.9 新增 form.filterDisabled。默认保持本项目既有行为（disabled 字段参与取值），
// 可通过 LAYUI_CONFIG.form_filter_disabled = true 显式排除 disabled 字段。
function applyLayuiCompatibility() {
    var api = _getLayui();
    if (!api || !api.form || typeof api.form.set !== 'function' || api.form.__layuiCompatPatched) return false;
    var raw = (window.LAYUI_CONFIG || {}).form_filter_disabled;
    var filterDisabled = raw === true || raw === 1 || String(raw).toLowerCase() === 'true';
    api.form.set({filterDisabled: filterDisabled});
    api.form.__layuiCompatPatched = true;
    return true;
}

if (typeof window !== 'undefined') {
    patchLayerCloseDefaults();
    applyLayuiCompatibility();
    var layuiPatchAttempts = 0;
    var layuiPatchTimer = setInterval(function() {
        layuiPatchAttempts++;
        var layerPatched = patchLayerCloseDefaults();
        var formPatched = applyLayuiCompatibility();
        if ((layerPatched && formPatched) || layuiPatchAttempts > 50) clearInterval(layuiPatchTimer);
    }, 100);
}

// layui 的 form 模块没有 off()，这里用标志位保证同一个事件处理器只注册一次。
function bindFormOnce(filter, callback) {
    var api = _getLayui();
    if (!api || !api.form || typeof api.form.on !== 'function') return;
    var key = '__layuiFormBound_' + filter.replace(/[^a-zA-Z0-9]/g, '_');
    if (window[key]) return;
    window[key] = true;
    api.form.on(filter, callback);
}

/**
 * API请求封装
 * @param {string} method - HTTP方法
 * @param {string} url - 请求URL
 * @param {object|null} data - 请求数据
 * @param {function} callback - 回调函数
 * @returns {Promise} 返回Promise对象
 */
function api(method, url, data, callback) {
    var _layui = _getLayui();
    var $ = _layui ? _layui.$ : (window.jQuery || window.$);
    var layer = _layui ? _layui.layer : null;

    var options = {
        method: method,
        url: url,
        dataType: 'json',
        contentType: 'application/json',
        data: data ? JSON.stringify(data) : null,
        beforeSend: function(xhr) {
            // Token认证（优先级更高）
            var token = getToken();
            if (token) {
                xhr.setRequestHeader('Authorization', 'Bearer ' + token);
            } else {
                // CSRF token认证（备选）
                var csrfToken = null;
                var match = document.cookie.match(/csrftoken=([^;]+)/);
                if (match) {
                    csrfToken = match[1];
                } else {
                    var input = document.querySelector('input[name="csrfmiddlewaretoken"]');
                    if (input) csrfToken = input.value;
                }
                if (csrfToken) {
                    xhr.setRequestHeader('X-CSRFToken', csrfToken);
                }
            }
        },
        success: function(res) {
            if (res.code === 401) {
                handleLoginExpired(res, callback);
                return;
            }
            if (res.code === 403) {
                if (layer) layer.msg((typeof t === 'function' ? t('common.noPermission') : '无权限执行此操作'), {icon: 2});
                if (callback) callback(res);
                return;
            }
            if (callback) callback(res);
        },
        error: function(xhr) {
            // 401 由后端直接返回 HTTP 状态码，必须走统一登录过期流程
            if (xhr && xhr.status === 401) {
                var expiredRes = {code: 401, msg: '未登录'};
                try { expiredRes = JSON.parse(xhr.responseText) || expiredRes; } catch (e) {}
                handleLoginExpired(expiredRes, callback);
                return;
            }
            // 尝试解析后端返回的JSON错误信息
            var errMsg = (typeof t === 'function' ? t('common.networkError') : '网络请求失败');
            try {
                var res = JSON.parse(xhr.responseText);
                if (res && res.msg) {
                    errMsg = res.msg;
                }
            } catch(e) {}
            if (layer) {
                layer.msg(errMsg, {icon: 2});
            }
            // 将错误响应也传给callback，让调用方可以处理
            if (callback) {
                try {
                    var res = JSON.parse(xhr.responseText);
                    callback(res);
                } catch(e) {
                    callback({code: xhr.status || 500, msg: errMsg});
                }
            }
        }
    };
    if (data) {
        options.data = JSON.stringify(data);
        options.contentType = 'application/json';
    }
    return $.ajax(options);
}

function getApi(url, callback) { return api('GET', url, null, callback); }
function postApi(url, data, callback) { return api('POST', url, data, callback); }
function putApi(url, data, callback) { return api('PUT', url, data, callback); }
function deleteApi(url, callback) { return api('DELETE', url, null, callback); }

// 获取URL参数
function getQueryParam(name) {
    var reg = new RegExp('(^|&)' + name + '=([^&]*)(&|$)');
    var r = window.location.search.substr(1).match(reg);
    return r ? decodeURIComponent(r[2]) : null;
}

// 获取父页面用户信息
function getParentUser() {
    try {
        if (window.parent && window.parent.currentUser) {
            return window.parent.currentUser;
        }
    } catch(e) {}
    return null;
}

// 在父页面打开Tab
function openParentTab(title, url) {
    try {
        if (window.parent && window.parent.openTab) {
            window.parent.openTab(title, url);
        }
    } catch(e) {}
}

// 子页面继承父页面主题：唯一协议是 data-theme-mode + themeChange{themeMode,theme}
function inheritTheme() {
    var root = document.documentElement;
    try {
        var parentRoot = null;
        try {
            parentRoot = window.parent && window.parent.document && window.parent.document.documentElement;
        } catch(e) {}
        var themeMode = parentRoot ? parentRoot.getAttribute('data-theme-mode') : null;
        var legacyTheme = parentRoot ? parentRoot.getAttribute('data-theme') : null;
        if (!themeMode) {
            themeMode = localStorage.getItem('theme') || 'light';
        }
        if (themeMode !== 'dark' && themeMode !== 'light') {
            themeMode = 'dark';
        }
        root.setAttribute('data-theme-mode', themeMode);
        root.setAttribute('data-theme', legacyTheme || themeMode);
    } catch(e) {
        root.setAttribute('data-theme-mode', 'dark');
        root.setAttribute('data-theme', 'dark');
    }
    if (!window.__layuiThemeListenerBound) {
        window.__layuiThemeListenerBound = true;
        window.addEventListener('message', function(e) {
            if (!e.data || e.data.type !== 'themeChange') return;
            var mode = e.data.themeMode || e.data.theme;
            if (mode !== 'dark' && mode !== 'light') mode = 'dark';
            document.documentElement.setAttribute('data-theme-mode', mode);
            document.documentElement.setAttribute('data-theme', e.data.theme || mode);
        });
    }
}
// 兼容历史页面中直接调用 syncParentTheme() 的写法
window.syncParentTheme = inheritTheme;

// 接收父窗口的语言切换广播，保持 iframe 内文案同步
if (!window.__layuiLangListenerBound) {
    window.__layuiLangListenerBound = true;
    window.addEventListener('message', function(e) {
        if (!e.data || e.data.type !== 'languageChange') return;
        var lang = e.data.lang;
        if (lang !== 'zh-hans' && lang !== 'en') return;
        try {
            if (window.I18N && typeof window.I18N.setLang === 'function') {
                window.I18N.setLang(lang);
            } else if (typeof I18N !== 'undefined' && I18N.setLang) {
                I18N.setLang(lang);
            }
            if (typeof renderI18n === 'function') renderI18n();
            document.querySelectorAll('[data-i18n]').forEach(function(el) {
                var key = el.getAttribute('data-i18n');
                if (key && typeof t === 'function') {
                    var value = t(key);
                    if (value && value !== key) el.textContent = value;
                }
            });
        } catch(err) {}
    });
}

// 防抖
function debounce(fn, delay) {
    var timer = null;
    return function() {
        var context = this, args = arguments;
        clearTimeout(timer);
        timer = setTimeout(function() { fn.apply(context, args); }, delay);
    };
}

// 确认删除
function confirmDelete(msg, callback) {
    var _layui = _getLayui();
    if (_layui && _layui.layer) {
        var message = msg || (typeof t === 'function' ? t('common.confirmDelete') : '确定要删除吗？');
        var title = (typeof t === 'function' ? t('common.confirm') : '提示');
        var btn1 = (typeof t === 'function' ? t('common.confirm') : '确定');
        var btn2 = (typeof t === 'function' ? t('common.cancel') : '取消');
        _layui.layer.confirm(message, {
            icon: 3,
            title: title,
            skin: 'layui-layer-admin',
            btn: [btn1, btn2]
        }, function(index) {
            _layui.layer.close(index);
            if (callback) callback();
        });
    }
}

// 获取问候语
function getGreeting() {
    var lang = (window.I18N && window.I18N.currentLang) || 'zh-hans';
    var h = new Date().getHours();
    if (lang === 'en') {
        if (h < 6) return 'Good Night';
        if (h < 12) return 'Good Morning';
        if (h < 18) return 'Good Afternoon';
        return 'Good Evening';
    }
    if (h < 6) return '凌晨好';
    if (h < 9) return '早上好';
    if (h < 12) return '上午好';
    if (h < 14) return '中午好';
    if (h < 17) return '下午好';
    if (h < 19) return '傍晚好';
    return '晚上好';
}

// 获取当前时间字符串
function getCurrentTime() {
    var now = new Date();
    var y = now.getFullYear();
    var m = String(now.getMonth() + 1).padStart(2, '0');
    var d = String(now.getDate()).padStart(2, '0');
    var h = String(now.getHours()).padStart(2, '0');
    var min = String(now.getMinutes()).padStart(2, '0');
    var s = String(now.getSeconds()).padStart(2, '0');
    return y + '-' + m + '-' + d + ' ' + h + ':' + min + ':' + s;
}

// HTML转义
function escapeHtml(str) {
    if (str === 0 || str === false) str = String(str);
    if (!str) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

/**
 * 渲染layui模板 - 将 {{ t('key') }} 替换为翻译后的文本
 * 解决 layui <script type="text/html"> 模板通过 .html() 获取时 {{ t() }} 不生效的问题
 * @param {string} tplId - 模板script标签的id
 * @param {object} [data] - 额外的模板数据
 * @returns {string} 渲染后的HTML字符串
 */
function renderTpl(tplId, data) {
    var _layui = _getLayui();
    if (!_layui || !_layui.laytpl) {
        // fallback: 直接返回原始HTML并用正则替换 {{ t('key') }}
        var srcEl = document.getElementById(tplId);
        if (!srcEl) return '';
        var html = srcEl.innerHTML;
        html = html.replace(/\{\{\s*t\(['"]([^'"]+)['"]\)\s*\}\}/g, function(match, key) {
            return (typeof t === 'function') ? t(key) : key;
        });
        return html;
    }
    var srcEl = document.getElementById(tplId);
    if (!srcEl) return '';
    var tplHtml = srcEl.innerHTML;
    var render = _layui.laytpl(tplHtml);
    var tplData = Object.assign({t: (typeof t === 'function' ? t : function(k){return k;})}, data || {});
    return render.render(tplData);
}

// ==================== 通用列表 / 弹窗组件 ====================

var STANDARD_TABLE_PAGE = {
    limit: 10,
    limits: [10, 30, 50, 100],
    groups: 5,
    layout: ['count', 'prev', 'page', 'next', 'skip', 'limit']
};

function getStandardTablePage(overrides) {
    if (overrides === false) return false;
    return Object.assign({}, STANDARD_TABLE_PAGE, overrides === true ? {} : (overrides || {}));
}

/**
 * 统一表格渲染：默认高度、斑马纹、无内置工具栏、统一分页配置。
 * 特殊页面可传 page:false 或覆盖任意 table 配置。
 */
function renderStandardTable(options) {
    var api = _getLayui();
    if (!api || !api.table) return null;
    var settings = Object.assign({}, options || {});
    var page = settings.page;
    delete settings.page;
    settings.defaultToolbar = settings.defaultToolbar || [];
    settings.escape = settings.escape !== false;
    settings.height = settings.height || 'full-220';
    settings.even = settings.even !== false;
    settings.page = getStandardTablePage(page === undefined ? true : page);
    return api.table.render(settings);
}

/**
 * 统一表单弹窗：模板、表单回填、render、保存/取消按钮与精确关闭。
 */
function openStandardDialog(options) {
    var api = _getLayui();
    if (!api || !api.layer) return null;
    var layer = api.layer;
    var form = api.form;
    var settings = Object.assign({}, options || {});
    var content = settings.content || '';
    if (settings.tplId) {
        content = renderTpl(settings.tplId, settings.tplData);
    }
    var originalSuccess = settings.success;
    var originalCancel = settings.cancel;
    var uiText = function(key, fallback) {
        return typeof t === 'function' ? t(key) : fallback;
    };
    var config = Object.assign({}, settings, {
        type: settings.type || 1,
        title: settings.title || '',
        area: settings.area || ['620px', '520px'],
        maxHeight: settings.maxHeight || '80vh',
        skin: settings.skin || 'layui-layer-admin',
        closeBtn: settings.closeBtn === undefined ? 1 : settings.closeBtn,
        btnAlign: settings.btnAlign || 'r',
        content: content,
        success: function(layero, idx) {
            if (form && settings.filter && settings.data) {
                form.val(settings.filter, settings.data);
            }
            if (form && settings.filter) {
                form.render(null, settings.filter);
            }
            if (settings.maxHeight) {
                var maxHeight = settings.maxHeight;
                layero.find('.layui-layer-content').css({
                    maxHeight: typeof maxHeight === 'number' ? maxHeight + 'px' : maxHeight,
                    overflow: 'auto'
                });
            }
            if (typeof renderI18n === 'function') renderI18n();
            if (typeof originalSuccess === 'function') originalSuccess(layero, idx);
        },
        cancel: function(idx) {
            if (typeof originalCancel === 'function' && originalCancel(idx) === false) return false;
            layer.close(idx);
        }
    });

    if (settings.standard) {
        config.btn = settings.btn || [uiText('common.save', 'Save'), uiText('common.cancel', 'Cancel')];
        config.yes = settings.yes || function(idx, layero) {
            if (typeof settings.onSubmit === 'function' && settings.onSubmit(layero, idx) === false) return;
            layer.close(idx);
        };
        config.btn2 = settings.btn2 || function(idx, layero) {
            if (typeof settings.onCancel === 'function' && settings.onCancel(layero, idx) === false) return false;
            layer.close(idx);
        };
    } else if (settings.onSubmit && !config.yes) {
        config.yes = function(idx, layero) {
            if (settings.onSubmit(layero, idx) === false) return;
            layer.close(idx);
        };
    }
    if (settings.onCancel && !config.btn2) {
        config.btn2 = function(idx, layero) {
            if (settings.onCancel(layero, idx) === false) return false;
            layer.close(idx);
        };
    }
    return layer.open(config);
}

/**
 * 虚拟滚动表格：支持本地数据、服务端分页混合加载与列宽持久化。
 * cols 使用与 Layui table 相同的 {field,title,width,templet} 结构。
 */
function renderVirtualTable(options) {
    var api = _getLayui();
    var $ = api ? api.$ : (window.jQuery || window.$);
    if (!$ || !options || !options.elem) return null;

    var settings = Object.assign({
        rowHeight: 38,
        buffer: 8,
        height: 420,
        data: [],
        cols: [],
        pageMode: 'client',
        page: 1,
        pageSize: 100,
        total: 0,
        request: {pageName: 'page', limitName: 'page_size'},
        tableKey: '',
        columnsConfigurable: false
    }, options);
    var allColumns = (settings.cols && settings.cols[0] ? settings.cols[0] : (settings.cols || [])).slice();
    allColumns.forEach(function(col, index) {
        if (!col.field && !col.__layuixKey) col.__layuixKey = '__col_' + index;
    });
    var columns = allColumns.slice();
    var storageKey = settings.tableKey ? 'layuix:virtual-table:' + settings.tableKey + ':columns' : '';
    var columnConfig = {order: [], hidden: [], widths: {}};

    function columnKey(col) {
        return col.field || col.__layuixKey;
    }

    function normalizeWidth(value) {
        if (typeof value === 'number' && value >= 60 && value <= 600) return value;
        var raw = String(value || '').trim();
        if (/^\d{2,4}px$/.test(raw)) raw = raw.slice(0, -2);
        if (/^\d{2,4}$/.test(raw)) {
            var width = parseInt(raw, 10);
            return width >= 60 && width <= 600 ? width : null;
        }
        return null;
    }

    function readColumnConfig() {
        if (!storageKey) return {order: [], hidden: [], widths: {}};
        var raw;
        try {
            raw = JSON.parse(localStorage.getItem(storageKey) || 'null');
        } catch (e) {
            raw = null;
        }
        if (!raw) return {order: [], hidden: [], widths: {}};
        if (raw.order || raw.hidden || raw.widths) {
            return {
                order: Array.isArray(raw.order) ? raw.order.filter(function(item) {
                    return typeof item === 'string';
                }) : [],
                hidden: Array.isArray(raw.hidden) ? raw.hidden.filter(function(item) {
                    return typeof item === 'string';
                }) : [],
                widths: raw.widths && typeof raw.widths === 'object' ? raw.widths : {}
            };
        }
        // Compatible with the 1.4.6 index-width storage format.
        var widths = {};
        Object.keys(raw).forEach(function(index) {
            var col = allColumns[parseInt(index, 10)];
            if (col && normalizeWidth(raw[index])) widths[columnKey(col)] = normalizeWidth(raw[index]);
        });
        return {order: [], hidden: [], widths: widths};
    }
    columnConfig = readColumnConfig();

    function applyColumnConfig() {
        var originalKeys = allColumns.map(columnKey);
        var orderedKeys = (columnConfig.order || []).filter(function(key) {
            return originalKeys.indexOf(key) > -1;
        });
        originalKeys.forEach(function(key) {
            if (orderedKeys.indexOf(key) < 0) orderedKeys.push(key);
        });
        var byKey = {};
        allColumns.forEach(function(col, index) { byKey[columnKey(col)] = col; });
        allColumns = orderedKeys.map(function(key) { return byKey[key]; });

        var hidden = new Set((columnConfig.hidden || []).filter(function(key) {
            return originalKeys.indexOf(key) > -1;
        }));
        columns = allColumns.filter(function(col, index) {
            return !hidden.has(columnKey(col));
        });
        if (!columns.length) {
            hidden.clear();
            columns = allColumns.slice();
        }
        allColumns.forEach(function(col, index) {
            var width = normalizeWidth((columnConfig.widths || {})[columnKey(col)]);
            if (width) col.width = width;
        });
    }
    applyColumnConfig();

    var rows = settings.data || [];
    var total = parseInt(settings.total, 10) || rows.length;
    var currentPage = parseInt(settings.page, 10) || 1;
    var loading = false;
    var loadError = null;
    var loaded = false;
    var exhausted = false;
    var lastFailedRequest = null;
    var requestId = 0;
    var root = $('<div class="layuix-virtual-table"></div>');
    var head = $('<div class="layuix-virtual-head"></div>');
    var body = $('<div class="layuix-virtual-body"></div>');
    var topSpacer = $('<div class="layuix-virtual-spacer"></div>');
    var list = $('<div class="layuix-virtual-rows"></div>');
    var bottomSpacer = $('<div class="layuix-virtual-spacer"></div>');
    var state = $('<div class="layuix-virtual-state"></div>');

    function widthStyle(col) {
        if (!col.width) return 'flex:1;';
        return 'width:' + (typeof col.width === 'number' ? col.width + 'px' : col.width) + ';flex:0 0 auto;';
    }

    function renderHead() {
        head.empty();
        columns.forEach(function(col, index) {
            var cell = $('<div class="layuix-virtual-cell" style="' + widthStyle(col) + '">'
                + escapeHtml(col.title || '') + '</div>');
            if (storageKey) {
                cell.append('<span class="layuix-virtual-resizer" data-key="' + escapeHtml(columnKey(col)) + '"></span>');
            }
            head.append(cell);
        });
        if (storageKey && settings.columnsConfigurable) {
            head.append('<div class="layuix-virtual-cell layuix-virtual-column-action" title="'
                + escapeHtml(typeof t === 'function' ? t('virtual.columnSettings') : 'Columns')
                + '"><button type="button" class="layuix-virtual-column-settings"><i class="layui-icon layui-icon-set"></i></button></div>');
        }
    }

    function persistWidths() {
        if (!storageKey) return;
        var visibleKeys = {};
        columns.forEach(function(col, index) { visibleKeys[columnKey(col)] = true; });
        columnConfig.order = allColumns.map(function(col, index) { return columnKey(col); });
        columnConfig.hidden = allColumns
            .filter(function(col, index) { return !visibleKeys[columnKey(col)]; })
            .map(function(col, index) { return columnKey(col); });
        columnConfig.widths = {};
        allColumns.forEach(function(col, index) {
            if (col.width) columnConfig.widths[columnKey(col)] = col.width;
        });
        try { localStorage.setItem(storageKey, JSON.stringify(columnConfig)); } catch (e) {}
    }

    function showState(type, message) {
        if (!type) {
            state.hide().empty();
            return;
        }
        var icon = type === 'loading' ? 'layui-icon-loading-1 layui-anim layui-anim-rotate layui-anim-loop' : 'layui-icon-close-fill';
        state.removeClass('is-loading is-error').addClass('is-' + type)
            .html('<i class="layui-icon ' + icon + '"></i><span>' + escapeHtml(message || '') + '</span>'
                + (type === 'error' ? '<button type="button" class="layui-btn layui-btn-xs layui-btn-primary">'
                    + escapeHtml(typeof t === 'function' ? t('common.retry') : 'Retry') + '</button>' : ''))
            .show();
        if (type === 'error') {
            state.find('button').on('click', function() { instance.retry(); });
        }
    }

    function safeTemplateHtml(value) {
        if (value === null || value === undefined) return '';
        return value && value.__html ? String(value.__html) : escapeHtml(value);
    }

    function cellHtml(row, col, index) {
        if (typeof col.templet === 'function') {
            return safeTemplateHtml(col.templet(row[col.field], row, index));
        }
        if (typeof col.templet === 'string' && api && api.laytpl) {
            var tpl = col.templet.charAt(0) === '#'
                ? ($(col.templet).html() || '')
                : col.templet;
            if (tpl) return safeTemplateHtml(api.laytpl(tpl).render(row));
        }
        var value = row[col.field];
        return escapeHtml(value === null || value === undefined ? '' : value);
    }

    function renderWindow() {
        var rowHeight = Math.max(1, parseInt(settings.rowHeight, 10) || 38);
        var viewport = body.innerHeight() || rowHeight * 10;
        var scrollTop = body.scrollTop();
        var start = Math.max(0, Math.floor(scrollTop / rowHeight) - (settings.buffer || 0));
        var end = Math.min(
            rows.length,
            Math.ceil((scrollTop + viewport) / rowHeight) + (settings.buffer || 0)
        );
        topSpacer.css('height', (start * rowHeight) + 'px');
        bottomSpacer.css('height', ((rows.length - end) * rowHeight) + 'px');
        var html = [];
        for (var i = start; i < end; i++) {
            var cells = columns.map(function(col) {
                return '<div class="layuix-virtual-cell" style="' + widthStyle(col) + '">'
                    + cellHtml(rows[i], col, i) + '</div>';
            }).join('');
            if (storageKey && settings.columnsConfigurable) {
                cells += '<div class="layuix-virtual-cell layuix-virtual-column-action"></div>';
            }
            html.push('<div class="layuix-virtual-row" style="height:' + rowHeight + 'px">' + cells + '</div>');
        }
        list.html(html.join(''));
        if (settings.pageMode === 'server' && loaded && !loading && !loadError && !exhausted
            && rows.length > 0 && rows.length < total
            && scrollTop + viewport >= rows.length * rowHeight - rowHeight * 2) {
            instance.loadPage(currentPage + 1, true);
        }
    }

    function applyPayload(payload, append) {
        var parsed = typeof settings.parseData === 'function'
            ? settings.parseData(payload) : payload;
        var batch = (parsed && parsed.data) || [];
        if (parsed && (parsed.count !== undefined || parsed.total !== undefined)) {
            total = parseInt(parsed.count !== undefined ? parsed.count : parsed.total, 10) || 0;
        }
        rows = append ? rows.concat(batch) : batch;
        currentPage = append ? currentPage + 1 : (parseInt(settings.page, 10) || 1);
        loaded = true;
        if (!batch.length) exhausted = true;
        showState(null);
        renderWindow();
        if (typeof settings.success === 'function') settings.success(rows, payload);
    }

    var instance = {
        elem: root,
        rows: function() { return rows; },
        state: function() { return {page: currentPage, total: total, loaded: rows.length, loading: loading, error: loadError}; },
        refresh: renderWindow,
        setData: function(data, meta) {
            requestId++;
            loading = false;
            rows = data || [];
            total = meta && meta.total !== undefined ? parseInt(meta.total, 10) || 0 : rows.length;
            currentPage = meta && meta.page ? parseInt(meta.page, 10) || 1 : 1;
            loaded = true;
            exhausted = false;
            loadError = null;
            lastFailedRequest = null;
            body.scrollTop(0);
            showState(null);
            renderWindow();
        },
        loadPage: function(page, append) {
            if (!settings.url || typeof fetch !== 'function' || loading) return;
            var currentRequest = ++requestId;
            loading = true;
            loadError = null;
            if (!append) exhausted = false;
            lastFailedRequest = {page: page, append: !!append};
            showState('loading', typeof t === 'function' ? t('common.loading') : 'Loading...');
            var url = settings.url;
            var request = settings.request || {};
            var sep = url.indexOf('?') > -1 ? '&' : '?';
            url += sep + (request.pageName || 'page') + '=' + encodeURIComponent(page)
                + '&' + (request.limitName || 'page_size') + '=' + encodeURIComponent(settings.pageSize);
            var headers = Object.assign({}, settings.headers || {});
            var token = getToken();
            if (token && !headers.Authorization) headers.Authorization = 'Bearer ' + token;
            fetch(url, {credentials: 'include', headers: headers})
                .then(function(response) {
                    if (response.status === 401) handleLoginExpired({code: 401}, null);
                    if (!response.ok) throw new Error((typeof t === 'function' ? t('common.loadFailed') : 'Load failed') + ' (' + response.status + ')');
                    return response.json();
                })
                .then(function(payload) {
                    if (currentRequest !== requestId) return;
                    if (payload && payload.code !== undefined && payload.code !== 0 && payload.code !== 200) {
                        throw new Error(payload.msg || 'Request failed');
                    }
                    applyPayload(payload, !!append);
                })
                .catch(function(error) {
                    if (currentRequest !== requestId) return;
                    loadError = error;
                    showState('error', (error && error.message) || (typeof t === 'function' ? t('common.loadFailed') : 'Load failed'));
                    if (typeof settings.error === 'function') settings.error(error);
                })
                .finally(function() { if (currentRequest === requestId) loading = false; });
        },
        retry: function() {
            if (!lastFailedRequest) return;
            var target = lastFailedRequest;
            loadError = null;
            instance.loadPage(target.page, target.append);
        },
        allColumns: function() { return allColumns.slice(); },
        columns: function() { return columns.slice(); },
        setColumnConfig: function(nextConfig) {
            columnConfig.order = Array.isArray(nextConfig && nextConfig.order) ? nextConfig.order : columnConfig.order;
            columnConfig.hidden = Array.isArray(nextConfig && nextConfig.hidden) ? nextConfig.hidden : columnConfig.hidden;
            if (nextConfig && nextConfig.widths && typeof nextConfig.widths === 'object') {
                columnConfig.widths = Object.assign({}, columnConfig.widths, nextConfig.widths);
            }
            applyColumnConfig();
            persistWidths();
            renderHead();
            renderWindow();
        },
        openColumnSettings: function() { if (storageKey) openColumnSettings(); }
    };

    body.css('height', typeof settings.height === 'number' ? settings.height + 'px' : settings.height);
    renderHead();
    body.append(topSpacer).append(list).append(bottomSpacer);
    root.append(head).append(body).append(state);
    $(settings.elem).html(root);

    function openColumnSettings() {
        var text = function(key, fallback) {
            return typeof t === 'function' ? t(key) : fallback;
        };
        var rows = allColumns.map(function(col, index) {
            var key = columnKey(col);
            var visible = columns.indexOf(col) > -1;
            return '<div class="layuix-column-config-item" data-key="' + escapeHtml(key) + '">'
                + '<label><input type="checkbox"' + (visible ? ' checked' : '') + '> ' + escapeHtml(col.title || key) + '</label>'
                + '<span><button type="button" class="layui-btn layui-btn-xs layui-btn-primary column-move-up"><i class="layui-icon layui-icon-up"></i></button>'
                + '<button type="button" class="layui-btn layui-btn-xs layui-btn-primary column-move-down"><i class="layui-icon layui-icon-down"></i></button></span>'
                + '</div>';
        }).join('');
        LayuiUI.dialog({
            title: text('virtual.columnSettings', 'Column settings'),
            area: ['360px', 'auto'],
            btn: [text('common.save', 'Save'), text('common.cancel', 'Cancel')],
            content: '<div class="layuix-column-config">' + rows + '</div>',
            success: function(dialogLayero) {
                var $layero = $(dialogLayero);
                $layero.off('click.layuixColumnMove').on('click.layuixColumnMove', '.column-move-up, .column-move-down', function() {
                    var $item = $(this).closest('.layuix-column-config-item');
                    var $target = $(this).hasClass('column-move-up') ? $item.prev() : $item.next();
                    if ($target.length) {
                        $(this).hasClass('column-move-up') ? $item.insertBefore($target) : $item.insertAfter($target);
                    }
                });
            },
            yes: function(index, layero) {
                var orderedKeys = [];
                var visibleKeys = [];
                $(layero).find('.layuix-column-config-item').each(function() {
                    var key = $(this).data('key');
                    orderedKeys.push(key);
                    if ($(this).find('input[type="checkbox"]').first().prop('checked')) visibleKeys.push(key);
                });
                var hidden = orderedKeys.filter(function(key) { return visibleKeys.indexOf(key) < 0; });
                if (!visibleKeys.length) {
                    if (window.layer) window.layer.msg(typeof t === 'function' ? t('virtual.keepOneColumn') : 'Keep at least one column visible', {icon: 2});
                    return false;
                }
                instance.setColumnConfig({order: orderedKeys, hidden: hidden});
                layer.close(index);
            }
        });
    }

    body.off('scroll.layuixVirtual').on('scroll.layuixVirtual', renderWindow);
    head.off('mousedown.layuixVirtualResize').on('mousedown.layuixVirtualResize', '.layuix-virtual-resizer', function(e) {
        if (!storageKey) return;
        e.preventDefault();
        e.stopPropagation();
        var handle = $(this);
        var key = String(handle.data('key'));
        var colIndex = allColumns.findIndex(function(col, index) { return columnKey(col) === key; });
        if (colIndex < 0) return;
        var startX = e.clientX;
        var startWidth = parseInt(allColumns[colIndex].width, 10) || 120;
        $(document).on('mousemove.layuixVirtualResize', function(moveEvent) {
            allColumns[colIndex].width = Math.min(600, Math.max(60, startWidth + moveEvent.clientX - startX));
            renderHead();
            renderWindow();
        });
        $(document).one('mouseup.layuixVirtualResize', function() {
            $(document).off('mousemove.layuixVirtualResize');
            persistWidths();
            renderHead();
        });
    });
    head.off('click.layuixColumnSettings').on('click.layuixColumnSettings', '.layuix-virtual-column-settings', openColumnSettings);
    renderWindow();

    if (settings.url && typeof fetch === 'function') {
        instance.loadPage(currentPage, false);
    }
    return instance;
}

var PAGE_PERMISSION_MAP = {
    '/static/layui/pages/dashboard.html': 'dashboard:view',
    '/static/layui/pages/menu.html': 'menu:view',
    '/static/layui/pages/role.html': 'role:view',
    '/static/layui/pages/user.html': 'user:view',
    '/static/layui/pages/log.html': 'log:view',
    '/static/layui/pages/config.html': 'config:view',
    '/static/layui/pages/dict.html': 'dict:view',
    '/static/layui/pages/permission.html': 'permission:view',
    '/static/layui/pages/dept.html': 'dept:view',
    '/static/layui/pages/position.html': 'position:view',
    '/static/layui/pages/region.html': 'region:view',
    '/static/layui/pages/member-level.html': 'member_level:view',
    '/static/layui/pages/ai-config.html': 'ai_config:view',
    '/static/layui/pages/server.html': 'server:view',
    '/static/layui/pages/abac.html': 'abac:view',
    '/static/layui/pages/scope.html': 'scope:view',
    '/static/layui/pages/constraints.html': 'constraint:view',
    '/static/layui/pages/profile.html': 'profile:view',
    '/static/layui/pages/frontend.html': 'frontend:view',
    '/static/permission_demo/pages/order.html': 'permission_demo:view',
    '/static/store/pages/product.html': 'product:view',
    '/static/store/pages/category.html': 'category:view',
    '/static/store/pages/order.html': 'store_order:view'
};

function currentUserPermissions() {
    var root = window.parent && window.parent !== window ? window.parent : window;
    var user = root.currentUser || window.currentUser || {};
    return user.permissions || [];
}

// 等待当前用户信息就绪后再渲染依赖权限的表格，避免工具栏按空权限渲染
function ensureCurrentUser(callback) {
    var root = window.parent && window.parent !== window ? window.parent : window;
    var user = root.currentUser || window.currentUser;
    if (user && user.permissions) {
        callback(user);
        return;
    }
    if (typeof fetch !== 'function') {
        callback({});
        return;
    }
    fetch('/admin/api/rbac/userinfo/', {credentials: 'same-origin'})
        .then(function(response) { return response.ok ? response.json() : {code: 401}; })
        .then(function(res) {
            var data = res && res.code === 200 ? res.data : {};
            root.currentUser = data;
            window.currentUser = data;
            callback(data);
        })
        .catch(function() { callback({}); });
}

function requiredPagePermission(path) {
    var clean = String(path || location.pathname).split('?')[0].split('#')[0];
    var map = PAGE_PERMISSION_MAP;
    var root = window.parent && window.parent !== window ? window.parent : window;
    if (root.currentUser && root.currentUser.page_permissions) {
        map = root.currentUser.page_permissions;
    }
    if (map[clean]) return map[clean];
    var file = clean.split('/').pop();
    for (var key in map) {
        if (key.split('/').pop() === file) return map[key];
    }
    return '';
}

function enforcePagePermission() {
    var path = location.pathname;
    if (path.indexOf('/static/') !== 0) return true;
    var publicPages = ['/static/layui/pages/login.html', '/static/layui/pages/register.html', '/static/layui/pages/404.html'];
    if (publicPages.indexOf(path) > -1) return true;
    var required = requiredPagePermission(path);
    if (!required) {
        deny();
        return false;
    }

    function deny() {
        document.body.innerHTML = '<div class="layuix-page-denied"><i class="layui-icon layui-icon-close-fill"></i><h2>'
            + escapeHtml((typeof t === 'function' ? t('common.noPermission') : '无权限访问'))
            + '</h2><p>' + escapeHtml(required) + '</p></div>';
    }

    function check(user) {
        if (user) {
            try {
                (root === window ? window : root).currentUser = user;
            } catch (e) {}
        }
        if (user && (user.is_superuser || (user.permissions || []).indexOf(required) > -1)) return true;
        deny();
        return false;
    }

    var root = window.parent && window.parent !== window ? window.parent : window;
    var user = root.currentUser || window.currentUser;
    if (user && user.permissions) return check(user);
    if (typeof fetch !== 'function') { deny(); return false; }
    fetch('/admin/api/rbac/userinfo/', {credentials: 'same-origin'})
        .then(function(response) { return response.ok ? response.json() : {code: 401}; })
        .then(function(res) { check(res && res.code === 200 ? res.data : null); })
        .catch(function() { deny(); });
    return true;
}

window.LayuiUI = {
    standardPage: getStandardTablePage,
    table: renderStandardTable,
    virtualTable: renderVirtualTable,
    dialog: openStandardDialog,
    enforcePagePermission: enforcePagePermission,
    requiredPagePermission: requiredPagePermission,
    ensureCurrentUser: ensureCurrentUser
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', enforcePagePermission);
} else {
    enforcePagePermission();
}

/**
 * 渲染页面中所有 {{ t(...) }} 占位符。
 * 不使用 eval：仅解析字符串字面量、t() 调用、参数数组、+ 拼接与 || 默认值。
 */
function renderI18n() {
    if (typeof I18N !== 'undefined' && typeof I18N.getLang === 'function') {
        I18N.getLang();
    }
    if (typeof t !== 'function') return;

    function splitTopLevel(input, delimiter) {
        var parts = [];
        var buffer = '';
        var quote = null;
        var depth = 0;
        for (var i = 0; i < input.length; i++) {
            var ch = input[i];
            if (quote) {
                buffer += ch;
                if (ch === quote && input[i - 1] !== '\\') quote = null;
                continue;
            }
            if (ch === '"' || ch === "'") {
                quote = ch;
                buffer += ch;
                continue;
            }
            if (ch === '(' || ch === '[' || ch === '{') {
                depth++;
                buffer += ch;
                continue;
            }
            if (ch === ')' || ch === ']' || ch === '}') {
                depth--;
                buffer += ch;
                continue;
            }
            if (depth === 0 && input.substr(i, delimiter.length) === delimiter) {
                parts.push(buffer);
                buffer = '';
                i += delimiter.length - 1;
                continue;
            }
            buffer += ch;
        }
        parts.push(buffer);
        return parts;
    }

    function parseLiteral(value) {
        var text = String(value).trim();
        var match = /^(['"])([\s\S]*)\1$/.exec(text);
        if (!match) return null;
        return match[2].replace(/\\(['"\\])/g, '$1');
    }

    function evaluate(expr) {
        var text = String(expr).trim();
        if (!text) return {value: text, key: null};

        var orParts = splitTopLevel(text, '||');
        if (orParts.length > 1) {
            var left = evaluate(orParts[0]);
            if (left.value !== '' && left.value !== left.key) return left;
            return evaluate(orParts.slice(1).join('||'));
        }

        var plusParts = splitTopLevel(text, '+');
        if (plusParts.length > 1) {
            return {
                value: plusParts.map(function(part) { return evaluate(part).value; }).join(''),
                key: null
            };
        }

        var callMatch = /^t\s*\(/.exec(text);
        if (callMatch && text.charAt(text.length - 1) === ')') {
            var inner = text.slice(callMatch[0].length, -1);
            var args = [];
            var callParts = splitTopLevel(inner, ',');
            var key = parseLiteral(callParts[0]);
            if (key !== null) {
                if (callParts.length > 1) {
                    var rawArgs = callParts.slice(1).join(',').trim();
                    if (rawArgs.charAt(0) === '[' && rawArgs.charAt(rawArgs.length - 1) === ']') {
                        var argText = rawArgs.slice(1, -1).trim();
                        args = argText ? splitTopLevel(argText, ',').map(function(item) {
                            return evaluate(item).value;
                        }) : [];
                    } else {
                        args = [evaluate(rawArgs).value];
                    }
                }
                return {value: t(key, args), key: key};
            }
        }

        var literal = parseLiteral(text);
        if (literal !== null) return {value: literal, key: null};
        return {value: text, key: null};
    }

    function translateText(value) {
        if (typeof value !== 'string' || value.indexOf('{{') === -1) return value;
        return value.replace(/\{\{([\s\S]*?)\}\}/g, function(match, expr) {
            if (!/^\s*t\s*\(/.test(expr)) return match;
            return evaluate(expr).value;
        });
    }

    var translatableAttrs = {
        placeholder: true, title: true, alt: true,
        'aria-label': true, 'lay-reqtext': true, 'lay-text': true,
        'data-title': true, 'data-content': true, 'data-tips': true
    };

    // 只替换文本节点和常用属性，不重写 body.innerHTML，避免销毁已绑定的事件与组件状态
    function walk(node) {
        if (!node) return;
        if (node.nodeType === 3) {
            var text = translateText(node.nodeValue);
            if (text !== node.nodeValue) node.nodeValue = text;
            return;
        }
        if (node.nodeType !== 1) return;
        var attrs = node.attributes;
        for (var i = 0; i < attrs.length; i++) {
            var attr = attrs[i];
            if (translatableAttrs[attr.name] || attr.name.indexOf('data-i18n') === 0) {
                var translated = translateText(attr.value);
                if (translated !== attr.value) attr.value = translated;
            }
        }
        var i18nKey = node.getAttribute('data-i18n');
        if (i18nKey && typeof t === 'function') {
            var translated = t(i18nKey);
            if (translated && translated !== i18nKey && node.textContent !== translated) {
                node.textContent = translated;
            }
        }
        ['placeholder', 'title'].forEach(function (attrName) {
            var key = node.getAttribute('data-i18n-' + attrName);
            if (!key || typeof t !== 'function') return;
            var value = t(key);
            if (value && value !== key) node.setAttribute(attrName, value);
        });

        for (var child = node.firstChild; child; child = child.nextSibling) {
            walk(child);
        }
    }
    walk(document.body);
}

/**
 * SSE (Server-Sent Events) 连接管理器
 * 支持Token认证，自动重连，降级到轮询
 */
var SSEManager = {
    evtSource: null,
    pollingTimer: null,
    isPolling: false,
    
    /**
     * 建立SSE连接
     * @param {string} url - SSE接口URL
     * @param {function} onMessage - 消息回调 function(data)
     * @param {function} onError - 错误回调 function(error)
     */
    connect: function(url, onMessage, onError) {
        var self = this;
        self.disconnect();

        function open(ticket) {
            var sseUrl = url;
            if (ticket) {
                sseUrl += (url.indexOf('?') > -1 ? '&' : '?') + 'stream_ticket=' + encodeURIComponent(ticket);
            }
            try {
                self.evtSource = new EventSource(sseUrl);
                self.evtSource.onmessage = function(e) {
                    try {
                        var res = JSON.parse(e.data);
                        if (res.code === 200 && res.data) {
                            onMessage(res.data);
                        } else if (res.code === 401) {
                            self.disconnect();
                            self.startPolling(url, onMessage);
                        }
                    } catch(err) {
                        console.error('SSE消息解析错误:', err);
                    }
                };
                self.evtSource.onerror = function(e) {
                    if (self.evtSource) {
                        self.evtSource.close();
                        self.evtSource = null;
                    }
                    if (!self.isPolling) self.startPolling(url, onMessage);
                    if (onError) onError(e);
                };
            } catch(err) {
                self.startPolling(url, onMessage);
            }
        }

        if (typeof getApi === 'function') {
            getApi('/admin/api/rbac/system/info/stream-ticket/', function(res) {
                open(res && res.code === 200 && res.data ? res.data.ticket : '');
            });
        } else {
            open('');
        }
    },
    
    /**
     * 启动轮询模式（降级方案）
     */
    startPolling: function(url, onMessage) {
        var self = this;
        if (self.isPolling) return;
        
        self.isPolling = true;
        console.log('🔄 启动5秒轮询模式');
        
        // 立即执行一次
        self.pollOnce(url, onMessage);
        
        // 每5秒执行一次
        self.pollingTimer = setInterval(function() {
            self.pollOnce(url, onMessage);
        }, 5000);
    },
    
    /**
     * 执行一次轮询
     */
    pollOnce: function(url, onMessage) {
        var token = getToken();
        var headers = {};
        
        if (token) {
            headers['Authorization'] = 'Bearer ' + token;
        }
        
        var _layui = _getLayui();
        var $ = _layui ? _layui.$ : (window.jQuery || window.$);
        if (!$ || !$.ajax) {
            console.error('轮询失败：未找到 ajax 实现');
            return;
        }
        $.ajax({
            url: url,
            method: 'GET',
            headers: headers,
            success: function(res) {
                if (res.code === 200 && res.data) {
                    onMessage(res.data);
                }
            },
            error: function(xhr) {
                console.error('轮询请求失败:', xhr.status);
                if (xhr.status === 401) {
                    console.error('认证失败，请重新登录');
                }
            }
        });
    },
    
    /**
     * 断开连接
     */
    disconnect: function() {
        var self = this;
        
        // 断开SSE
        if (self.evtSource) {
            self.evtSource.close();
            self.evtSource = null;
        }
        
        // 停止轮询
        if (self.pollingTimer) {
            clearInterval(self.pollingTimer);
            self.pollingTimer = null;
        }
        
        self.isPolling = false;
        console.log('🔌 SSE/轮询连接已断开');
    },
    
    /**
     * 获取当前连接状态
     */
    getStatus: function() {
        if (this.isPolling) return 'polling';
        if (this.evtSource) return 'sse';
        return 'disconnected';
    }
};

window.LayuiUI.realtime = SSEManager;
