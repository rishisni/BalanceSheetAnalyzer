import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import CompanySelector from './CompanySelector';
import BalanceSheetUpload from '../BalanceSheet/BalanceSheetUpload';
import ChatInterface from '../Chat/ChatInterface';
import Analytics from '../Analytics/Analytics';
import CreateCompany from '../Companies/CreateCompany';

const Dashboard = () => {
  const { user } = useAuth();
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [activeTab, setActiveTab] = useState('chat');
  const [refreshCompanies, setRefreshCompanies] = useState(0);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-600">
            Welcome, {user?.username}! Select a company to view its financial analysis.
          </p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar - Company Selector */}
          <div className="lg:col-span-1 space-y-4">
            <CompanySelector 
              key={refreshCompanies}
              onSelectCompany={setSelectedCompany} 
            />
            
            {/* Company Creation (Group Owners only) */}
            {user?.role === 'GROUP_OWNER' && (
              <CreateCompany 
                onCompanyCreated={(newCompany) => {
                  setRefreshCompanies(prev => prev + 1);
                  setSelectedCompany(newCompany);
                  setActiveTab('chat');
                }}
              />
            )}
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            {selectedCompany ? (
              <div className="bg-white shadow rounded-lg">
                {/* Tabs */}
                <div className="border-b border-gray-200">
                  <nav className="flex -mb-px">
                    <button
                      onClick={() => setActiveTab('chat')}
                      className={`px-4 py-3 text-sm font-medium ${
                        activeTab === 'chat'
                          ? 'text-indigo-600 border-b-2 border-indigo-600'
                          : 'text-gray-600 hover:text-gray-800'
                      }`}
                    >
                      Chat Analysis
                    </button>
                    <button
                      onClick={() => setActiveTab('analytics')}
                      className={`px-4 py-3 text-sm font-medium ${
                        activeTab === 'analytics'
                          ? 'text-indigo-600 border-b-2 border-indigo-600'
                          : 'text-gray-600 hover:text-gray-800'
                      }`}
                    >
                      Analytics
                    </button>
                    {user?.role === 'ANALYST' && (
                      <button
                        onClick={() => setActiveTab('upload')}
                        className={`px-4 py-3 text-sm font-medium ${
                          activeTab === 'upload'
                            ? 'text-indigo-600 border-b-2 border-indigo-600'
                            : 'text-gray-600 hover:text-gray-800'
                        }`}
                      >
                        Upload Balance Sheet
                      </button>
                    )}
                  </nav>
                </div>

                {/* Tab Content */}
                <div className="p-6">
                  {activeTab === 'chat' && <ChatInterface companyId={selectedCompany.id} />}
                  {activeTab === 'analytics' && <Analytics companyId={selectedCompany.id} />}
                  {activeTab === 'upload' && <BalanceSheetUpload companyId={selectedCompany.id} />}
                </div>
              </div>
            ) : (
              <div className="bg-white shadow rounded-lg p-8 text-center text-gray-500">
                Please select a company to get started
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

