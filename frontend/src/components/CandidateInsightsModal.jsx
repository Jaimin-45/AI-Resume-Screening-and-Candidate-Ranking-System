import { useState, useEffect } from 'react';
import axios from 'axios';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import { 
  FiX, FiCheckCircle, FiAlertCircle, FiAlertTriangle, FiAward, 
  FiTrendingUp, FiMail, FiPhone, FiMapPin, FiLinkedin, FiGlobe,
  FiBriefcase, FiBookOpen, FiMessageSquare, FiFlag
} from 'react-icons/fi';

const getScoreBand = (score) => {
  if (score >= 75) return { label: 'Strong Fit', color: 'text-green-400', bg: 'bg-green-400/10', border: 'border-green-400/30', emoji: '🟢' };
  if (score >= 50) return { label: 'Possible Fit', color: 'text-yellow-400', bg: 'bg-yellow-400/10', border: 'border-yellow-400/30', emoji: '🟡' };
  if (score >= 30) return { label: 'Weak Fit', color: 'text-orange-400', bg: 'bg-orange-400/10', border: 'border-orange-400/30', emoji: '🟠' };
  return { label: 'Poor Fit', color: 'text-red-400', bg: 'bg-red-400/10', border: 'border-red-400/30', emoji: '🔴' };
};

const getBarColor = (value) => {
  if (value >= 75) return '#34d399';
  if (value >= 50) return '#fbbf24';
  if (value >= 30) return '#fb923c';
  return '#f87171';
};

const getActionStyle = (action) => {
  const a = (action || '').toLowerCase();
  if (a.includes('technical')) return 'bg-green-500/15 text-green-400 border-green-500/30';
  if (a.includes('phone')) return 'bg-blue-500/15 text-blue-400 border-blue-500/30';
  if (a.includes('reject')) return 'bg-red-500/15 text-red-400 border-red-500/30';
  return 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30';
};

