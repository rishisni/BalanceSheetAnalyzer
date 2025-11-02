import { useState, useEffect } from 'react';
import { companyAPI } from '../../services/api';

const CompanySelector = ({ onSelectCompany }) => {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCompany, setSelectedCompany] = useState(null);

  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    try {
      const response = await companyAPI.getCompanies();
      // Handle both paginated and non-paginated responses
      const companiesData = response.data.results || response.data || [];
      
      if (companiesData.length > 0) {
        setCompanies(companiesData);
        setSelectedCompany(companiesData[0].id);
        onSelectCompany(companiesData[0]);
      } else {
        setCompanies([]);
      }
    } catch (error) {
      console.error('Error loading companies:', error);
      console.error('Error details:', error.response?.data);
      setCompanies([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (company) => {
    setSelectedCompany(company.id);
    onSelectCompany(company);
  };

  if (loading) {
    return <div className="text-center py-4">Loading companies...</div>;
  }

  if (companies.length === 0 && !loading) {
    return (
      <div className="bg-white shadow rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-3">Select Company</h3>
        <div className="text-center py-4 text-gray-500">
          <p className="mb-2">No companies available</p>
          <p className="text-sm">Please contact an administrator to add companies.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-4">
      <h3 className="text-lg font-semibold mb-3">Select Company</h3>
      <div className="space-y-2">
        {companies.map((company) => (
          <button
            key={company.id}
            onClick={() => handleSelect(company)}
            className={`w-full text-left px-4 py-2 rounded-md transition-colors ${
              selectedCompany === company.id
                ? 'bg-indigo-100 text-indigo-700 font-medium'
                : 'bg-gray-50 hover:bg-gray-100 text-gray-700'
            }`}
          >
            {company.name}
          </button>
        ))}
      </div>
    </div>
  );
};

export default CompanySelector;

