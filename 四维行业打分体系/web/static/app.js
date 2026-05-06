/**
 * 四维行业打分体系 - 主应用逻辑
 * 处理所有交互操作和UI更新
 */

// 全局状态管理
let comparisonList = [];
let currentScoreResult = null;

// DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    loadTokenFromStorage();
});

/**
 * 初始化应用
 */
function initializeApp() {
    setupTabNavigation();
    setupFormInteractions();
    loadFromLocalStorage();
}

// ============================================================
// Tushare 数据获取 API 调用
// ============================================================

const API_BASE = '';

function getToken() {
    return document.getElementById('tushare-token').value.trim();
}

function getIndustryName() {
    return document.getElementById('industry-name').value.trim();
}

function saveTokenToStorage(token) {
    try {
        localStorage.setItem('tushare_token', token);
    } catch (e) {}
}

function loadTokenFromStorage() {
    try {
        const saved = localStorage.getItem('tushare_token');
        if (saved) {
            document.getElementById('tushare-token').value = saved;
        }
    } catch (e) {}
}

function toggleTokenVisibility() {
    const input = document.getElementById('tushare-token');
    input.type = input.type === 'password' ? 'text' : 'password';
}

async function apiCall(endpoint, body) {
    const resp = await fetch(API_BASE + endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    const data = await resp.json();
    if (!resp.ok || data.error) {
        throw new Error(data.error || `HTTP ${resp.status}`);
    }
    return data;
}

function showFetchStatus(elementId, message, type) {
    const el = document.getElementById(elementId);
    el.style.display = 'block';
    el.className = `fetch-status fetch-${type}`;
    el.textContent = message;
    if (type === 'success') {
        setTimeout(() => { el.style.display = 'none'; }, 4000);
    }
}

function setButtonLoading(btnId, loading) {
    const btn = document.getElementById(btnId);
    if (loading) {
        btn.disabled = true;
        btn.dataset.originalText = btn.textContent;
        btn.textContent = '⏳ 获取中...';
    } else {
        btn.disabled = false;
        btn.textContent = btn.dataset.originalText || btn.textContent;
    }
}

async function testTushareConnection() {
    const token = getToken();
    if (!token) {
        showAlert('请先输入Tushare Token', 'warning');
        return;
    }

    const statusEl = document.getElementById('connection-status');
    statusEl.style.display = 'block';
    statusEl.className = 'connection-status status-loading';
    statusEl.textContent = '⏳ 正在测试连接...';

    setButtonLoading('btn-test-conn', true);

    try {
        const data = await apiCall('/api/fetch_industry', {
            token: token,
            industry_name: '人工智能'
        });

        saveTokenToStorage(token);
        statusEl.className = 'connection-status status-success';
        statusEl.innerHTML = `✅ 连接成功！支持 ${data.ths_code ? '同花顺行业指数' : '基础数据'}，行业类型：${data.industry_type}，周期阶段：${data.cycle_phase}`;
        showAlert('Tushare 连接成功！', 'success');
    } catch (e) {
        statusEl.className = 'connection-status status-error';
        statusEl.textContent = `❌ 连接失败：${e.message}`;
        showAlert(`连接失败：${e.message}`, 'error');
    } finally {
        setButtonLoading('btn-test-conn', false);
    }
}

async function fetchCapitalData() {
    const token = getToken();
    const industryName = getIndustryName();

    if (!token) { showAlert('请先输入Tushare Token', 'warning'); return; }
    if (!industryName) { showAlert('请先输入行业名称', 'warning'); return; }

    setButtonLoading('btn-fetch-capital', true);
    showFetchStatus('capital-fetch-status', '⏳ 正在获取ETF资金流向数据...', 'loading');

    try {
        const data = await apiCall('/api/fetch_capital', {
            token: token,
            industry_name: industryName
        });

        document.getElementById('etf-subscription').value = data.etf_net_subscription;

        if (!data.fund_position_available) {
            showFetchStatus('capital-fetch-status',
                `⚠️ ETF资金已获取（净申购：${data.etf_net_subscription}亿），公募仓位需手动填写（需Tushare高级积分）`,
                'warning');
        } else {
            document.getElementById('fund-position-change').value = data.fund_position_change;
            showFetchStatus('capital-fetch-status',
                `✅ 资金面数据已填充：ETF净申购 ${data.etf_net_subscription}亿，公募仓位变化 ${data.fund_position_change}%`,
                'success');
        }

        saveTokenToStorage(token);
    } catch (e) {
        showFetchStatus('capital-fetch-status', `❌ 获取失败：${e.message}`, 'error');
    } finally {
        setButtonLoading('btn-fetch-capital', false);
    }
}

async function fetchTechnicalData() {
    const token = getToken();
    const industryName = getIndustryName();

    if (!token) { showAlert('请先输入Tushare Token', 'warning'); return; }
    if (!industryName) { showAlert('请先输入行业名称', 'warning'); return; }

    setButtonLoading('btn-fetch-technical', true);
    showFetchStatus('technical-fetch-status', '⏳ 正在检测技术信号...', 'loading');

    try {
        const data = await apiCall('/api/fetch_technical', {
            token: token,
            industry_name: industryName
        });

        document.querySelectorAll('input[name="technical-signal"]').forEach(cb => {
            cb.checked = false;
            const optDiv = cb.closest('.signal-option');
            if (optDiv) optDiv.classList.remove('selected');
        });

        if (data.signals && data.signals.length > 0) {
            data.signals.forEach(sig => {
                document.querySelectorAll('input[name="technical-signal"]').forEach(cb => {
                    if (cb.value === sig.signal_type) {
                        cb.checked = true;
                        const optDiv = cb.closest('.signal-option');
                        if (optDiv) optDiv.classList.add('selected');
                    }
                });
            });

            const sigNames = data.signals.map(s => s.signal_type).join('、');
            showFetchStatus('technical-fetch-status',
                `✅ 检测到 ${data.signals.length} 个信号：${sigNames}`,
                'success');
        } else {
            showFetchStatus('technical-fetch-status',
                'ℹ️ 当前未检测到技术信号（1020起爆点/龙回头/意外大跌抄底）',
                'info');
        }

        if (data.metrics && Object.keys(data.metrics).length > 0) {
            const m = data.metrics;
            showFetchStatus('technical-fetch-status',
                `✅ 技术指标：收盘${m.close} | MA10:${m.ma10} | MA20:${m.ma20} | 偏离MA20:${m.deviation_ma20}% | ${data.reason}`,
                'success');
        }

        saveTokenToStorage(token);
    } catch (e) {
        showFetchStatus('technical-fetch-status', `❌ 检测失败：${e.message}`, 'error');
    } finally {
        setButtonLoading('btn-fetch-technical', false);
    }
}

async function fetchAllData() {
    const token = getToken();
    const industryName = getIndustryName();

    if (!token) { showAlert('请先输入Tushare Token', 'warning'); return; }
    if (!industryName) { showAlert('请先输入行业名称', 'warning'); return; }

    setButtonLoading('btn-fetch-all', true);

    const statusEl = document.getElementById('connection-status');
    statusEl.style.display = 'block';
    statusEl.className = 'connection-status status-loading';
    statusEl.textContent = '⏳ 正在获取全部数据...';

    try {
        const data = await apiCall('/api/fetch_all', {
            token: token,
            industry_name: industryName
        });

        const ind = data.industry;
        document.getElementById('industry-type').value = ind.industry_type;
        document.getElementById('cycle-phase').value = ind.cycle_phase;

        const cap = data.capital;
        document.getElementById('etf-subscription').value = cap.etf_net_subscription;
        if (cap.fund_position_available) {
            document.getElementById('fund-position-change').value = cap.fund_position_change;
        }

        const tech = data.technical;
        document.querySelectorAll('input[name="technical-signal"]').forEach(cb => {
            cb.checked = false;
            const optDiv = cb.closest('.signal-option');
            if (optDiv) optDiv.classList.remove('selected');
        });
        if (tech.signals && tech.signals.length > 0) {
            tech.signals.forEach(sig => {
                document.querySelectorAll('input[name="technical-signal"]').forEach(cb => {
                    if (cb.value === sig.signal_type) {
                        cb.checked = true;
                        const optDiv = cb.closest('.signal-option');
                        if (optDiv) optDiv.classList.add('selected');
                    }
                });
            });
        }

        saveTokenToStorage(token);

        const sigCount = tech.signals ? tech.signals.length : 0;
        statusEl.className = 'connection-status status-success';
        statusEl.innerHTML = `
            ✅ 全部数据已填充！<br>
            📊 行业类型：${ind.industry_type} | 周期阶段：${ind.cycle_phase}（${ind.phase_reason}）<br>
            💰 ETF净申购：${cap.etf_net_subscription}亿 | 公募仓位：${cap.fund_position_available ? '已获取' : '需手动填写'}<br>
            📉 技术信号：${sigCount}个（${tech.reason}）
        `;
        showAlert('全部数据已自动填充！请检查并补充政策面信息后点击"开始评分"', 'success');
    } catch (e) {
        statusEl.className = 'connection-status status-error';
        statusEl.textContent = `❌ 获取失败：${e.message}`;
        showAlert(`获取失败：${e.message}`, 'error');
    } finally {
        setButtonLoading('btn-fetch-all', false);
    }
}

/**
 * 设置标签页导航
 */
function setupTabNavigation() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');

            // 移除所有active状态
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // 添加active状态到当前标签
            this.classList.add('active');
            document.getElementById(`tab-${targetTab}`).classList.add('active');
        });
    });
}

