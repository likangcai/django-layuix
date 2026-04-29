/**
 * 公共JS工具 - django-layui
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
                if (layer) layer.msg((typeof t === 'function' ? t('login.expired') : '登录已过期，请重新登录'), {icon: 2});
                setTimeout(function() {
                    // BUG-35 FIX: 使用动态 admin 登录路径而非硬编码 /login/
                    var loginUrl = (window.ADMIN_LOGIN_URL || '/admin/login/');
                    if (window.top) {
                        window.top.location.href = loginUrl;
                    } else {
                        window.location.href = loginUrl;
                    }
                }, 1500);
                if (callback) callback(res);
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

// 子页面继承父页面主题
function inheritTheme() {
    try {
        if (window.parent && window.parent.currentTheme) {
            document.documentElement.setAttribute('data-theme', window.parent.currentTheme);
        }
    } catch(e) {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
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
    if (!str) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
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

/**
 * 渲染页面中所有 {{ t('key') }} 占位符
 * 解决静态HTML文件中 {{ t('...') }} 不会被模板引擎处理的问题
 * 在子页面加载 i18n.js 后调用即可
 *
 * 支持的语法：
 *   {{ t('key') }}           → 纯文本替换
 *   {{ t('key', [arg1]) }}   → 带参数的翻译
 *   {{ t('key') || '默认' }}  → 带默认值的翻译
 */
function renderI18n() {
    if (typeof t !== 'function') return;

    // 匹配 {{ t('key') }}, {{ t("key") }}, {{ t('key', [...]) }}, {{ t('key') || 'default' }}
    var regex = /\{\{\s*t\(\s*(['"])([^'"]+)\1\s*(?:,\s*\[([^\]]*)\]\s*)?\)\s*(?:\|\|\s*(['"])([^'"]*)\4)?\s*\}\}/g;

    document.body.innerHTML = document.body.innerHTML.replace(regex, function(match, q1, key, args, q2, fallback) {
        var result;
        if (args) {
            try {
                var argsArr = eval('[' + args + ']');
                result = t(key, argsArr);
            } catch(e) {
                result = t(key);
            }
        } else {
            result = t(key);
        }
        // 如果翻译结果等于key（未找到翻译），使用fallback
        if (result === key && fallback) return fallback;
        return result;
    });
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
        self.disconnect(); // 先断开旧连接
        
        var token = getToken();
        var sseUrl = url;
        
        // 如果有token，添加到URL参数
        if (token) {
            sseUrl += (url.indexOf('?') > -1 ? '&' : '?') + 'token=' + encodeURIComponent(token);
        }
        
        try {
            console.log(' 正在建立SSE连接:', sseUrl);
            self.evtSource = new EventSource(sseUrl);
            
            self.evtSource.onmessage = function(e) {
                try {
                    var res = JSON.parse(e.data);
                    if (res.code === 200 && res.data) {
                        onMessage(res.data);
                    } else if (res.code === 401) {
                        console.error('SSE认证失败，切换为轮询模式');
                        self.disconnect();
                        self.startPolling(url, onMessage);
                    }
                } catch(err) {
                    console.error('SSE消息解析错误:', err);
                }
            };
            
            self.evtSource.onerror = function(e) {
                console.error('SSE连接错误:', e);
                if (self.evtSource) {
                    self.evtSource.close();
                    self.evtSource = null;
                }
                
                // SSE连接失败，降级到轮询
                if (!self.isPolling) {
                    console.warn('️ SSE不可用，降级为5秒轮询模式');
                    self.startPolling(url, onMessage);
                }
                
                if (onError) onError(e);
            };
            
            self.evtSource.onopen = function() {
                console.log('✅ SSE 连接已建立，实时数据推送已启用');
            };
            
        } catch(err) {
            console.error('SSE 初始化失败，使用轮询模式:', err);
            self.startPolling(url, onMessage);
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
