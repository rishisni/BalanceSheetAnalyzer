import { useState, useEffect } from 'react';
import { companyAPI } from '../../services/api';

const CreateCompany = ({ onCompanyCreated }) => {
  const [formData, setFormData] = useState({
    name: '',
    parent_company: '',
  });
  const [parentCompanies, setParentCompanies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    loadParentCompanies();
  }, []);

  const loadParentCompanies = async () => {
    try {
      const response = await companyAPI.getCompanies();
      const companies = response.data.results || response.data || [];
      // Filter to show only companies without parents (potential parents)
      setParentCompanies(companies.filter(c => !c.parent_company));
    } catch (error) {
      console.error('Error loading companies:', error);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setMessage({ type: '', text: '' });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const data = {
        name: formData.name,
      };
      
      if (formData.parent_company) {
        data.parent_company = parseInt(formData.parent_company);
      }

      const response = await companyAPI.createCompany(data);
      setMessage({ type: 'success', text: `Company "${response.data.name}" created successfully!` });
      setFormData({ name: '', parent_company: '' });
      
      if (onCompanyCreated) {
        onCompanyCreated(response.data);
      }
      
      // Reload parent companies list
      loadParentCompanies();
    } catch (error) {
      const errorMessage = error.response?.data;
      if (typeof errorMessage === 'object') {
        const errorText = Object.values(errorMessage).flat().join(', ');
        setMessage({ type: 'error', text: errorText || 'Failed to create company' });
      } else {
        setMessage({ type: 'error', text: 'Failed to create company. Please try again.' });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">Create New Company</h3>
      
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
            Company Name *
          </label>
          <input
            type="text"
            name="name"
            required
            value={formData.name}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Enter company name"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Parent Company (Optional)
          </label>
          <select
            name="parent_company"
            value={formData.parent_company}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">None (Parent Company)</option>
            {parentCompanies.map((company) => (
              <option key={company.id} value={company.id}>
                {company.name}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-gray-500">
            Select a parent company if this is a subsidiary
          </p>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Creating...' : 'Create Company'}
        </button>
      </form>
    </div>
  );
};

export default CreateCompany;

