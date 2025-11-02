import axiosInstance from '../utils/axiosConfig';

// Auth API
export const authAPI = {
  register: (data) => axiosInstance.post('/auth/register/', data),
  login: (data) => axiosInstance.post('/auth/login/', data),
  getProfile: () => axiosInstance.get('/auth/profile/'),
};

// Company API
export const companyAPI = {
  getCompanies: () => axiosInstance.get('/companies/'),
  getCompany: (id) => axiosInstance.get(`/companies/${id}/`),
  getSubsidiaries: (id) => axiosInstance.get(`/companies/${id}/subsidiaries/`),
  createCompany: (data) => axiosInstance.post('/companies/', data),
  assignAccess: (data) => axiosInstance.post('/companies/assign_access/', data),
};

// Balance Sheet API
export const balanceSheetAPI = {
  upload: (formData) => axiosInstance.post('/balance-sheets/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getBalanceSheets: (companyId) => axiosInstance.get(`/balance-sheets/?company=${companyId}`),
  getBalanceSheet: (id) => axiosInstance.get(`/balance-sheets/${id}/`),
  getAnalytics: (id) => axiosInstance.get(`/balance-sheets/${id}/analytics/`),
  getAnalyticsSummary: (companyId, selectedIds = []) => {
    const params = new URLSearchParams({ company: companyId });
    selectedIds.forEach(id => params.append('ids', id));
    return axiosInstance.get(`/balance-sheets/analytics_summary/?${params.toString()}`);
  },
};

// Chat API
export const chatAPI = {
  sendQuery: (data) => axiosInstance.post('/chat/query/', data),
  getHistory: (companyId) => axiosInstance.get(`/chat/history/?company=${companyId}`),
};

