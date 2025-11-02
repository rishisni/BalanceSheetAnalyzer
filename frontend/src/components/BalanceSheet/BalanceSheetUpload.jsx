import { useState } from 'react';
import { balanceSheetAPI } from '../../services/api';

const BalanceSheetUpload = ({ companyId }) => {
  const [file, setFile] = useState(null);
  const [year, setYear] = useState(new Date().getFullYear());
  const [quarter, setQuarter] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setMessage({ type: 'error', text: 'Please select a PDF file' });
      return;
    }

    setLoading(true);
    setMessage({ type: '', text: '' });

    const formData = new FormData();
    formData.append('pdf_file', file);
    formData.append('company_id', companyId);
    formData.append('year', year);
    if (quarter) {
      formData.append('quarter', quarter);
    }

    try {
      await balanceSheetAPI.upload(formData);
      setMessage({ type: 'success', text: 'Balance sheet uploaded successfully!' });
      setFile(null);
      setQuarter('');
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Failed to upload balance sheet',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Upload Balance Sheet</h2>
      
      {message.text && (
        <div
          className={`mb-4 p-4 rounded-md ${
            message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
          }`}
        >
          {message.text}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            PDF File
          </label>
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setFile(e.target.files[0])}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Year
            </label>
            <input
              type="number"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              required
              min="2000"
              max="2100"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Quarter (Optional)
            </label>
            <select
              value={quarter}
              onChange={(e) => setQuarter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">Not Applicable</option>
              <option value="1">Q1</option>
              <option value="2">Q2</option>
              <option value="3">Q3</option>
              <option value="4">Q4</option>
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Uploading...' : 'Upload Balance Sheet'}
        </button>
      </form>
    </div>
  );
};

export default BalanceSheetUpload;