/**
 * 设置表单交互
 */
function setupFormInteractions() {
    // 政策复选框联动
    const supportPolicyCheckbox = document.getElementById('has-support-policy');
    const catalystEventCheckbox = document.getElementById('has-catalyst-event');

    if (supportPolicyCheckbox) {
        supportPolicyCheckbox.addEventListener('change', function() {
            const detailDiv = document.getElementById('policy-detail-1');
            if (this.checked) {
                detailDiv.classList.add('active');
            } else {
                detailDiv.classList.remove('active');
                document.getElementById('policy-description').value = '';
            }
        });
    }

    if (catalystEventCheckbox) {
        catalystEventCheckbox.addEventListener('change', function() {
            const detailDiv = document.getElementById('policy-detail-2');
            if (this.checked) {
                detailDiv.classList.add('active');
            } else {
                detailDiv.classList.remove('active');
                document.getElementById('catalyst-description').value = '';
            }
        });
    }

    // 技术信号选项样式切换
    const signalCheckboxes = document.querySelectorAll('input[name="technical-signal"]');
    signalCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const optionDiv = this.closest('.signal-option');
            if (this.checked) {
                optionDiv.classList.add('selected');
            } else {
                optionDiv.classList.remove('selected');
            }
        });

        // 点击整个卡片也能选中
        const optionDiv = checkbox.closest('.signal-option');
        if (optionDiv) {
            optionDiv.addEventListener('click', function(e) {
                if (e.target.type !== 'checkbox') {
                    checkbox.checked = !checkbox.checked;
                    checkbox.dispatchEvent(new Event('change'));
                }
            });
        }
    });
}

