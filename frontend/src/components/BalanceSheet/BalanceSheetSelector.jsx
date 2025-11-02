import { useState, useEffect } from 'react';
import { balanceSheetAPI } from '../../services/api';

const BalanceSheetSelector = ({ companyId, onSelectionChange }) => {
  const [balanceSheets, setBalanceSheets] = useState([]);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (companyId) {
      loadBalanceSheets();
    }
  }, [companyId]);

  useEffect(() => {
    // Auto-select all sheets by default
    if (balanceSheets.length > 0 && selectedIds.size === 0) {
      const allIds = new Set(balanceSheets.map(bs => bs.id));
      setSelectedIds(allIds);
      if (onSelectionChange) {
        onSelectionChange(allIds);
      }
    }
  }, [balanceSheets]);

  const loadBalanceSheets = async () => {
    try {
      const response = await balanceSheetAPI.getBalanceSheets(companyId);
      const sheets = response.data.results || response.data || [];
      // Sort by year descending
      sheets.sort((a, b) => b.year - a.year || (b.quarter || '').localeCompare(a.quarter || ''));
      setBalanceSheets(sheets);
    } catch (error) {
      console.error('Error loading balance sheets:', error);
      setBalanceSheets([]);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = (id) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
    if (onSelectionChange) {
      onSelectionChange(newSelected);
    }
  };

  const handleSelectAll = () => {
    const allIds = new Set(balanceSheets.map(bs => bs.id));
    setSelectedIds(allIds);
    if (onSelectionChange) {
      onSelectionChange(allIds);
    }
  };

  const handleDeselectAll = () => {
    setSelectedIds(new Set());
    if (onSelectionChange) {
      onSelectionChange(new Set());
    }
  };

  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg p-4">
        <div className="text-center py-4 text-gray-500">Loading balance sheets...</div>
      </div>
    );
  }

  if (balanceSheets.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-3 text-gray-700">Available Balance Sheets</h3>
        <div className="text-center py-4 text-gray-500">
          <p className="mb-2">No balance sheets uploaded</p>
          <p className="text-sm">Upload balance sheets to see analytics</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-4">
      <h3 className="text-lg font-semibold mb-3 text-gray-700">
        Available Balance Sheets
      </h3>
      <p className="text-xs text-gray-500 mb-3">
        Select sheets to analyze (showing selected: {selectedIds.size}/{balanceSheets.length})
      </p>
      
      <div className="space-y-2 max-h-60 overflow-y-auto mb-3">
        {balanceSheets.map((sheet) => (
          <label
            key={sheet.id}
            className={`flex items-center px-3 py-2 rounded-md cursor-pointer transition-colors ${
              selectedIds.has(sheet.id)
                ? 'bg-indigo-50 hover:bg-indigo-100'
                : 'hover:bg-gray-50'
            }`}
          >
            <input
              type="checkbox"
              checked={selectedIds.has(sheet.id)}
              onChange={() => handleToggle(sheet.id)}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <span className="ml-3 text-sm text-gray-700">
              {sheet.year} {sheet.quarter ? `Q${sheet.quarter}` : ''}
              <span className="text-xs text-gray-500 ml-2">
                {new Date(sheet.uploaded_at).toLocaleDateString()}
              </span>
            </span>
          </label>
        ))}
      </div>

      <div className="flex space-x-2 border-t pt-3">
        <button
          onClick={handleSelectAll}
          className="flex-1 px-3 py-2 text-xs font-medium text-indigo-600 bg-indigo-50 rounded-md hover:bg-indigo-100 transition-colors"
        >
          Select All
        </button>
        <button
          onClick={handleDeselectAll}
          className="flex-1 px-3 py-2 text-xs font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
        >
          Deselect All
        </button>
      </div>
    </div>
  );
};

export default BalanceSheetSelector;