export default function CandidateInsightsModal({ candidateId, onClose, apiBase }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    const fetchInsights = async () => {
      try {
        const res = await axios.get(`${apiBase}/candidate-insights/${candidateId}`);
        setData(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchInsights();
  }, [candidateId, apiBase]);

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-gray-400 text-sm animate-pulse">Analyzing the candidate...</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const { profile, analysis } = data;
  const { candidate, match, experience, education, skills, red_flags, recruiter_tools } = analysis;
  const band = getScoreBand(match.overall_score_percent);

  const radarData = [
    { dimension: 'Skills', value: match.skills_score_percent },
    { dimension: 'Experience', value: match.experience_score_percent },
    { dimension: 'Relevance', value: match.semantic_relevance_score_percent },
    { dimension: 'Overall', value: match.overall_score_percent },
  ];

  const scoreItems = [
    { name: 'Skills Match', value: match.skills_score_percent },
    { name: 'Experience', value: match.experience_score_percent },
    { name: 'Semantic Relevance', value: match.semantic_relevance_score_percent },
  ];

  const hasRedFlags = (
    (red_flags.employment_gaps && red_flags.employment_gaps.toLowerCase() !== 'none') ||
    (red_flags.job_hopping && red_flags.job_hopping.toLowerCase() !== 'none') ||
    (red_flags.role_mismatch && red_flags.role_mismatch.toLowerCase() !== 'none') ||
    (red_flags.other_concerns && red_flags.other_concerns.trim() !== '')
  );

  const tabs = [
    { key: 'overview', label: 'Overview' },
    { key: 'skills', label: 'Skills' },
    { key: 'experience', label: 'Experience' },
    { key: 'recruiter', label: 'Recruiter Tools' },
  ];

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div 
        className="bg-[#1a1d2d] border border-white/10 w-full max-w-6xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]"
        onClick={(e) => e.stopPropagation()}
      >
        
        {/* ═══ Header ═══ */}
        <div className="p-6 border-b border-white/10 bg-white/5">
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-5">
              <div className={`w-22 h-22 rounded-2xl border-4 ${band.border} ${band.bg} flex flex-col items-center justify-center shrink-0 p-4`}>
                <span className={`text-3xl font-bold ${band.color}`}>{match.overall_score_percent}%</span>
                <span className={`text-xs ${band.color} mt-0.5`}>{match.fit_tier}</span>
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white mb-1">{candidate.full_name || profile.name}</h2>
                <p className="text-gray-400 text-sm mb-2">{match.one_line_verdict}</p>
                <div className="flex items-center gap-3 flex-wrap">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium border ${band.border} ${band.bg} ${band.color}`}>
                    {band.emoji} {band.label}
                  </span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getActionStyle(recruiter_tools.recommended_action)}`}>
                    {recruiter_tools.recommended_action}
                  </span>
                  {hasRedFlags && (
                    <span className="px-3 py-1 rounded-full text-sm font-medium border border-red-400/30 bg-red-400/10 text-red-400 flex items-center gap-1">
                      <FiFlag className="text-xs" /> Red Flags Detected
                    </span>
                  )}
                </div>
              </div>
            </div>
            <button onClick={onClose} className="p-2 bg-white/5 rounded-full hover:bg-white/10 text-gray-400 hover:text-white transition-colors">
              <FiX className="text-xl" />
            </button>
          </div>

          {/* Contact Info Bar */}
          <div className="flex flex-wrap gap-4 mt-4 pt-3 border-t border-white/5">
            {candidate.email && candidate.email !== "Not specified" && (
              <span className="text-xs text-gray-400 flex items-center gap-1"><FiMail className="text-blue-400" />{candidate.email}</span>
            )}
            {candidate.phone && candidate.phone !== "Not specified" && (
              <span className="text-xs text-gray-400 flex items-center gap-1"><FiPhone className="text-green-400" />{candidate.phone}</span>
            )}
            {candidate.location && candidate.location !== "Not specified" && (
              <span className="text-xs text-gray-400 flex items-center gap-1"><FiMapPin className="text-orange-400" />{candidate.location}</span>
            )}
            {candidate.linkedin_url && candidate.linkedin_url !== "Not specified" && (
              <a href={candidate.linkedin_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-400 flex items-center gap-1 hover:text-blue-300">
                <FiLinkedin />LinkedIn
              </a>
            )}
            {candidate.portfolio_url && candidate.portfolio_url !== "Not specified" && (
              <a href={candidate.portfolio_url} target="_blank" rel="noopener noreferrer" className="text-xs text-purple-400 flex items-center gap-1 hover:text-purple-300">
                <FiGlobe />Portfolio
              </a>
            )}
          </div>
        </div>

        {/* ═══ Tab Bar ═══ */}
        <div className="flex border-b border-white/10 bg-white/[0.02] px-6">
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-5 py-3 text-sm font-medium transition-all relative ${
                activeTab === tab.key 
                  ? 'text-white' 
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              {tab.label}
              {activeTab === tab.key && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500 to-purple-500"></div>
              )}
            </button>
          ))}
        </div>

        {/* ═══ Content ═══ */}
        <div className="p-6 overflow-y-auto flex-1">
          
          {/* ─── Overview Tab ─── */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Left: Score Bars + Radar */}
              <div className="space-y-6">
                {/* Score Breakdown */}
                <div className="glass-panel p-5">
                  <h3 className="text-sm font-semibold text-gray-400 mb-4">Score Breakdown</h3>
                  <div className="space-y-4">
                    {scoreItems.map((item) => (
                      <div key={item.name}>
                        <div className="flex justify-between text-sm mb-1.5">
                          <span className="text-gray-300 font-medium">{item.name}</span>
                          <span className="font-bold" style={{ color: getBarColor(item.value) }}>{item.value}%</span>
                        </div>
                        <div className="w-full bg-white/5 rounded-full h-3 overflow-hidden">
                          <div 
                            className="h-full rounded-full transition-all duration-700 ease-out"
                            style={{ 
                              width: `${item.value}%`, 
                              backgroundColor: getBarColor(item.value),
                              boxShadow: `0 0 8px ${getBarColor(item.value)}40`
                            }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="flex justify-between mt-4 pt-3 border-t border-white/5">
                    <div className="flex items-center gap-1 text-xs"><span className="w-2 h-2 rounded-full bg-red-400"></span><span className="text-gray-500">0-29</span></div>
                    <div className="flex items-center gap-1 text-xs"><span className="w-2 h-2 rounded-full bg-orange-400"></span><span className="text-gray-500">30-49</span></div>
                    <div className="flex items-center gap-1 text-xs"><span className="w-2 h-2 rounded-full bg-yellow-400"></span><span className="text-gray-500">50-74</span></div>
                    <div className="flex items-center gap-1 text-xs"><span className="w-2 h-2 rounded-full bg-green-400"></span><span className="text-gray-500">75-100</span></div>
                  </div>
                </div>

                {/* Radar */}
                <div className="h-64 glass-panel p-4">
                  <h3 className="text-sm font-semibold text-gray-400 text-center mb-2">Competency Radar</h3>
                  <ResponsiveContainer width="100%" height="85%">
                    <RadarChart cx="50%" cy="50%" outerRadius="68%" data={radarData}>
                      <PolarGrid stroke="rgba(255,255,255,0.08)" />
                      <PolarAngleAxis dataKey="dimension" tick={{fill: '#9ca3af', fontSize: 11, fontWeight: 500}} />
                      <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{fill: '#6b7280', fontSize: 9}} axisLine={false} tickCount={5} />
                      <Radar name="Candidate" dataKey="value" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.3} strokeWidth={2} dot={{ r: 3, fill: '#8b5cf6' }} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Right: Strengths, Weaknesses, Red Flags */}
              <div className="space-y-5">
                {/* Strengths */}
                <div>
                  <h3 className="text-sm font-semibold text-green-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <FiTrendingUp /> Strengths
                  </h3>
                  <p className="text-sm text-gray-300 bg-green-500/5 border border-green-500/10 p-3.5 rounded-xl leading-relaxed">
                    {recruiter_tools.strengths_summary}
                  </p>
                </div>

                {/* Weaknesses */}
                <div>
                  <h3 className="text-sm font-semibold text-yellow-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <FiAlertCircle /> Weaknesses
                  </h3>
                  <p className="text-sm text-gray-300 bg-yellow-500/5 border border-yellow-500/10 p-3.5 rounded-xl leading-relaxed">
                    {recruiter_tools.weaknesses_summary}
                  </p>
                </div>

                {/* Red Flags */}
                {hasRedFlags && (
                  <div>
                    <h3 className="text-sm font-semibold text-red-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                      <FiFlag /> Red Flags
                    </h3>
                    <div className="space-y-2">
                      {red_flags.employment_gaps && red_flags.employment_gaps.toLowerCase() !== 'none' && (
                        <div className="flex items-start gap-2 text-sm text-red-300 bg-red-500/5 border border-red-500/10 p-2.5 rounded-lg">
                          <FiAlertTriangle className="mt-0.5 shrink-0" />
                          <span><strong>Employment Gaps:</strong> {red_flags.employment_gaps}</span>
                        </div>
                      )}
                      {red_flags.job_hopping && red_flags.job_hopping.toLowerCase() !== 'none' && (
                        <div className="flex items-start gap-2 text-sm text-red-300 bg-red-500/5 border border-red-500/10 p-2.5 rounded-lg">
                          <FiAlertTriangle className="mt-0.5 shrink-0" />
                          <span><strong>Job Hopping:</strong> {red_flags.job_hopping}</span>
                        </div>
                      )}
                      {red_flags.role_mismatch && red_flags.role_mismatch.toLowerCase() !== 'none' && (
                        <div className="flex items-start gap-2 text-sm text-red-300 bg-red-500/5 border border-red-500/10 p-2.5 rounded-lg">
                          <FiAlertTriangle className="mt-0.5 shrink-0" />
                          <span><strong>Role Mismatch:</strong> {red_flags.role_mismatch}</span>
                        </div>
                      )}
                      {red_flags.other_concerns && red_flags.other_concerns.trim() !== '' && (
                        <div className="flex items-start gap-2 text-sm text-red-300 bg-red-500/5 border border-red-500/10 p-2.5 rounded-lg">
                          <FiAlertTriangle className="mt-0.5 shrink-0" />
                          <span><strong>Other:</strong> {red_flags.other_concerns}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Quick Stats */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="glass-panel p-3 text-center">
                    <p className="text-2xl font-bold text-white">{experience.total_years || 0}</p>
                    <p className="text-xs text-gray-400 mt-1">Years Exp</p>
                  </div>
                  <div className="glass-panel p-3 text-center">
                    <p className="text-2xl font-bold text-green-400">{skills.matched_required_skills?.length || 0}</p>
                    <p className="text-xs text-gray-400 mt-1">Skills Matched</p>
                  </div>
                  <div className="glass-panel p-3 text-center">
                    <p className="text-2xl font-bold text-red-400">{skills.missing_required_skills?.length || 0}</p>
                    <p className="text-xs text-gray-400 mt-1">Skills Missing</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ─── Skills Tab ─── */}
          {activeTab === 'skills' && (
            <div className="space-y-6">
              {/* Tech Stack Summary */}
              <div className="glass-panel p-5">
                <h3 className="text-sm font-semibold text-gray-400 mb-3">Tech Stack Summary</h3>
                <p className="text-gray-200 text-sm">{skills.tech_stack_summary}</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                {/* Matched Skills */}
                <div>
                  <h3 className="text-sm font-semibold text-green-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <FiCheckCircle /> Matched Skills
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {(skills.matched_required_skills || []).map((skill, i) => (
                      <span key={i} className="px-2.5 py-1 bg-green-500/10 text-green-300 border border-green-500/20 rounded-lg text-xs font-medium">
                        ✓ {skill}
                      </span>
                    ))}
                    {(!skills.matched_required_skills || skills.matched_required_skills.length === 0) && (
                      <p className="text-sm text-gray-500">No matched skills detected</p>
                    )}
                  </div>
                </div>

                {/* Missing Skills */}
                <div>
                  <h3 className="text-sm font-semibold text-red-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <FiAlertTriangle /> Missing Skills
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {(skills.missing_required_skills || []).map((skill, i) => (
                      <span key={i} className="px-2.5 py-1 bg-red-500/10 text-red-300 border border-red-500/20 rounded-lg text-xs font-medium">
                        ✗ {skill}
                      </span>
                    ))}
                    {(!skills.missing_required_skills || skills.missing_required_skills.length === 0) && (
                      <p className="text-sm text-gray-500">No missing skills</p>
                    )}
                  </div>
                </div>

                {/* Bonus Skills */}
                <div>
                  <h3 className="text-sm font-semibold text-purple-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <FiAward /> Bonus Skills
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {(skills.bonus_skills || []).map((skill, i) => (
                      <span key={i} className="px-2.5 py-1 bg-purple-500/10 text-purple-300 border border-purple-500/20 rounded-lg text-xs font-medium">
                        ★ {skill}
                      </span>
                    ))}
                    {(!skills.bonus_skills || skills.bonus_skills.length === 0) && (
                      <p className="text-sm text-gray-500">No bonus skills detected</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ─── Experience Tab ─── */}
          {activeTab === 'experience' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Experience */}
              <div className="space-y-5">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <FiBriefcase className="text-blue-400" /> Work Experience
                </h3>
                <div className="space-y-3">
                  <div className="glass-panel p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-white font-medium">{experience.current_role || 'Not specified'}</p>
                        <p className="text-gray-400 text-sm">{experience.current_company || 'Not specified'}</p>
                      </div>
                      <span className="text-sm text-blue-400 font-bold">{experience.total_years || 0} yrs</span>
                    </div>
                  </div>
                  <div className="glass-panel p-4">
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Career Progression</p>
                    <p className="text-sm text-gray-300">{experience.career_progression || 'Not specified'}</p>
                  </div>
                  <div className="glass-panel p-4">
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Industry Background</p>
                    <p className="text-sm text-gray-300">{experience.industry_background || 'Not specified'}</p>
                  </div>
                  {experience.notable_companies && experience.notable_companies.length > 0 && (
                    <div className="glass-panel p-4">
                      <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Notable Companies</p>
                      <div className="flex flex-wrap gap-2">
                        {experience.notable_companies.map((company, i) => (
                          <span key={i} className="px-2.5 py-1 bg-blue-500/10 text-blue-300 border border-blue-500/20 rounded-lg text-xs font-medium">
                            {company}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Education */}
              <div className="space-y-5">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <FiBookOpen className="text-purple-400" /> Education
                </h3>
                <div className="glass-panel p-5 space-y-4">
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wider">Highest Degree</p>
                    <p className="text-white font-medium mt-1">{education.highest_degree || 'Not specified'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wider">Field of Study</p>
                    <p className="text-gray-300 mt-1">{education.field_of_study || 'Not specified'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wider">Institution</p>
                    <p className="text-gray-300 mt-1">{education.institution || 'Not specified'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wider">Graduation Year</p>
                    <p className="text-gray-300 mt-1">{education.graduation_year || 'Not specified'}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ─── Recruiter Tools Tab ─── */}
          {activeTab === 'recruiter' && (
            <div className="space-y-6">
              {/* Action Recommendation */}
              <div className="glass-panel p-5 flex items-center gap-4">
                <div className={`px-4 py-2 rounded-xl text-sm font-bold border ${getActionStyle(recruiter_tools.recommended_action)}`}>
                  {recruiter_tools.recommended_action}
                </div>
                <p className="text-gray-400 text-sm">Recommended next step for this candidate</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Strengths Summary */}
                <div>
                  <h3 className="text-sm font-semibold text-green-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <FiTrendingUp /> Why This Candidate Stands Out
                  </h3>
                  <p className="text-sm text-gray-300 bg-green-500/5 border border-green-500/10 p-4 rounded-xl leading-relaxed">
                    {recruiter_tools.strengths_summary}
                  </p>
                </div>

                {/* Weaknesses Summary */}
                <div>
                  <h3 className="text-sm font-semibold text-yellow-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <FiAlertCircle /> Key Gaps to Probe
                  </h3>
                  <p className="text-sm text-gray-300 bg-yellow-500/5 border border-yellow-500/10 p-4 rounded-xl leading-relaxed">
                    {recruiter_tools.weaknesses_summary}
                  </p>
                </div>
              </div>

              {/* Interview Questions */}
              <div>
                <h3 className="text-sm font-semibold text-blue-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <FiMessageSquare /> Suggested Interview Questions
                </h3>
                <div className="space-y-2">
                  {(recruiter_tools.suggested_interview_questions || []).map((q, i) => (
                    <div key={i} className="flex items-start gap-3 text-sm text-gray-300 bg-blue-500/5 border border-blue-500/10 p-3.5 rounded-xl">
                      <span className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-xs font-bold shrink-0">
                        {i + 1}
                      </span>
                      <span>{q}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
