import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const Home = () => {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Hero Section */}
        <div className="text-center">
          <h1 className="text-5xl font-extrabold text-gray-900 sm:text-6xl">
            Balance Sheet Analyzer
          </h1>
          <p className="mt-6 text-xl text-gray-600 max-w-3xl mx-auto">
            AI-powered financial analysis platform for balance sheet insights.
            Analyze company performance, track trends, and get intelligent recommendations.
          </p>
        </div>

        {/* Features */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <div className="text-indigo-600 text-4xl mb-4">📊</div>
            <h3 className="text-xl font-semibold mb-2">AI-Powered Analysis</h3>
            <p className="text-gray-600">
              Chat with our AI analyst to get insights about company performance,
              growth trends, and financial health.
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-lg">
            <div className="text-indigo-600 text-4xl mb-4">📈</div>
            <h3 className="text-xl font-semibold mb-2">Visual Analytics</h3>
            <p className="text-gray-600">
              Interactive charts and graphs showing revenue, assets, liabilities,
              and equity trends over time.
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-lg">
            <div className="text-indigo-600 text-4xl mb-4">🔒</div>
            <h3 className="text-xl font-semibold mb-2">Role-Based Access</h3>
            <p className="text-gray-600">
              Secure access control for Analysts, CEOs, and Group Owners
              with appropriate permissions.
            </p>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-20 text-center">
          {!isAuthenticated ? (
            <div className="space-x-4">
              <Link
                to="/register"
                className="inline-block px-8 py-3 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 transition-colors shadow-lg"
              >
                Get Started
              </Link>
              <Link
                to="/login"
                className="inline-block px-8 py-3 bg-white text-indigo-600 font-semibold rounded-lg border-2 border-indigo-600 hover:bg-indigo-50 transition-colors"
              >
                Login
              </Link>
            </div>
          ) : (
            <Link
              to="/dashboard"
              className="inline-block px-8 py-3 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 transition-colors shadow-lg"
            >
              Go to Dashboard
            </Link>
          )}
        </div>

        {/* Additional Info */}
        <div className="mt-16 bg-indigo-100 rounded-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-gray-700">
            <div>
              <div className="font-semibold mb-2">1. Upload Balance Sheets</div>
              <p className="text-sm">
                Analysts can upload PDF balance sheets which are automatically processed
                to extract financial data.
              </p>
            </div>
            <div>
              <div className="font-semibold mb-2">2. AI Analysis</div>
              <p className="text-sm">
                Ask questions about company performance, trends, and get intelligent
                AI-powered insights.
              </p>
            </div>
            <div>
              <div className="font-semibold mb-2">3. Visual Insights</div>
              <p className="text-sm">
                View comprehensive analytics with interactive charts showing financial
                metrics over time.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;

