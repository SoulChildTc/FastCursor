/**
 * Cursor 账号管理系统前端 JS
 */

// DOM 加载完成后执行
document.addEventListener('DOMContentLoaded', function() {

    // 存储原始账号数据
    let originalAccountsData = [];
    
    // 存储下一次注册的时间戳
    let nextRunTimestamp = null;
    
    // 倒计时定时器
    let countdownTimer = null;
    
    // 初始加载数据
    loadStats();
    loadAccounts();
    loadSchedulerInfo();

    // 设置定时刷新调度器信息（每30秒）
    setInterval(loadSchedulerInfo, 30000);

    // 添加页面加载动画
    setTimeout(() => {
        document.querySelectorAll('.animate__animated').forEach(el => {
            el.classList.add('animate__faster');
        });
    }, 1000);

    // 刷新按钮点击事件
    document.getElementById('refresh-btn').addEventListener('click', function() {
        // 添加旋转动画
        const icon = this.querySelector('i');
        icon.classList.add('bx-spin');
        
        // 加载数据
        Promise.all([
            loadStatsAsync(),
            loadAccountsAsync(),
            loadSchedulerInfoAsync()
        ]).finally(() => {
            // 移除旋转动画
            setTimeout(() => {
                icon.classList.remove('bx-spin');
                showToast('刷新成功', '数据已更新', 'success');
            }, 500);
        });
    });

    // 触发注册按钮点击事件
    document.getElementById('trigger-registration').addEventListener('click', function() {
        triggerRegistration();
    });

    // 搜索输入框事件 - 使用防抖处理
    const searchInput = document.getElementById('search-input');
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(function() {
            filterAccounts();
        }, 300);
    });

    // 状态筛选事件
    document.getElementById('status-filter').addEventListener('change', function() {
        filterAccounts();
    });

    // 密码显示/隐藏切换
    document.getElementById('toggle-password').addEventListener('click', function() {
        const passwordInput = document.getElementById('detail-password');
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        this.innerHTML = type === 'password' ? '<i class="bx bx-show"></i>' : '<i class="bx bx-hide"></i>';
    });

    // 复制密码
    document.getElementById('copy-password').addEventListener('click', function() {
        copyToClipboard('detail-password');
    });

    // 复制 Token
    document.getElementById('copy-token').addEventListener('click', function() {
        copyToClipboard('detail-token');
    });

    // 批量标记相关
    const batchMarkModal = new bootstrap.Modal(document.getElementById('batch-mark-modal'));
    const suffixInput = document.getElementById('suffix-input');
    
    // 打开模态框
    document.getElementById('batch-mark-btn').addEventListener('click', function() {
        suffixInput.value = ''; // 清空输入
        batchMarkModal.show();
    });

    // 确认标记
    document.getElementById('confirm-batch-mark').addEventListener('click', function() {
        const suffix = suffixInput.value.trim();
        if (!suffix || !suffix.startsWith('@')) {
            showToast('错误', '请输入正确的邮箱后缀', 'danger');
            return;
        }

        // 禁用按钮，显示加载状态
        const btn = this;
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="bx bx-loader-alt bx-spin me-1"></i>处理中...';

        fetch('/api/accounts/batch-mark-invalid', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ suffix })
        })
        .then(response => response.json())
        .then(data => {
            if (data.code === 200) {
                // 创建并显示 Toast
                const toastEl = document.createElement('div');
                toastEl.className = 'toast align-items-center text-white bg-success border-0 position-fixed bottom-0 end-0 m-3';
                toastEl.setAttribute('role', 'alert');
                toastEl.setAttribute('aria-live', 'assertive');
                toastEl.setAttribute('aria-atomic', 'true');
                toastEl.innerHTML = `
                    <div class="d-flex">
                        <div class="toast-body">
                            <i class='bx bx-check-circle me-2'></i>
                            批量标记完成
                        </div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                    </div>
                `;
                
                document.body.appendChild(toastEl);
                const toast = new bootstrap.Toast(toastEl, {
                    delay: 3000
                });
                toast.show();
                
                // 自动移除 toast 元素
                toastEl.addEventListener('hidden.bs.toast', function () {
                    document.body.removeChild(toastEl);
                });
                
                // 刷新数据
                loadAccounts();
                updateStats();
                // 关闭模态框
                batchMarkModal.hide();
            } else {
                showToast('错误', data.message, 'danger');
            }
        })
        .catch(error => {
            showToast('错误', '操作失败: ' + error, 'danger');
        })
        .finally(() => {
            // 恢复按钮状态
            btn.disabled = false;
            btn.innerHTML = originalText;
        });
    });

    // 监听回车键
    suffixInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            document.getElementById('confirm-batch-mark').click();
        }
    });

    /**
     * 加载账号统计信息
     */
    function loadStats() {
        showLoading(true);
        loadStatsAsync().finally(() => {
            showLoading(false);
        });
    }
    
    /**
     * 异步加载统计信息
     * @returns {Promise} Promise对象
     */
    function loadStatsAsync() {
        return fetch('/api/stats')
            .then(response => {
                if (!response.ok) {
                    throw new Error('网络请求失败');
                }
                return response.json();
            })
            .then(data => {
                if (data.code === 200) {
                    updateStatsUI(data.data);
                } else {
                    showToast('错误', data.message, 'danger');
                }
            })
            .catch(error => {
                console.error('获取统计信息失败:', error);
                showToast('错误', '获取统计信息失败', 'danger');
            });
    }

    /**
     * 更新统计信息 UI
     * @param {Object} stats 统计数据
     */
    function updateStatsUI(stats) {
        // 使用动画效果更新数字
        animateNumber('total-accounts', stats.total);
        animateNumber('available-accounts', stats.available);
        animateNumber('allocated-accounts', stats.allocated);
        animateNumber('invalid-accounts', stats.invalid);
    }
    
    /**
     * 数字动画效果
     * @param {string} elementId 元素ID
     * @param {number} targetNumber 目标数字
     */
    function animateNumber(elementId, targetNumber) {
        const element = document.getElementById(elementId);
        const currentNumber = parseInt(element.textContent) || 0;
        if (isNaN(currentNumber) || element.textContent === '--') {
            element.textContent = targetNumber;
            return;
        }
        
        const duration = 1000; // 动画持续时间（毫秒）
        const steps = 20; // 动画步数
        const stepValue = (targetNumber - currentNumber) / steps;
        let currentStep = 0;
        
        const interval = setInterval(() => {
            currentStep++;
            const newValue = Math.round(currentNumber + stepValue * currentStep);
            element.textContent = newValue;
            
            if (currentStep >= steps) {
                clearInterval(interval);
                element.textContent = targetNumber;
            }
        }, duration / steps);
    }

    /**
     * 加载账号列表
     */
    function loadAccounts() {
        showLoading(true);
        document.getElementById('loading-spinner').classList.remove('d-none');
        document.getElementById('no-data-message').classList.add('d-none');
        
        // 清空搜索和筛选条件
        document.getElementById('search-input').value = '';
        document.getElementById('status-filter').value = 'all';
        
        loadAccountsAsync().finally(() => {
            showLoading(false);
            document.getElementById('loading-spinner').classList.add('d-none');
        });
    }
    
    /**
     * 异步加载账号列表
     * @returns {Promise} Promise对象
     */
    function loadAccountsAsync() {
        return fetch('/api/accounts')
            .then(response => {
                if (!response.ok) {
                    throw new Error('网络请求失败');
                }
                return response.json();
            })
            .then(data => {
                if (data.code === 200) {
                    // 保存原始数据
                    originalAccountsData = data.data;
                    renderAccountsTable(originalAccountsData);
                } else {
                    showToast('错误', data.message, 'danger');
                    document.getElementById('no-data-message').classList.remove('d-none');
                }
            })
            .catch(error => {
                console.error('获取账号列表失败:', error);
                showToast('错误', '获取账号列表失败', 'danger');
                document.getElementById('no-data-message').classList.remove('d-none');
            });
    }

    /**
     * 渲染账号表格
     * @param {Array} accounts 账号列表
     */
    function renderAccountsTable(accounts) {
        const tableBody = document.getElementById('accounts-table-body');
        tableBody.innerHTML = '';
        
        if (!accounts || accounts.length === 0) {
            document.getElementById('no-data-message').classList.remove('d-none');
            return;
        }
        
        document.getElementById('no-data-message').classList.add('d-none');
        
        accounts.forEach((account, index) => {
            const tr = document.createElement('tr');
            tr.setAttribute('data-account', JSON.stringify(account));
            
            // 添加淡入动画
            tr.classList.add('animate__animated', 'animate__fadeIn');
            tr.style.animationDelay = `${index * 0.05}s`;
            
            // 格式化日期
            const registerTime = formatDateTime(account.register_time);
            const lastAllocatedTime = account.last_allocated_time ? formatDateTime(account.last_allocated_time) : '-';
            
            // 状态样式
            const statusClass = getStatusClass(account.status);
            
            tr.innerHTML = `
                <td>${account.id}</td>
                <td>${account.email}</td>
                <td>
                    <span class="password-mask">••••••••</span>
                </td>
                <td class="status-column">
                    <span class="status-badge ${statusClass}">${getStatusText(account.status)}</span>
                </td>
                <td>${registerTime}</td>
                <td>${lastAllocatedTime}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-icon btn-outline-primary view-account" title="查看详情">
                            <i class='bx bx-detail'></i>
                        </button>
                        <button class="btn btn-icon btn-outline-success switch-account ${account.status !== 'available' ? 'disabled' : ''}" 
                                title="更换账号" ${account.status !== 'available' ? 'disabled' : ''}>
                            <i class='bx bx-transfer'></i>
                        </button>
                    </div>
                </td>
            `;
            
            tableBody.appendChild(tr);
        });
        
        // 添加查看详情事件
        document.querySelectorAll('.view-account').forEach(btn => {
            btn.addEventListener('click', function() {
                const accountData = JSON.parse(this.closest('tr').getAttribute('data-account'));
                showAccountDetails(accountData);
            });
        });

        // 添加更换账号事件
        document.querySelectorAll('.switch-account').forEach(btn => {
            btn.addEventListener('click', function() {
                if (!this.disabled) {
                    const accountData = JSON.parse(this.closest('tr').getAttribute('data-account'));
                    switchCursorAccount(accountData);
                }
            });
        });
    }

    /**
     * 筛选账号列表
     */
    function filterAccounts() {
        if (!originalAccountsData || originalAccountsData.length === 0) {
            return;
        }
        
        const searchTerm = document.getElementById('search-input').value.toLowerCase().trim();
        const statusFilter = document.getElementById('status-filter').value;
        
        // 如果没有筛选条件，显示所有数据
        if (!searchTerm && statusFilter === 'all') {
            renderAccountsTable(originalAccountsData);
            return;
        }
        
        const filteredAccounts = originalAccountsData.filter(account => {
            const matchSearch = !searchTerm || (account.email && account.email.toLowerCase().includes(searchTerm));
            const matchStatus = statusFilter === 'all' || account.status === statusFilter;
            return matchSearch && matchStatus;
        });
        
        renderAccountsTable(filteredAccounts);
        
        // 显示筛选结果数量
        const resultCount = filteredAccounts.length;
        const totalCount = originalAccountsData.length;
        showToast('筛选结果', `显示 ${resultCount}/${totalCount} 条记录`, 'info');
    }

    /**
     * 显示账号详情
     * @param {Object} account 账号数据
     */
    function showAccountDetails(account) {
        // 保存当前账号数据到模态框元素上，方便后续使用
        const modal = document.getElementById('account-details-modal');
        modal.setAttribute('data-account', JSON.stringify(account));
        
        document.getElementById('detail-email').value = account.email || '';
        document.getElementById('detail-password').value = account.password || '';
        document.getElementById('detail-token').value = account.token || '无';
        document.getElementById('detail-register-time').value = formatDateTime(account.register_time);
        document.getElementById('detail-last-allocated-time').value = account.last_allocated_time ? formatDateTime(account.last_allocated_time) : '无';
        
        // 设置单选按钮状态
        document.getElementById('status-available').checked = account.status === 'available';
        document.getElementById('status-allocated').checked = account.status === 'allocated';
        document.getElementById('status-invalid').checked = account.status === 'invalid';
        
        // 重置密码显示状态
        document.getElementById('detail-password').setAttribute('type', 'password');
        document.getElementById('toggle-password').innerHTML = '<i class="bx bx-show"></i>';
        
        // 显示模态框
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
    }

    /**
     * 获取状态文本
     * @param {string} status 状态值
     * @returns {string} 状态文本
     */
    function getStatusText(status) {
        const statusMap = {
            'available': '可用',
            'allocated': '已分配',
            'invalid': '无效'
        };
        return statusMap[status] || status || '未知';
    }

    /**
     * 获取状态样式类
     * @param {string} status 状态值
     * @returns {string} 样式类名
     */
    function getStatusClass(status) {
        const classMap = {
            'available': 'status-available',
            'allocated': 'status-allocated',
            'invalid': 'status-invalid'
        };
        return classMap[status] || '';
    }

    /**
     * 格式化日期时间
     * @param {string} dateTimeStr 日期时间字符串
     * @returns {string} 格式化后的日期时间
     */
    function formatDateTime(dateTimeStr) {
        if (!dateTimeStr) return '-';
        try {
            // 将时间字符串转换为时间戳
            const timestamp = Date.parse(dateTimeStr);
            // 创建新的日期对象
            const date = new Date(timestamp);
            const pad = (num) => String(num).padStart(2, '0');
            
            // 使用 UTC 方法获取时间组件
            const year = date.getUTCFullYear();
            const month = pad(date.getUTCMonth() + 1);
            const day = pad(date.getUTCDate());
            const hour = pad(date.getUTCHours());
            const minute = pad(date.getUTCMinutes());
            const second = pad(date.getUTCSeconds());
            
            return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
        } catch (e) {
            return dateTimeStr;
        }
    }

    /**
     * 复制文本到剪贴板
     * @param {string} elementId 元素ID
     */
    function copyToClipboard(elementId) {
        const element = document.getElementById(elementId);
        element.select();
        document.execCommand('copy');
        
        // 添加复制成功的动画效果
        const button = document.getElementById(`copy-${elementId.split('-')[1]}`);
        const originalIcon = button.innerHTML;
        button.innerHTML = '<i class="bx bx-check" style="color: var(--success-color)"></i>';
        
        setTimeout(() => {
            button.innerHTML = originalIcon;
        }, 1500);
        
        showToast('成功', '已复制到剪贴板', 'success');
    }

    /**
     * 显示/隐藏加载状态
     * @param {boolean} isLoading 是否加载中
     */
    function showLoading(isLoading) {
        // 可以在这里添加全局加载状态的显示逻辑
    }

    /**
     * 显示提示消息
     * @param {string} title 标题
     * @param {string} message 消息内容
     * @param {string} type 类型 (success, danger, warning, info)
     */
    function showToast(title, message, type = 'info') {
        // 创建 Toast 元素
        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0 animate__animated animate__fadeInUp" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="bx ${getToastIcon(type)} me-2"></i>
                        <strong>${title}</strong>: ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        // 添加到页面
        if (!document.querySelector('.toast-container')) {
            const toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        const toastContainer = document.querySelector('.toast-container');
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        // 显示 Toast
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
        toast.show();
        
        // 自动移除
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    }
    
    /**
     * 获取Toast图标
     * @param {string} type 类型
     * @returns {string} 图标类名
     */
    function getToastIcon(type) {
        const iconMap = {
            'success': 'bx-check-circle',
            'danger': 'bx-error-circle',
            'warning': 'bx-error',
            'info': 'bx-info-circle'
        };
        return iconMap[type] || 'bx-info-circle';
    }

    /**
     * 加载调度器信息
     */
    function loadSchedulerInfo() {
        loadSchedulerInfoAsync();
    }
    
    /**
     * 异步加载调度器信息
     * @returns {Promise} Promise对象
     */
    function loadSchedulerInfoAsync() {
        return fetch('/api/scheduler/next')
            .then(response => response.json())
            .then(data => {
                if (data.code === 200) {
                    updateSchedulerUI(data.data);
                    // 设置倒计时
                    setupCountdown(data.data.next_run_time);
                } else {
                    console.error('获取调度器信息失败:', data.message);
                }
            })
            .catch(error => {
                console.error('获取调度器信息出错:', error);
            });
    }

    /**
     * 更新调度器UI
     */
    function updateSchedulerUI(data) {
        const nextRunTimeEl = document.getElementById('next-run-time');
        const timeLeftEl = document.getElementById('time-left');
        
        // 如果值发生变化，添加高亮动画
        if (nextRunTimeEl.value !== data.next_run_time) {
            nextRunTimeEl.classList.add('animate__animated', 'animate__flash');
            setTimeout(() => {
                nextRunTimeEl.classList.remove('animate__animated', 'animate__flash');
            }, 1000);
        }
        
        nextRunTimeEl.value = data.next_run_time;
        
        // 初始设置剩余时间（后续会由倒计时更新）
        if (!countdownTimer) {
            timeLeftEl.value = data.time_left;
        }
    }
    
    /**
     * 设置倒计时
     * @param {string} nextRunTimeStr 下一次运行时间字符串
     */
    function setupCountdown(nextRunTimeStr) {
        // 清除现有的倒计时
        if (countdownTimer) {
            clearInterval(countdownTimer);
            countdownTimer = null;
        }
        
        // 解析下一次运行时间
        const nextRunTime = new Date(nextRunTimeStr);
        nextRunTimestamp = nextRunTime.getTime();
        
        // 如果时间无效，不设置倒计时
        if (isNaN(nextRunTimestamp)) {
            return;
        }
        
        // 立即更新一次
        updateCountdown();
        
        // 设置倒计时定时器，每秒更新一次
        countdownTimer = setInterval(updateCountdown, 1000);
    }
    
    /**
     * 更新倒计时显示
     */
    function updateCountdown() {
        if (!nextRunTimestamp) return;
        
        const now = new Date().getTime();
        const timeLeft = nextRunTimestamp - now;
        
        // 如果时间已过，停止倒计时
        if (timeLeft <= 0) {
            clearInterval(countdownTimer);
            countdownTimer = null;
            document.getElementById('time-left').value = "即将开始...";
            
            // 10秒后重新加载调度器信息
            setTimeout(loadSchedulerInfo, 10000);
            return;
        }
        
        // 计算剩余时间
        const hours = Math.floor(timeLeft / (1000 * 60 * 60));
        const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);
        
        // 格式化剩余时间
        const formattedTime = `${hours}小时 ${minutes}分钟 ${seconds}秒`;
        
        // 更新显示
        const timeLeftEl = document.getElementById('time-left');
        timeLeftEl.value = formattedTime;
        
        // 当剩余时间少于5分钟时，添加闪烁效果
        if (timeLeft < 5 * 60 * 1000) {
            timeLeftEl.classList.add('text-danger');
            
            // 当剩余时间少于1分钟时，添加更强的视觉提示
            if (timeLeft < 60 * 1000) {
                if (!timeLeftEl.classList.contains('animate__animated')) {
                    timeLeftEl.classList.add('animate__animated', 'animate__pulse');
                    timeLeftEl.style.animationIterationCount = 'infinite';
                }
            }
        } else {
            timeLeftEl.classList.remove('text-danger', 'animate__animated', 'animate__pulse');
            timeLeftEl.style.animationIterationCount = '';
        }
    }

    /**
     * 触发账号注册
     */
    function triggerRegistration() {
        const button = document.getElementById('trigger-registration');
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 注册中...';

        // 显示日志模态框
        const logModal = new bootstrap.Modal(document.getElementById('log-viewer-modal'));
        const logContent = document.getElementById('log-content');
        logContent.innerHTML = ''; // 清空之前的日志
        logModal.show();

        // 创建 EventSource 连接
        const eventSource = new EventSource('/api/logs/stream');
        
        // 监听日志消息
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            const logLine = data.log;
            
            // 添加新的日志行
            logContent.innerHTML += logLine + '\n';
            
            // 自动滚动到底部
            const logContainer = logContent.parentElement;
            logContainer.scrollTop = logContainer.scrollHeight;
        };

        // 监听连接错误
        eventSource.onerror = function() {
            eventSource.close();
            showToast('错误', '日志流连接已断开', 'warning');
        };

        // 监听模态框关闭事件
        document.getElementById('log-viewer-modal').addEventListener('hidden.bs.modal', function () {
            eventSource.close(); // 关闭日志流连接
        });

        // 清空日志按钮事件
        document.getElementById('clear-logs').addEventListener('click', function() {
            logContent.innerHTML = '';
        });

        fetch('/api/scheduler/trigger', {
            method: 'POST'
        })
            .then(response => response.json())
            .then(data => {
                if (data.code === 200) {
                    showToast('成功', '已触发账号注册任务，请稍后刷新查看结果', 'success');
                    
                    // 清除现有的倒计时
                    if (countdownTimer) {
                        clearInterval(countdownTimer);
                        countdownTimer = null;
                    }
                } else {
                    showToast('错误', data.message, 'danger');
                    logModal.hide(); // 出错时关闭日志模态框
                }
            })
            .catch(error => {
                console.error('触发注册出错:', error);
                showToast('错误', '触发注册失败，请查看控制台日志', 'danger');
                logModal.hide(); // 出错时关闭日志模态框
            })
            .finally(() => {
                setTimeout(() => {
                    button.disabled = false;
                    button.innerHTML = '<i class="bx bx-play-circle me-2"></i>立即注册一个账号';
                    // 刷新调度器信息
                    loadSchedulerInfo();
                    // 添加成功动画
                    button.classList.add('animate__animated', 'animate__pulse');
                    setTimeout(() => {
                        button.classList.remove('animate__animated', 'animate__pulse');
                    }, 1000);
                }, 3000);
            });
    }

    // 更新统计信息
    function updateStats() {
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                if (data.code === 200) {
                    document.getElementById('total-accounts').textContent = data.data.total;
                    document.getElementById('available-accounts').textContent = data.data.available;
                    document.getElementById('allocated-accounts').textContent = data.data.allocated;
                    document.getElementById('invalid-accounts').textContent = data.data.invalid;
                }
            })
            .catch(error => console.error('获取统计信息失败:', error));
    }

    // 初始加载统计信息
    updateStats();

    /**
     * 更换 Cursor 账号
     * @param {Object} account 账号数据
     */
    function switchCursorAccount(account) {
        // 检查是否已存在模态框，如果存在则移除
        let existingModal = document.getElementById('switch-account-modal');
        if (existingModal) {
            existingModal.remove();
        }

        // 创建模态框 HTML
        const modalHtml = `
            <div class="modal fade" id="switch-account-modal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class='bx bx-transfer text-primary me-2'></i>确认更换账号
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="text-center mb-4">
                                <div class="avatar-lg mx-auto mb-3">
                                    <i class='bx bx-user-circle' style="font-size: 4rem; color: var(--primary-color);"></i>
                                </div>
                                <h5 class="mb-3">确定要更换到以下账号吗？</h5>
                                <p class="text-muted" id="switch-account-email">${account.email}</p>
                            </div>
                            <div class="alert alert-info">
                                <i class='bx bx-info-circle me-2'></i>
                                <span>更换账号后会自动重启 cursor</span>
                                <br/>
                                <span>如重启失败请手动重启</span>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-light" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" id="confirm-switch-account">
                                <i class='bx bx-check me-1'></i>确认更换
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 将模态框添加到 body
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // 获取新创建的模态框元素
        const modalEl = document.getElementById('switch-account-modal');
        
        try {
            // 创建模态框实例
            const modal = new bootstrap.Modal(modalEl, {
                backdrop: 'static',
                keyboard: false
            });
            
            // 获取确认按钮
            const confirmButton = document.getElementById('confirm-switch-account');
            if (!confirmButton) {
                console.error('找不到确认按钮');
                return;
            }

            const originalHtml = confirmButton.innerHTML;
            
            // 定义确认处理函数
            const handleConfirm = () => {
                confirmButton.disabled = true;
                confirmButton.innerHTML = '<i class="bx bx-loader-alt bx-spin me-1"></i>正在更换...';

                fetch('/api/account/switch', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ account_id: account.id })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.code === 200) {
                        modal.hide();
                        showToast('成功', '账号更换成功', 'success');
                        // 刷新账号列表和统计信息
                        loadAccounts();
                        updateStats();
                    } else {
                        showToast('错误', data.message || '更换账号失败', 'danger');
                    }
                })
                .catch(error => {
                    console.error('更换账号失败:', error);
                    showToast('错误', '更换账号失败，请查看控制台日志', 'danger');
                })
                .finally(() => {
                    confirmButton.disabled = false;
                    confirmButton.innerHTML = originalHtml;
                });
            };

            // 添加确认按钮事件监听器
            confirmButton.addEventListener('click', handleConfirm);
            
            // 模态框隐藏后清理
            modalEl.addEventListener('hidden.bs.modal', function () {
                modal.dispose();
                modalEl.remove();
            });
            
            // 显示模态框
            modal.show();
            
        } catch (error) {
            console.error('初始化模态框失败:', error);
            // 降级为使用原生 confirm
            if (confirm(`确定要更换到账号 ${account.email} 吗？`)) {
                handleConfirm();
            }
        }
    }

    // 添加保存状态按钮的点击事件
    document.getElementById('save-status-btn').addEventListener('click', function() {
        const modal = document.getElementById('account-details-modal');
        const accountData = JSON.parse(modal.getAttribute('data-account'));
        const email = accountData.email;
        
        // 获取选中的状态值
        const statusRadios = document.getElementsByName('status-option');
        let selectedStatus = '';
        for (const radio of statusRadios) {
            if (radio.checked) {
                selectedStatus = radio.value;
                break;
            }
        }
        
        // 如果状态没有变化，不执行保存操作
        if (selectedStatus === accountData.status) {
            showToast('提示', '状态未发生变化', 'info');
            return;
        }
        
        // 保存按钮状态
        const button = this;
        const originalText = button.innerHTML;
        button.disabled = true;
        button.classList.add('saving');
        button.innerHTML = '<i class="bx bx-loader-alt bx-spin me-1"></i>保存中...';
        
        // 发送请求更新状态
        fetch('/api/account/mark-status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                status: selectedStatus
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.code === 200) {
                showToast('成功', '账号状态已更新', 'success');
                
                // 更新本地数据
                accountData.status = selectedStatus;
                modal.setAttribute('data-account', JSON.stringify(accountData));
                
                // 更新表格中的账号状态
                updateAccountInTable(accountData);
                
                // 刷新统计信息
                updateStats();
                
                // 隐藏模态框
                bootstrap.Modal.getInstance(modal).hide();
            } else {
                showToast('错误', data.message || '状态更新失败', 'danger');
            }
        })
        .catch(error => {
            console.error('更新状态失败:', error);
            showToast('错误', '状态更新失败，请查看控制台日志', 'danger');
        })
        .finally(() => {
            // 恢复按钮状态
            button.disabled = false;
            button.classList.remove('saving');
            button.innerHTML = originalText;
        });
    });

    /**
     * 更新表格中的账号状态
     * @param {Object} updatedAccount 更新后的账号
     */
    function updateAccountInTable(updatedAccount) {
        // 查找对应的表格行
        const rows = document.querySelectorAll('#accounts-table-body tr');
        for (const row of rows) {
            const accountData = JSON.parse(row.getAttribute('data-account'));
            if (accountData.id === updatedAccount.id) {
                // 更新行数据
                row.setAttribute('data-account', JSON.stringify(updatedAccount));
                
                // 更新状态单元格
                const statusCell = row.querySelector('td.status-column');
                if (statusCell) {
                    const statusBadge = statusCell.querySelector('.status-badge');
                    if (statusBadge) {
                        statusBadge.className = 'status-badge ' + getStatusClass(updatedAccount.status);
                        statusBadge.textContent = getStatusText(updatedAccount.status);
                    }
                }
                
                // 更新操作按钮状态
                const switchBtn = row.querySelector('.switch-account');
                if (switchBtn) {
                    if (updatedAccount.status === 'available') {
                        switchBtn.classList.remove('disabled');
                        switchBtn.disabled = false;
                    } else {
                        switchBtn.classList.add('disabled');
                        switchBtn.disabled = true;
                    }
                }
                
                // 添加行高亮动画效果
                row.classList.add('animate__animated', 'animate__pulse');
                setTimeout(() => {
                    row.classList.remove('animate__animated', 'animate__pulse');
                }, 1000);
                
                break;
            }
        }
    }
});
