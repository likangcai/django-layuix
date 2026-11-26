/**
 * Shared helpers for data-management pages.
 */
(function (window, $) {
    'use strict';

    function currentUser() {
        return (window.parent && window.parent.currentUser) || window.currentUser || {};
    }

    function perms() {
        return currentUser().permissions || [];
    }

    function hasPerm(code) {
        var user = currentUser();
        return !!user.is_superuser || perms().indexOf(code) > -1;
    }

    function statusBadge(status) {
        if (status) {
            return '<span class="layui-badge layui-bg-green">' +
                (typeof t === 'function' ? t('data.enabled') : 'Enabled') + '</span>';
        }
        return '<span class="layui-badge layui-bg-gray">' +
            (typeof t === 'function' ? t('data.disabled') : 'Disabled') + '</span>';
    }

    function buildTree(rows, idKey, parentKey) {
        idKey = idKey || 'id';
        parentKey = parentKey || 'parent_id';
        var map = {};
        var roots = [];
        (rows || []).forEach(function (row) {
            map[String(row[idKey])] = Object.assign({}, row, {children: []});
        });
        Object.keys(map).forEach(function (key) {
            var row = map[key];
            var parent = map[String(row[parentKey])];
            if (parent && parent !== row) parent.children.push(row);
            else roots.push(row);
        });
        return {list: rows || [], map: map, roots: roots};
    }

    function treeData(nodes, titleKey) {
        titleKey = titleKey || 'name';
        return (nodes || []).map(function (node) {
            return {
                id: node.id,
                title: node[titleKey] || node.name,
                children: treeData(node.children, titleKey),
                spread: false,
            };
        });
    }

    function descendantIds(rows, id, idKey, parentKey) {
        idKey = idKey || 'id';
        parentKey = parentKey || 'parent_id';
        var allowed = {};
        allowed[String(id)] = true;
        var changed = true;
        while (changed) {
            changed = false;
            (rows || []).forEach(function (row) {
                if (allowed[String(row[parentKey])] && !allowed[String(row[idKey])]) {
                    allowed[String(row[idKey])] = true;
                    changed = true;
                }
            });
        }
        return allowed;
    }

    function matches(row, keyword, fields) {
        if (!keyword) return true;
        keyword = String(keyword).toLowerCase();
        return (fields || []).some(function (field) {
            return String(row[field] === undefined ? '' : row[field]).toLowerCase().indexOf(keyword) > -1;
        });
    }

    function loadPerms(callback) {
        var current = currentUser();
        if (current.is_superuser || (current.permissions && current.permissions.length)) {
            callback(current);
            return;
        }
        if (typeof getApi !== 'function') {
            callback(current);
            return;
        }
        getApi('/admin/api/rbac/userinfo/', function (res) {
            if (res.code === 200 && res.data) {
                current = res.data;
                window.parent.currentUser = current;
                window.currentUser = current;
            }
            callback(current);
        });
    }

    function confirmDelete(message, callback) {
        if (typeof layer === 'undefined') return;
        layer.confirm(message, {
            title: typeof t === 'function' ? t('common.confirmDelete') : 'Delete',
            skin: 'layui-layer-admin',
            btn: [typeof t === 'function' ? t('common.confirm') : 'Confirm',
                typeof t === 'function' ? t('common.cancel') : 'Cancel'],
        }, function (index) {
            layer.close(index);
            callback();
        });
    }

    window.DataAdmin = {
        perms: perms,
        hasPerm: hasPerm,
        statusBadge: statusBadge,
        buildTree: buildTree,
        treeData: treeData,
        descendantIds: descendantIds,
        matches: matches,
        loadPerms: loadPerms,
        confirmDelete: confirmDelete,
    };
})(window, window.layui ? window.layui.$ : window.jQuery);
