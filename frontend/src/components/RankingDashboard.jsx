import { motion } from 'framer-motion';
import { FiUser, FiLinkedin, FiArrowRight } from 'react-icons/fi';

const getTierBadge = (tier) => {
  const t = (tier || '').toLowerCase();
  if (t.includes('strong')) return { emoji: '🟢', label: 'Strong Fit', classes: 'text-green-400' };
  if (t.includes('possible')) return { emoji: '🟡', label: 'Possible Fit', classes: 'text-yellow-400' };
  return { emoji: '🔴', label: 'Weak Fit', classes: 'text-red-400' };
};

export default function RankingDashboard({ rankings, onSelect }) {
  if (rankings.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
        <div className="w-16 h-16 mb-4 rounded-full bg-white/5 flex items-center justify-center">
          <FiUser className="text-2xl opacity-50" />
        </div>
        <p>Waiting for candidates...</p>
        <p className="text-sm">Upload resumes or add LinkedIn URLs</p>
      </div>
    );
  }

  const getScoreColor = (score) => {
    if (score >= 75) return 'text-green-400 bg-green-400/10 border-green-400/20';
    if (score >= 50) return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20';
    if (score >= 30) return 'text-orange-400 bg-orange-400/10 border-orange-400/20';
    return 'text-red-400 bg-red-400/10 border-red-400/20';
  };

  const getMedalEmoji = (idx) => {
    if (idx === 0) return '🥇';
    if (idx === 1) return '🥈';
    if (idx === 2) return '🥉';
    return null;
  };

  return (
    <div className="flex-1 overflow-y-auto pr-2 space-y-3">
      {rankings.map((cand, idx) => {
        const tier = getTierBadge(cand.fit_tier);
        const medal = getMedalEmoji(idx);
        
        return (
          <motion.div 
            key={cand.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            onClick={() => onSelect(cand.id)}
            className="glass-card p-4 flex items-center justify-between cursor-pointer group"
          >
            <div className="flex items-center gap-4">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg bg-white/10 group-hover:bg-blue-500/20 transition-colors`}>
                {medal || `#${idx + 1}`}
              </div>
              <div>
                <h3 className="font-medium text-white flex items-center gap-2">
                  {cand.name}
                  {cand.source === 'linkedin' && <FiLinkedin className="text-blue-500 text-sm" />}
                </h3>
                <p className={`text-xs ${tier.classes}`}>{tier.emoji} {tier.label}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className={`px-3 py-1 rounded-full border font-bold ${getScoreColor(cand.score)}`}>
                {cand.score}% Match
              </div>
              <div className="text-gray-500 group-hover:text-white transition-colors">
                <FiArrowRight />
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
