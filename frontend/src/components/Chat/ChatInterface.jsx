import { useState, useEffect, useRef } from 'react';
import { chatAPI, balanceSheetAPI } from '../../services/api';
import BalanceSheetSelector from '../BalanceSheet/BalanceSheetSelector';

const ChatInterface = ({ companyId }) => {
  const [messages, setMessages] = useState([]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [balanceSheets, setBalanceSheets] = useState([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadHistory();
    loadBalanceSheets();
  }, [companyId]);
  
  const loadBalanceSheets = async () => {
    try {
      const response = await balanceSheetAPI.getBalanceSheets(companyId);
      const sheets = response.data.results || response.data || [];
      setBalanceSheets(sheets);
      // Auto-select all by default
      setSelectedIds(new Set(sheets.map(s => s.id)));
    } catch (error) {
      console.error('Error loading balance sheets:', error);
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadHistory = async () => {
    try {
      const response = await chatAPI.getHistory(companyId);
      setMessages(response.data.reverse());
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputQuery.trim() || loading) return;

    const query = inputQuery.trim();
    setInputQuery('');
    setLoading(true);

    // Add user message immediately
    const userMessage = { query, response: '', created_at: new Date().toISOString() };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await chatAPI.sendQuery({
        company_id: companyId,
        query,
        selected_balance_sheet_ids: selectedIds.size > 0 ? Array.from(selectedIds) : [],
      });
      
      // Update the message with response
      setMessages((prev) =>
        prev.map((msg, idx) =>
          idx === prev.length - 1
            ? { ...msg, response: response.data.response }
            : msg
        )
      );
    } catch (error) {
      setMessages((prev) =>
        prev.map((msg, idx) =>
          idx === prev.length - 1
            ? { ...msg, response: 'Error: Could not get response. Please try again.' }
            : msg
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="space-y-4">
      {/* Balance Sheet Selector */}
      <div>
        <BalanceSheetSelector 
          companyId={companyId}
          onSelectionChange={setSelectedIds}
        />
      </div>

      {/* Chat Interface */}
      <div className="flex flex-col h-[600px] bg-white border border-gray-200 rounded-lg p-4">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            Start a conversation by asking a question about the company's performance
          </div>
        ) : (
          messages.map((message, idx) => (
            <div key={idx} className="space-y-2">
              {/* User message */}
              <div className="flex justify-end">
                <div className="max-w-3xl bg-indigo-100 text-gray-900 rounded-lg px-4 py-2">
                  <p className="text-sm">{message.query}</p>
                </div>
              </div>
              
              {/* AI response */}
              {message.response && (
                <div className="flex justify-start">
                  <div className="max-w-3xl bg-gray-100 text-gray-900 rounded-lg px-4 py-2 whitespace-pre-wrap">
                    <p className="text-sm">{message.response}</p>
                  </div>
                </div>
              )}
              
              {!message.response && loading && idx === messages.length - 1 && (
                <div className="flex justify-start">
                  <div className="max-w-3xl bg-gray-100 text-gray-900 rounded-lg px-4 py-2">
                    <p className="text-sm text-gray-500">Thinking...</p>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="flex space-x-2">
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          placeholder="Ask about company performance..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !inputQuery.trim()}
          className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </form>
      </div>
    </div>
  );
};

export default ChatInterface;

