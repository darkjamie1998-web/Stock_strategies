/**
 * 四维行业打分体系 - 评分引擎
 * 完整实现四维评分算法逻辑
 */

class ScoringEngine {
    constructor() {
        this.VALID_CYCLE_PHASES_CYCLICAL = ['底部', '底部反转'];
        this.VALID_CYCLE_PHASES_NON_CYCLICAL = ['成长期', '成熟期'];
        this.DECLINE_PHASES = ['衰退期', '下行周期'];
        
        this.SIGNAL_TYPES = ['意外大跌抄底', '1020起爆点', '龙回头'];
    }

    /**
     * 维度一：评估行业景气度
     * @param {Object} industryData - 行业数据
     * @returns {Object} 评分结果 {score, reason, details}
     */
    scoreProsperity(industryData) {
        const { industryType, cyclePhase } = industryData;
        
        if (!industryType || !cyclePhase) {
            return {
                score: 0,
                reason: '请完整填写行业类型和周期阶段',
                details: { error: 'incomplete_data' }
            };
        }

        const details = {
            industryType,
            cyclePhase
        };

        if (industryType === '周期性') {
            if (this.VALID_CYCLE_PHASES_CYCLICAL.includes(cyclePhase)) {
                return {
                    score: 1,
                    reason: `周期性行业，处于${cyclePhase}阶段`,
                    details
                };
            } else {
                let advice = `周期性行业，但处于${cyclePhase}阶段`;
                if (this.DECLINE_PHASES.includes(cyclePhase)) {
                    advice += ' - 衰退型行业，建议回避';
                }
                return {
                    score: 0,
                    reason: advice,
                    details
                };
            }
        } else if (industryType === '非周期性') {
            if (this.VALID_CYCLE_PHASES_NON_CYCLICAL.includes(cyclePhase)) {
                return {
                    score: 1,
                    reason: `非周期性行业，处于${cyclePhase}`,
                    details
                };
            } else {
                return {
                    score: 0,
                    reason: `非周期性行业，但处于${cyclePhase}阶段`,
                    details
                };
            }
        }

        return {
            score: 0,
            reason: `未知行业类型：${industryType}`,
            details
        };
    }

    /**
     * 维度二：评估政策面
     * @param {Object} policyData - 政策数据
     * @returns {Object} 评分结果
     */
    scorePolicy(policyData) {
        const { hasSupportPolicy, policyDescription, hasCatalystEvent, catalystDescription } = policyData;

        const details = {
            hasSupportPolicy,
            policyDescription,
            hasCatalystEvent,
            catalystDescription
        };

        if (hasSupportPolicy && hasCatalystEvent) {
            const reasons = [];
            reasons.push(policyDescription ? `有支持政策：${policyDescription}` : '有支持政策');
            reasons.push(catalystDescription ? `有催化事件：${catalystDescription}` : '有催化事件');

            return {
                score: 1,
                reason: reasons.join(' & '),
                details
            };
        } else {
            const missing = [];
            if (!hasSupportPolicy) missing.push('无明确支持政策');
            if (!hasCatalystEvent) missing.push('无近期催化事件');

            return {
                score: 0,
                reason: missing.join('；'),
                details
            };
        }
    }

    /**
     * 维度三：评估资金面
     * @param {Object} capitalData - 资金面数据
     * @returns {Object} 评分结果
     */
    scoreCapital(capitalData) {
        const { etfNetSubscription, fundPositionChange } = capitalData;

        const etfPositive = etfNetSubscription > 0;
        const fundStable = fundPositionChange >= 0;

        const details = {
            etfNetSubscription,
            etfPositive,
            fundPositionChange,
            fundStable
        };

        if (etfPositive && fundStable) {
            const reasons = [];
            reasons.push(`ETF净申购>0（${etfNetSubscription.toFixed(2)}亿元）`);
            reasons.push(
                fundPositionChange === 0 
                    ? '公募仓位未降' 
                    : `公募仓位上升（+${fundPositionChange.toFixed(2)}%）`
            );

            return {
                score: 1,
                reason: reasons.join('，'),
                details
            };
        } else {
            const problems = [];
            if (!etfPositive) problems.push(`ETF净申购≤0（${etfNetSubscription.toFixed(2)}亿元）`);
            if (!fundStable) problems.push(`公募仓位下降（${fundPositionChange.toFixed(2)}%）`);

            return {
                score: 0,
                reason: problems.join('；'),
                details
            };
        }
    }

    /**
     * 维度四：评估技术面
     * @param {Array} signals - 技术信号列表
     * @returns {Object} 评分结果
     */
    scoreTechnical(signals) {
        const validSignals = signals.filter(s => this.SIGNAL_TYPES.includes(s));

        const details = {
            signalCount: validSignals.length,
            signals: validSignals
        };

        if (validSignals.length > 0) {
            return {
                score: 1,
                reason: `触发技术信号：${validSignals.join('、')}`,
                details
            };
        } else {
            return {
                score: 0,
                reason: '无技术信号触发',
                details
            };
        }
    }

    /**
     * 执行完整的四维评分
     * @param {Object} inputData - 完整的输入数据
     * @returns {Object} 完整的评分结果
     */
    calculateScore(inputData) {
        const prosperityResult = this.scoreProsperity({
            industryType: inputData.industryType,
            cyclePhase: inputData.cyclePhase
        });

        const policyResult = this.scorePolicy({
            hasSupportPolicy: inputData.hasSupportPolicy,
            policyDescription: inputData.policyDescription,
            hasCatalystEvent: inputData.hasCatalystEvent,
            catalystDescription: inputData.catalystDescription
        });

        const capitalResult = this.scoreCapital({
            etfNetSubscription: parseFloat(inputData.etfNetSubscription) || 0,
            fundPositionChange: parseFloat(inputData.fundPositionChange) || 0
        });

        const technicalResult = this.scoreTechnical(inputData.technicalSignals || []);

        const totalScore = prosperityResult.score + policyResult.score + 
                          capitalResult.score + technicalResult.score;

        let signalLevel, actionAdvice;
        if (totalScore >= 4) {
            signalLevel = '强买入信号';
            actionAdvice = '优先配置，可重仓参与。该行业处于最佳配置时机，可适当提高仓位，重点关注其发展潜力。';
        } else if (totalScore >= 3) {
            signalLevel = '潜伏信号';
            actionAdvice = '具备配置价值，可适度建仓。该行业具备配置价值，可适度建仓等待进一步催化，需持续跟踪评分变化。';
        } else {
            signalLevel = '观望/淘汰';
            actionAdvice = '不具备配置价值，应回避或减仓。该行业当前不具备配置价值，建议回避或及时切换至新晋高分赛道。';
        }

        return {
            industryName: inputData.industryName,
            dimensions: {
                prosperity: { name: '行业景气度', ...prosperityResult },
                policy: { name: '政策面', ...policyResult },
                capital: { name: '资金面', ...capitalResult },
                technical: { name: '技术面', ...technicalResult }
            },
            totalScore,
            signalLevel,
            actionAdvice,
            timestamp: new Date().toLocaleString('zh-CN')
        };
    }
}

// 导出评分引擎实例
const scoringEngine = new ScoringEngine();