/**
 * 收集表单数据
 */
function collectFormData() {
    const industryName = document.getElementById('industry-name').value.trim();
    const industryType = document.getElementById('industry-type').value;
    const cyclePhase = document.getElementById('cycle-phase').value;
    
    // 验证必填字段
    if (!industryName) {
        showAlert('请输入行业名称', 'warning');
        return null;
    }
    if (!industryType || !cyclePhase) {
        showAlert('请完整选择行业类型和周期阶段', 'warning');
        return null;
    }

    // 收集技术信号
    const technicalSignals = [];
    document.querySelectorAll('input[name="technical-signal"]:checked').forEach(checkbox => {
        technicalSignals.push(checkbox.value);
    });

    return {
        industryName,
        industryType,
        cyclePhase,
        hasSupportPolicy: document.getElementById('has-support-policy').checked,
        policyDescription: document.getElementById('policy-description').value.trim(),
        hasCatalystEvent: document.getElementById('has-catalyst-event').checked,
        catalystDescription: document.getElementById('catalyst-description').value.trim(),
        etfNetSubscription: document.getElementById('etf-subscription').value || '0',
        fundPositionChange: document.getElementById('fund-position-change').value || '0',
        technicalSignals
    };
}

/**
 * 计算评分
 */
function calculateScore() {
    const inputData = collectFormData();
    if (!inputData) return;

    try {
        currentScoreResult = scoringEngine.calculateScore(inputData);
        displayScoreResult(currentScoreResult);
        
        // 切换到结果页面
        switchToTab('result');
        
        // 保存到本地存储
        saveToLocalStorage(currentScoreResult);
        
    } catch (error) {
        console.error('评分计算错误:', error);
        showAlert('评分计算出错，请检查输入数据', 'error');
    }
}

/**
 * 显示评分结果
 */
