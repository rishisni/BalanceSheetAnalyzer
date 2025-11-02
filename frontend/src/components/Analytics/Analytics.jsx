import { useState, useEffect } from 'react';
import { balanceSheetAPI } from '../../services/api';
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import BalanceSheetSelector from '../BalanceSheet/BalanceSheetSelector';
import { formatCurrency, formatPercentage, formatRatio } from '../../utils/formatNumbers';

const Analytics = ({ companyId }) => {
  const [balanceSheets, setBalanceSheets] = useState([]);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedMetric, setSelectedMetric] = useState('revenue');
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [activeView, setActiveView] = useState('overview'); // overview, ratios, growth, cashflow

  useEffect(() => {
    loadBalanceSheets();
  }, [companyId]);

  useEffect(() => {
    if (companyId) {
      loadAnalytics();
    }
  }, [companyId, selectedIds]);

  const loadBalanceSheets = async () => {
    try {
      const response = await balanceSheetAPI.getBalanceSheets(companyId);
      const sheets = response.data.results || response.data || [];
      setBalanceSheets(sheets);
      // Auto-select all by default
      if (sheets.length > 0 && selectedIds.size === 0) {
        setSelectedIds(new Set(sheets.map(s => s.id)));
      }
    } catch (error) {
      console.error('Error loading balance sheets:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAnalytics = async () => {
    try {
      const selectedIdsArray = selectedIds.size > 0 ? Array.from(selectedIds) : [];
      const response = await balanceSheetAPI.getAnalyticsSummary(companyId, selectedIdsArray);
      setAnalyticsData(response.data);
    } catch (error) {
      console.error('Error loading analytics:', error);
    }
  };

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1', '#d084d0'];

  // Custom tooltip with formatted numbers
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-300 rounded-lg shadow-lg">
          <p className="font-semibold mb-2">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }} className="text-sm">
              {entry.name}: {formatCurrency(entry.value)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // Status badge component
  const StatusBadge = ({ status, label }) => {
    const statusColors = {
      good: 'bg-green-100 text-green-800',
      attention: 'bg-yellow-100 text-yellow-800',
      bad: 'bg-red-100 text-red-800',
      moderate: 'bg-orange-100 text-orange-800',
      high: 'bg-red-100 text-red-800',
      unknown: 'bg-gray-100 text-gray-800',
    };
    
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${statusColors[status] || statusColors.unknown}`}>
        {label}
      </span>
    );
  };

  // KPI Card Component
  const KPICard = ({ title, value, growth, subtitle, status }) => {
    const formattedValue = typeof value === 'number' ? formatCurrency(value) : (value || 'N/A');
    const growthDisplay = growth !== null && growth !== undefined ? formatPercentage(growth) : null;
    const isPositive = growth > 0;

    return (
      <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-gray-600">{title}</h3>
          {status && <StatusBadge status={status} label={status} />}
        </div>
        <div className="text-2xl font-bold text-gray-900 mb-1">{formattedValue}</div>
        {subtitle && <div className="text-xs text-gray-500 mb-1">{subtitle}</div>}
        {growthDisplay && (
          <div className={`text-sm ${isPositive ? 'text-green-600' : 'text-red-600'} flex items-center`}>
            <span className="mr-1">{isPositive ? '↑' : '↓'}</span>
            {growthDisplay}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return <div className="text-center py-8">Loading analytics...</div>;
  }

  if (!analyticsData || analyticsData.analytics.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold mb-4">Financial Analytics</h2>
          <BalanceSheetSelector 
            companyId={companyId}
            onSelectionChange={setSelectedIds}
          />
        </div>
        <div className="text-center py-8 text-gray-500">
          No balance sheet data available for analytics
        </div>
      </div>
    );
  }

  const { analytics, kpis } = analyticsData;
  const chartData = analytics.map(item => ({
    ...item,
    displayYear: item.period,
    assetsGrowth: item.growth?.assets || 0,
    revenueGrowth: item.growth?.revenue || 0,
  }));

  return (
    <div className="space-y-6">
      {/* Header with Selector */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Financial Analytics</h2>
        <BalanceSheetSelector 
          companyId={companyId}
          onSelectionChange={(ids) => {
            setSelectedIds(ids);
            // Reload analytics when selection changes
            const idsArray = ids.size > 0 ? Array.from(ids) : [];
            balanceSheetAPI.getAnalyticsSummary(companyId, idsArray)
              .then(response => setAnalyticsData(response.data))
              .catch(err => console.error('Error loading analytics:', err));
          }}
        />
      </div>

      {/* KPI Dashboard Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Assets"
          value={kpis.total_assets}
          growth={kpis.assets_growth}
          subtitle="Latest period"
        />
        <KPICard
          title="Revenue"
          value={kpis.revenue}
          growth={kpis.revenue_growth}
          subtitle="Latest period"
        />
        <KPICard
          title="Current Ratio"
          value={kpis.current_ratio}
          subtitle={kpis.current_ratio ? formatRatio(kpis.current_ratio) : 'N/A'}
          status={analytics[analytics.length - 1]?.current_ratio_status}
        />
        <KPICard
          title="Debt-to-Equity"
          value={kpis.debt_to_equity}
          subtitle={kpis.debt_to_equity ? formatRatio(kpis.debt_to_equity) : 'N/A'}
          status={analytics[analytics.length - 1]?.debt_to_equity_status}
        />
        {kpis.roe && (
          <KPICard
            title="ROE"
            value={kpis.roe}
            subtitle={formatPercentage(kpis.roe)}
          />
        )}
        {kpis.working_capital && (
          <KPICard
            title="Working Capital"
            value={kpis.working_capital}
            subtitle="Current Assets - Current Liabilities"
          />
        )}
      </div>

      {/* View Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex -mb-px space-x-4">
          <button
            onClick={() => setActiveView('overview')}
            className={`px-4 py-2 text-sm font-medium ${
              activeView === 'overview'
                ? 'text-indigo-600 border-b-2 border-indigo-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveView('ratios')}
            className={`px-4 py-2 text-sm font-medium ${
              activeView === 'ratios'
                ? 'text-indigo-600 border-b-2 border-indigo-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Financial Ratios
          </button>
          <button
            onClick={() => setActiveView('growth')}
            className={`px-4 py-2 text-sm font-medium ${
              activeView === 'growth'
                ? 'text-indigo-600 border-b-2 border-indigo-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Growth Analysis
          </button>
          {analytics.some(a => a.operating_cash_flow || a.net_cash_flow) && (
            <button
              onClick={() => setActiveView('cashflow')}
              className={`px-4 py-2 text-sm font-medium ${
                activeView === 'cashflow'
                  ? 'text-indigo-600 border-b-2 border-indigo-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              Cash Flow
            </button>
          )}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeView === 'overview' && (
        <div className="space-y-6">
          {/* Metric Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Metric
            </label>
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="revenue">Revenue</option>
              <option value="total_assets">Total Assets</option>
              <option value="total_liabilities">Total Liabilities</option>
              <option value="total_equity">Total Equity</option>
              <option value="current_assets">Current Assets</option>
              <option value="working_capital">Working Capital</option>
            </select>
          </div>

          {/* Trend Analysis - Area Chart */}
          <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
            <h3 className="text-lg font-medium mb-4">Trend Analysis</h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorMetric" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="displayYear" />
                <YAxis tickFormatter={(value) => formatCurrency(value, 0)} />
                <Tooltip content={<CustomTooltip />} />
                <Area 
                  type="monotone" 
                  dataKey={selectedMetric} 
                  stroke="#8884d8" 
                  fillOpacity={1} 
                  fill="url(#colorMetric)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Financial Comparison - Bar Chart */}
          <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
            <h3 className="text-lg font-medium mb-4">Financial Comparison</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="displayYear" />
                <YAxis tickFormatter={(value) => formatCurrency(value, 0)} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar dataKey="revenue" fill="#8884d8" name="Revenue" />
                <Bar dataKey="total_assets" fill="#82ca9d" name="Total Assets" />
                <Bar dataKey="total_liabilities" fill="#ffc658" name="Total Liabilities" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Composition - Pie Chart */}
          {chartData.length > 0 && (
            <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
              <h3 className="text-lg font-medium mb-4">
                Composition - {chartData[chartData.length - 1].displayYear}
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Assets', value: chartData[chartData.length - 1].total_assets },
                      { name: 'Liabilities', value: chartData[chartData.length - 1].total_liabilities },
                      { name: 'Equity', value: chartData[chartData.length - 1].total_equity },
                    ]}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {[0, 1, 2].map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Financial Ratios Tab */}
      {activeView === 'ratios' && (
        <div className="space-y-6">
          <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
            <h3 className="text-lg font-medium mb-4">Financial Ratios Over Time</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="displayYear" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="current_ratio" 
                  stroke="#8884d8" 
                  strokeWidth={2}
                  name="Current Ratio"
                  connectNulls
                />
                <Line 
                  type="monotone" 
                  dataKey="debt_to_equity" 
                  stroke="#82ca9d" 
                  strokeWidth={2}
                  name="Debt-to-Equity"
                  connectNulls
                />
                {analytics.some(a => a.roe) && (
                  <Line 
                    type="monotone" 
                    dataKey="roe" 
                    stroke="#ffc658" 
                    strokeWidth={2}
                    name="ROE (%)"
                    connectNulls
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Ratio Status Table */}
          <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
            <h3 className="text-lg font-medium mb-4">Ratio Status</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Period</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Current Ratio</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Debt-to-Equity</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">ROE</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Asset Turnover</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {chartData.map((item, idx) => (
                    <tr key={idx}>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{item.displayYear}</td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {item.current_ratio ? formatRatio(item.current_ratio) : 'N/A'}
                        {item.current_ratio_status && (
                          <StatusBadge status={item.current_ratio_status} label="" className="ml-2" />
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {item.debt_to_equity ? formatRatio(item.debt_to_equity) : 'N/A'}
                        {item.debt_to_equity_status && (
                          <StatusBadge status={item.debt_to_equity_status} label="" className="ml-2" />
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {item.roe ? formatPercentage(item.roe) : 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {item.asset_turnover ? formatRatio(item.asset_turnover, 3) : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Growth Analysis Tab */}
      {activeView === 'growth' && (
        <div className="space-y-6">
          <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
            <h3 className="text-lg font-medium mb-4">Growth Trends</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="displayYear" />
                <YAxis tickFormatter={(value) => formatPercentage(value)} />
                <Tooltip 
                  formatter={(value) => formatPercentage(value)}
                  labelFormatter={(label) => `Period: ${label}`}
                />
                <Legend />
                <Bar dataKey="assetsGrowth" fill="#8884d8" name="Assets Growth %" />
                <Bar dataKey="revenueGrowth" fill="#82ca9d" name="Revenue Growth %" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Growth Summary */}
          {kpis.revenue_cagr && (
            <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
              <h3 className="text-lg font-medium mb-4">Compound Annual Growth Rate (CAGR)</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Revenue CAGR</p>
                  <p className="text-2xl font-bold text-indigo-600">{formatPercentage(kpis.revenue_cagr)}</p>
                </div>
                {kpis.total_assets_cagr && (
                  <div>
                    <p className="text-sm text-gray-600">Assets CAGR</p>
                    <p className="text-2xl font-bold text-indigo-600">{formatPercentage(kpis.total_assets_cagr)}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Cash Flow Tab */}
      {activeView === 'cashflow' && (
        <div className="space-y-6">
          <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
            <h3 className="text-lg font-medium mb-4">Cash Flow Analysis</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="displayYear" />
                <YAxis tickFormatter={(value) => formatCurrency(value, 0)} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar dataKey="operating_cash_flow" fill="#8884d8" name="Operating" />
                <Bar dataKey="investing_cash_flow" fill="#82ca9d" name="Investing" />
                <Bar dataKey="financing_cash_flow" fill="#ffc658" name="Financing" />
                <Bar dataKey="net_cash_flow" fill="#ff7c7c" name="Net Cash Flow" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};

export default Analytics;
