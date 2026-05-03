import { useState, useEffect } from 'react';
import axios from 'axios';
import ResumeUploader from './components/ResumeUploader';
import LinkedInInput from './components/LinkedInInput';
import JobDescriptionPanel from './components/JobDescriptionPanel';
import RankingDashboard from './components/RankingDashboard';
import CandidateInsightsModal from './components/CandidateInsightsModal';
import { FiDownload } from 'react-icons/fi';

const API_BASE = 'http://localhost:8000/api/v1';
const WS_URL = 'ws://localhost:8000/api/v1/ws/rank-updates';

function App() {
  const [jobDescription, setJobDescription] = useState(null);
  const [rankings, setRankings] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [view, setView] = useState('setup');
  const [isExporting, setIsExporting] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  useEffect(() => {
    // Setup WebSocket
    const ws = new WebSocket(WS_URL);
    
    ws.onopen = () => console.log("Connected to WS");
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'rankings_update') {
        setRankings(message.data);
      }
    };
    ws.onclose = () => console.log("Disconnected from WS");

    return () => ws.close();
  }, []);

  const handleJobSubmit = async (job) => {
    try {
      await axios.post(`${API_BASE}/analyze-job`, job);
      setJobDescription(job);
    } catch (err) {
      console.error("Failed to analyze job", err);
    }
  };

  const handleResumeUpload = async (files) => {
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    try {
      setIsAnalyzing(true);
      await axios.post(`${API_BASE}/upload-resumes`, formData);
    } catch (err) {
      console.error("Upload failed", err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleLinkedInSubmit = async (url) => {
    try {
      await axios.post(`${API_BASE}/linkedin-profile`, { url });
    } catch (err) {
      console.error("LinkedIn submission failed", err);
    }
  };

  const handleExportExcel = async () => {
    try {
      setIsExporting(true);
      const response = await axios.get(`${API_BASE}/export-excel`, {
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Extract filename from Content-Disposition header or use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'hiring_report.xlsx';
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^";\n]+)"?/);
        if (match) filename = match[1];
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export failed", err);
      alert("Export failed. Make sure candidates have been analyzed first.");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="container mx-auto p-4 md:p-8 max-w-7xl">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gradient">AI Hiring Intelligence</h1>
          <p className="text-gray-400 text-sm mt-1">Powered by Gemini — Smart candidate screening & ranking</p>
        </div>
        <div className="flex gap-3">
          <div className="text-sm px-4 py-2 glass-card flex items-center gap-2 text-purple-400">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
            Gemini AI
          </div>
          <div className="text-sm px-4 py-2 glass-card flex items-center gap-2 text-green-400">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
            System Online
          </div>
        </div>
      </header>

      {view === 'setup' ? (
        <div className="max-w-3xl mx-auto space-y-8">
          <div className="text-center">
            <h2 className="text-2xl font-semibold text-white">Step 1: Set up hiring criteria</h2>
            <p className="text-gray-400 mt-2">Define the job and add candidates to get started.</p>
          </div>
          
          <JobDescriptionPanel onSubmit={handleJobSubmit} />
          
          <div className="glass-panel p-6">
            <h2 className="text-xl font-semibold mb-4 text-white">Add Candidates</h2>
            <ResumeUploader onUpload={handleResumeUpload} disabled={!jobDescription} />
            <div className="my-4 text-center text-gray-500 text-sm">OR</div>
            <LinkedInInput onSubmit={handleLinkedInSubmit} disabled={!jobDescription} />
          </div>

          {isAnalyzing && (
            <div className="text-center py-6">
              <div className="flex flex-col items-center gap-3">
                <div className="w-10 h-10 border-4 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
                <p className="text-purple-400 text-sm animate-pulse">Gemini is analyzing resumes... This may take a moment.</p>
              </div>
            </div>
          )}

          <div className="text-center pt-4">
            <button 
              onClick={() => setView('leaderboard')}
              disabled={!jobDescription || rankings.length === 0}
              className={`px-8 py-3.5 rounded-xl font-medium text-lg transition-all ${
                (!jobDescription || rankings.length === 0)
                  ? 'bg-white/5 text-gray-500 cursor-not-allowed border border-white/10'
                  : 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:shadow-lg hover:shadow-purple-500/25 hover:-translate-y-1'
              }`}
            >
              Analyze Candidates & View Leaderboard
            </button>
            {(!jobDescription || rankings.length === 0) && (
              <p className="text-sm text-gray-500 mt-3">
                Set job requirements and add at least one candidate to continue.
              </p>
            )}
          </div>
        </div>
      ) : (
        <div className="max-w-5xl mx-auto space-y-6">
          <div className="flex items-center justify-between">
            <button 
              onClick={() => setView('setup')}
              className="text-gray-400 hover:text-white flex items-center gap-2 transition-colors px-4 py-2 glass-card inline-flex"
            >
              ← Back to Setup
            </button>
            
            {/* Export Excel Button */}
            <button
              onClick={handleExportExcel}
              disabled={isExporting || rankings.length === 0}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all ${
                isExporting || rankings.length === 0
                  ? 'bg-white/5 text-gray-500 cursor-not-allowed border border-white/10'
                  : 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:shadow-lg hover:shadow-emerald-500/25 hover:-translate-y-0.5'
              }`}
            >
              {isExporting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Generating Report...
                </>
              ) : (
                <>
                  <FiDownload />
                  Export Excel Report
                </>
              )}
            </button>
          </div>
          
          <div className="glass-panel h-[75vh] p-8 flex flex-col">
            <div className="flex justify-between items-end mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white">Live Leaderboard</h2>
                <p className="text-gray-400 text-sm mt-1">Candidates ranked by Gemini AI analysis</p>
              </div>
              <div className="text-sm text-blue-400 font-medium">
                {rankings.length} Candidates Analyzed
              </div>
            </div>
            
            <RankingDashboard rankings={rankings} onSelect={setSelectedCandidate} />
          </div>
        </div>
      )}

      {selectedCandidate && (
        <CandidateInsightsModal 
          candidateId={selectedCandidate} 
          onClose={() => setSelectedCandidate(null)}
          apiBase={API_BASE}
        />
      )}
    </div>
  );
}

export default App;