function displayScoreResult(result) {
    const container = document.getElementById('score-result');
    const emptyState = document.getElementById('empty-result');

    emptyState.style.display = 'none';
    container.style.display = 'block';

    // 确定信号等级样式类
    let signalClass;
    if (result.totalScore >= 4) {
        signalClass = 'signal-strong-buy';
    } else if (result.totalScore >= 3) {
        signalClass = 'signal-latent';
    } else {
        signalClass = 'signal-wait';
    }

    // 构建HTML
    let html = `
        <div class="score-header">
            <div class="score-industry-name">${escapeHtml(result.industryName)}</div>
            <div class="total-score-circle">
                <div class="score-number">${result.totalScore}</div>
                <div class="score-total">/ 4 分</div>
            </div>
            <div class="signal-badge ${signalClass}">${result.signalLevel}</div>
        </div>

        <div class="dimension-scores-grid">
    `;

    // 四个维度的评分卡片
    const dimensions = ['prosperity', 'policy', 'capital', 'technical'];
    const dimIcons = ['📊', '🏛️', '💰', '📉'];

    dimensions.forEach((dim, index) => {
        const dimData = result.dimensions[dim];
        const isPassed = dimData.score === 1;
        const statusClass = isPassed ? 'passed' : 'failed';

        html += `
            <div class="dimension-card ${statusClass}">
                <div class="dim-name">
                    <span>${dimIcons[index]} ${dimData.name}</span>
                    <div class="dim-score-badge ${statusClass}">${dimData.score}</div>
                </div>
                <div class="dim-reason">${escapeHtml(dimData.reason)}</div>
            </div>
        `;
    });

    html += `
        </div>

        <div class="action-advice-box">
            <div class="action-advice-title">💡 操作建议</div>
            <div class="action-advice-text">${result.actionAdvice}</div>
        </div>

        <div style="text-align: center; margin-top: 25px; color: #6c757d; font-size: 0.9em;">
            评估时间：${result.timestamp}
        </div>
    `;

    container.innerHTML = html;

    // 添加动画效果
    container.style.animation = 'none';
    container.offsetHeight; // 触发重绘
    container.style.animation = 'fadeIn 0.5s ease-in-out';
}

/**
 * 加入对比列表
 */
function addToComparison() {
    if (!currentScoreResult) {
        showAlert('请先进行评分', 'warning');
        return;
    }

    // 检查是否已存在
    const exists = comparisonList.some(item => item.industryName === currentScoreResult.industryName);
    if (exists) {
        showAlert('该行业已在对比列表中', 'info');
        return;
    }

    comparisonList.push({...currentScoreResult});
    updateComparisonTable();
    saveComparisonToStorage();

    showAlert(`"${currentScoreResult.industryName}" 已加入对比列表`, 'success');
}

/**
 * 更新对比表格
 */
