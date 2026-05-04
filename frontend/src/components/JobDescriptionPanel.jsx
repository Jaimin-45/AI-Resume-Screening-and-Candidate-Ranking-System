import { useState } from 'react';
import { FiBriefcase } from 'react-icons/fi';

export default function JobDescriptionPanel({ onSubmit, initialJob }) {
  const [title, setTitle] = useState(initialJob?.title || 'Senior Software Engineer');
  const [description, setDescription] = useState(initialJob?.description || 'We are looking for a Python developer with experience in Machine Learning, Docker, AWS, and modern web frameworks like FastAPI and React.');
  const [isSubmitted, setIsSubmitted] = useState(!!initialJob);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ title, description });
    setIsSubmitted(true);
  };

  return (
    <div className="glass-panel p-6">
      <h2 className="text-xl font-semibold mb-4 text-white flex items-center gap-2">
        <FiBriefcase className="text-blue-400" /> Job Requirements
      </h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Job Title</label>
          <input 
            type="text" 
            className="w-full bg-white/5 border border-white/10 rounded-lg p-2.5 text-white focus:outline-none focus:border-blue-400 transition-colors"
            value={title}
            onChange={(e) => { setTitle(e.target.value); setIsSubmitted(false); }}
            required
          />
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">Description & Required Skills</label>
          <textarea 
            className="w-full bg-white/5 border border-white/10 rounded-lg p-2.5 text-white h-32 resize-none focus:outline-none focus:border-blue-400 transition-colors"
            value={description}
            onChange={(e) => { setDescription(e.target.value); setIsSubmitted(false); }}
            required
          />
        </div>
        <button 
          type="submit" 
          className={`w-full py-2.5 rounded-lg font-medium transition-all ${
            isSubmitted 
              ? 'bg-green-500/20 text-green-400 border border-green-500/30 cursor-default'
              : 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:shadow-lg hover:shadow-purple-500/20'
          }`}
        >
          {isSubmitted ? 'Active Job Profile' : 'Set Requirements'}
        </button>
      </form>
    </div>
  );
}
