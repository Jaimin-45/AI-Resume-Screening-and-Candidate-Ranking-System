import { useState } from 'react';
import { FiLinkedin, FiArrowRight } from 'react-icons/fi';

export default function LinkedInInput({ onSubmit, disabled }) {
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url || disabled) return;
    
    setIsLoading(true);
    await onSubmit(url);
    setUrl('');
    setIsLoading(false);
  };

  return (
    <form onSubmit={handleSubmit} className={`relative ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}>
      <div className="flex items-center bg-white/5 border border-white/10 rounded-lg overflow-hidden focus-within:border-blue-400 transition-colors">
        <div className="pl-3 py-2.5 text-blue-500">
          <FiLinkedin className="text-xl" />
        </div>
        <input 
          type="url" 
          placeholder="LinkedIn Profile URL..." 
          className="flex-1 bg-transparent border-none p-2.5 text-white text-sm focus:outline-none"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={disabled || isLoading}
          required
        />
        <button 
          type="submit"
          disabled={disabled || isLoading || !url}
          className="px-4 py-2.5 bg-blue-600/20 text-blue-400 hover:bg-blue-600/40 transition-colors disabled:opacity-50"
        >
          {isLoading ? (
            <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <FiArrowRight />
          )}
        </button>
      </div>
    </form>
  );
}
