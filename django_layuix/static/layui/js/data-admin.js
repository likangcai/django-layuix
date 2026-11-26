/**
 * Shared helpers for data-management pages.
 */
(function (window) {
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
        var layer = window.layui && window.layui.layer;
        if (!layer) return;
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

    var RESOURCE_PERM_PREFIX = {
        departments: 'dept',
        positions: 'position',
        regions: 'region',
        member_levels: 'member_level'
    };

    function permissionPrefix(resource) {
        return RESOURCE_PERM_PREFIX[resource] || resource;
    }

    function tableToolbar(resource) {
        var prefix = permissionPrefix(resource);
        var html = '<div class="layui-btn-container data-table-toolbar">';
        if (hasPerm(prefix + ':add')) {
            html += '<button type="button" class="layui-btn layui-btn-sm layui-btn-primary" lay-event="data-import">' +
                '<i class="layui-icon layui-icon-upload"></i>' + (typeof t === 'function' ? t('data.import') : 'Import') + '</button>';
        }
        html += '<button type="button" class="layui-btn layui-btn-sm layui-btn-primary" lay-event="data-export">' +
            '<i class="layui-icon layui-icon-download-circle"></i>' + (typeof t === 'function' ? t('data.export') : 'Export') + '</button>';
        if (hasPerm(prefix + ':edit')) {
            html += '<button type="button" class="layui-btn layui-btn-sm layui-btn-primary" lay-event="data-enable">' +
                '<i class="layui-icon layui-icon-play"></i>' + (typeof t === 'function' ? t('data.batchEnable') : 'Batch enable') + '</button>';
            html += '<button type="button" class="layui-btn layui-btn-sm layui-btn-primary" lay-event="data-disable">' +
                '<i class="layui-icon layui-icon-pause"></i>' + (typeof t === 'function' ? t('data.batchDisable') : 'Batch disable') + '</button>';
        }
        if (hasPerm(prefix + ':delete')) {
            html += '<button type="button" class="layui-btn layui-btn-sm layui-btn-danger" lay-event="data-delete">' +
                '<i class="layui-icon layui-icon-delete"></i>' + (typeof t === 'function' ? t('data.batchDelete') : 'Batch delete') + '</button>';
        }
        html += '</div>';
        var hostId = 'data-toolbar-' + resource;
        var old = document.getElementById(hostId);
        if (old) old.parentNode.removeChild(old);
        var host = document.createElement('div');
        host.id = hostId;
        host.style.display = 'none';
        host.innerHTML = html;
        document.body.appendChild(host);
        return '#' + hostId;
    }

    function selectedIds(table, tableId) {
        var rows = (table.checkStatus(tableId).data) || [];
        return rows.map(function (row) { return row.id; });
    }

    function notify(message, icon) {
        var layer = window.layui && window.layui.layer;
        if (layer) layer.msg(message, {icon: icon || 1});
    }

    function downloadExport(resource, format) {
        notify(typeof t === 'function' ? t('data.exporting') : 'Exporting...', 0);
        window.location.href = '/admin/api/rbac/data-export/?resource=' +
            encodeURIComponent(resource) + '&format=' + encodeURIComponent(format);
    }

    function openExportDialog(resource) {
        var layer = window.layui && window.layui.layer;
        if (!layer) return;
        var html = '' +
            '<div class="data-export-dialog">' +
            '<button type="button" class="layui-btn layui-btn-primary data-export-choice" data-format="csv">' +
            'CSV</button>' +
            '<button type="button" class="layui-btn layui-btn-primary data-export-choice" data-format="xlsx">' +
            'Excel (.xlsx)</button>' +
            '</div>';
        var index = layer.open({
            type: 1,
            title: typeof t === 'function' ? t('data.exportTitle') : 'Export',
            skin: 'layui-layer-admin',
            area: ['420px', 'auto'],
            content: html,
            success: function (layero) {
                layero.find('.data-export-choice').on('click', function () {
                    var format = window.layui.jquery(this).data('format');
                    layer.close(index);
                    downloadExport(resource, format);
                });
            },
        });
    }

    function openImportDialog(resource, done) {
        var layer = window.layui && window.layui.layer;
        if (!layer) return;
        var html = '' +
            '<div class="data-import-dialog">' +
            '<div class="layui-form-item"><label class="layui-form-label">' +
            (typeof t === 'function' ? t('data.importMode') : 'Import mode') + '</label>' +
            '<div class="layui-input-block"><select id="dataImportMode" class="layui-input">' +
            '<option value="upsert">' + (typeof t === 'function' ? t('data.importUpsert') : 'Create and update') + '</option>' +
            '<option value="insert">' + (typeof t === 'function' ? t('data.importInsert') : 'Create only') + '</option>' +
            '</select></div></div>' +
            '<div class="layui-form-item"><label class="layui-form-label">' +
            (typeof t === 'function' ? t('data.chooseFile') : 'Choose CSV or Excel') + '</label>' +
            '<div class="layui-input-block"><input type="file" id="dataImportFile" accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"></div></div>' +
            '<div class="data-import-hint">' + (typeof t === 'function' ? t('data.importHint') : '') + '</div>' +
            '</div>';
        LayuiUI.dialog({
            title: typeof t === 'function' ? t('data.importTitle') : 'Import CSV or Excel',
            content: html,
            area: ['560px', 'auto'],
            btn: [typeof t === 'function' ? t('data.import') : 'Import',
                typeof t === 'function' ? t('common.cancel') : 'Cancel'],
            yes: function (index, layero) {
                var input = layero.find('#dataImportFile')[0];
                if (!input || !input.files || !input.files.length) {
                    layer.msg(typeof t === 'function' ? t('data.chooseFile') : 'Choose CSV or Excel file', {icon: 2});
                    return;
                }
                var button = layero.find('.layui-layer-btn0');
                button.addClass('layui-btn-disabled').prop('disabled', true);
                var data = new FormData();
                data.append('resource', resource);
                data.append('mode', layero.find('#dataImportMode').val() || 'upsert');
                data.append('file', input.files[0]);
                fetch('/admin/api/rbac/data-import/', {
                    method: 'POST',
                    credentials: 'same-origin',
                    body: data,
                }).then(function (response) {
                    return response.json();
                }).then(function (res) {
                    button.removeClass('layui-btn-disabled').prop('disabled', false);
                    if (res.code !== 200) {
                        layer.msg(res.msg || 'Import failed', {icon: 2});
                        return;
                    }
                    var result = res.data || {};
                    var summary = (typeof t === 'function'
                        ? t('data.importResult', [result.created || 0, result.updated || 0,
                            result.skipped || 0, (result.errors || []).length])
                        : 'Import complete');
                    layer.close(index);
                    if (done) done();
                    if (result.errors && result.errors.length) {
                        var rows = result.errors.slice(0, 20).map(function (item) {
                            return '<div>#' + escapeHtml(item.row) + ' ' + escapeHtml(item.message) + '</div>';
                        }).join('');
                        layer.alert(summary + '<div class="data-import-errors"><b>' +
                            (typeof t === 'function' ? t('data.importErrors') : 'Errors') +
                            '</b>' + rows + '</div>', {title: summary, skin: 'layui-layer-admin'});
                    } else {
                        layer.msg(summary, {icon: 1});
                    }
                }).catch(function () {
                    button.removeClass('layui-btn-disabled').prop('disabled', false);
                    layer.msg(typeof t === 'function' ? t('common.loadFailed') : 'Import failed', {icon: 2});
                });
            }
        });
    }

    function batchStatus(resource, ids, status, done) {
        postApi('/admin/api/rbac/data-batch-status/', {
            resource: resource, ids: ids, status: status
        }, function (res) {
            if (res.code !== 200) {
                notify(res.msg || 'Update failed', 2);
                return;
            }
            notify(typeof t === 'function'
                ? t('data.batchStatusUpdated', [res.data.updated || 0])
                : 'Updated', 1);
            if (done) done();
        });
    }

    function batchDelete(resource, ids, done) {
        confirmDelete(typeof t === 'function' ? t('common.confirmDelete') : 'Delete selected?', function () {
            postApi('/admin/api/rbac/data-batch-delete/', {
                resource: resource, ids: ids
            }, function (res) {
                if (res.code !== 200) {
                    notify(res.msg || 'Delete failed', 2);
                    return;
                }
                var message = typeof t === 'function'
                    ? t('data.batchDeleted', [res.data.deleted || 0])
                    : 'Deleted';
                if ((res.data.skipped || []).length) {
                    message += '；' + (typeof t === 'function'
                        ? t('data.batchSkipped', [res.data.skipped.length]) : ' skipped');
                }
                notify(message, 1);
                if (done) done();
            });
        });
    }

    function bindTableToolbar(table, tableId, resource, reload) {
        table.on('toolbar(' + tableId + ')', function (obj) {
            var ids = selectedIds(table, tableId);
            if (obj.event === 'data-export') {
                openExportDialog(resource);
                return;
            }
            if (obj.event === 'data-import') {
                openImportDialog(resource, reload);
                return;
            }
            if (!ids.length) {
                notify(typeof t === 'function' ? t('data.noSelection') : 'Select rows first', 0);
                return;
            }
            if (obj.event === 'data-enable') {
                batchStatus(resource, ids, true, reload);
            } else if (obj.event === 'data-disable') {
                batchStatus(resource, ids, false, reload);
            } else if (obj.event === 'data-delete') {
                batchDelete(resource, ids, reload);
            }
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
        permissionPrefix: permissionPrefix,
        tableToolbar: tableToolbar,
        selectedIds: selectedIds,
        downloadExport: downloadExport,
        openExportDialog: openExportDialog,
        openImportDialog: openImportDialog,
        batchStatus: batchStatus,
        batchDelete: batchDelete,
        bindTableToolbar: bindTableToolbar,
    };
})(window);