function updateComparisonTable() {
    const tbody = document.getElementById('comparison-tbody');
    const emptyState = document.getElementById('empty-comparison');
    const statsSection = document.getElementById('stats-section');

    if (comparisonList.length === 0) {
        tbody.innerHTML = '';
        emptyState.style.display = 'block';
        statsSection.style.display = 'none';
        return;
    }

    emptyState.style.display = 'none';
    statsSection.style.display = 'block';

    // 按总分排序
    const sorted = [...comparisonList].sort((a, b) => b.totalScore - a.totalScore);

    let html = '';
    sorted.forEach((item, index) => {
        const levelClass = getLevelClass(item.totalScore);
        
        html += `
            <tr>
                <td><strong>${index + 1}</strong></td>
                <td><strong>${escapeHtml(item.industryName)}</strong></td>
                <td class="score-cell ${item.dimensions.prosperity.score === 1 ? 'score-passed' : 'score-failed'}">
                    ${item.dimensions.prosperity.score}分
                </td>
                <td class="score-cell ${item.dimensions.policy.score === 1 ? 'score-passed' : 'score-failed'}">
                    ${item.dimensions.policy.score}分
                </td>
                <td class="score-cell ${item.dimensions.capital.score === 1 ? 'score-passed' : 'score-failed'}">
                    ${item.dimensions.capital.score}分
                </td>
                <td class="score-cell ${item.dimensions.technical.score === 1 ? 'score-passed' : 'score-failed'}">
                    ${item.dimensions.technical.score}分
                </td>
                <td class="total-cell">${item.totalScore}</td>
                <td><span class="level-badge ${levelClass}">${item.signalLevel}</span></td>
                <td>
                    <button class="delete-btn" onclick="removeFromComparison('${escapeHtml(item.industryName)}')">
                        删除
                    </button>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;

    // 更新统计信息
    updateStatistics(sorted);
}

/**
 * 获取等级样式类
 */
function getLevelClass(score) {
    if (score >= 4) return 'level-strong';
    if (score >= 3) return 'level-latent';
    return 'level-weak';
}

/**
 * 更新统计信息
 */
function updateStatistics(sortedResults) {
    const count4 = sortedResults.filter(r => r.totalScore >= 4).length;
    const count3 = sortedResults.filter(r => r.totalScore === 3).length;
    const count2 = sortedResults.filter(r => r.totalScore <= 2).length;

    document.getElementById('count-4').textContent = `${count4}个`;
    document.getElementById('count-3').textContent = `${count3}个`;
    document.getElementById('count-2').textContent = `${count2}个`;
}

/**
 * 从对比列表中移除
 */
function removeFromComparison(industryName) {
    comparisonList = comparisonList.filter(item => item.industryName !== industryName);
    updateComparisonTable();
    saveComparisonToStorage();
    showAlert(`"${industryName}" 已从对比列表移除`, 'info');
}

/**
 * 清空对比列表
 */
function clearComparison() {
    if (comparisonList.length === 0) {
        showAlert('对比列表已经是空的', 'info');
        return;
    }

    if (confirm('确定要清空整个对比列表吗？')) {
        comparisonList = [];
        updateComparisonTable();
        saveComparisonToStorage();
        showAlert('对比列表已清空', 'success');
    }
}

/**
 * 清空表单
 */
function clearForm() {
    if (!confirm('确定要清空所有输入内容吗？')) return;

    document.getElementById('industry-name').value = '';
    document.getElementById('industry-type').selectedIndex = 0;
    document.getElementById('cycle-phase').selectedIndex = 0;
    document.getElementById('has-support-policy').checked = false;
    document.getElementById('policy-description').value = '';
    document.getElementById('has-catalyst-event').checked = false;
    document.getElementById('catalyst-description').value = '';
    document.getElementById('etf-subscription').value = '';
    document.getElementById('fund-position-change').value = '';

    // 取消所有技术信号选择
    document.querySelectorAll('input[name="technical-signal"]').forEach(checkbox => {
        checkbox.checked = false;
        const optionDiv = checkbox.closest('.signal-option');
        if (optionDiv) optionDiv.classList.remove('selected');
    });

    // 隐藏子表单
    document.getElementById('policy-detail-1').classList.remove('active');
    document.getElementById('policy-detail-2').classList.remove('active');

    showAlert('表单已清空', 'success');
}

/**
 * 切换到指定标签页
 */
function switchToTab(tabName) {
    const buttons = document.querySelectorAll('.tab-btn');
    const contents = document.querySelectorAll('.tab-content');

    buttons.forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-tab') === tabName);
    });

    contents.forEach(content => {
        content.classList.toggle('active', content.id === `tab-${tabName}`);
    });
}

/**
 * 显示提示消息
 */
function showAlert(message, type = 'info') {
    // 创建提示元素
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        border-radius: 10px;
        color: white;
        font-weight: 600;
        z-index: 10000;
        animation: slideInRight 0.3s ease;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    `;

    // 根据类型设置背景色
    const colors = {
        success: '#28a745',
        warning: '#ffc107',
        error: '#dc3545',
        info: '#17a2b8'
    };
    alert.style.background = colors[type] || colors.info;
    alert.textContent = message;

    document.body.appendChild(alert);

    // 3秒后自动消失
    setTimeout(() => {
        alert.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 300);
    }, 3000);
}

/**
 * HTML转义（防止XSS）
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 保存评分结果到localStorage
 */
function saveToLocalStorage(result) {
    try {
        const history = JSON.parse(localStorage.getItem('scoringHistory') || '[]');
        history.unshift(result);
        // 只保留最近50条记录
        if (history.length > 50) history.pop();
        localStorage.setItem('scoringHistory', JSON.stringify(history));
    } catch (e) {
        console.error('保存到本地存储失败:', e);
    }
}

/**
 * 保存对比列表到localStorage
 */
function saveComparisonToStorage() {
    try {
        localStorage.setItem('comparisonList', JSON.stringify(comparisonList));
    } catch (e) {
        console.error('保存对比列表失败:', e);
    }
}

/**
 * 从localStorage加载数据
 */
function loadFromLocalStorage() {
    try {
        const saved = localStorage.getItem('comparisonList');
        if (saved) {
            comparisonList = JSON.parse(saved);
            updateComparisonTable();
        }
    } catch (e) {
        console.error('从本地存储加载失败:', e);
    }
}

// 添加动画样式
const styleSheet = document.createElement('style');
styleSheet.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(styleSheet);
