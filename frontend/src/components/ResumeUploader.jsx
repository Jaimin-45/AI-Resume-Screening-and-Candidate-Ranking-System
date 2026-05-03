import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { FiUploadCloud, FiFileText } from 'react-icons/fi';

export default function ResumeUploader({ onUpload, disabled }) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const onDrop = useCallback(async (acceptedFiles) => {
    if (disabled || acceptedFiles.length === 0) return;
    
    setIsUploading(true);
    await onUpload(acceptedFiles);
    setUploadedFiles(prev => [...prev, ...acceptedFiles.map(f => f.name)]);
    setIsUploading(false);
  }, [onUpload, disabled]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    disabled
  });

  return (
    <div className={`transition-opacity ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}>
      <div 
        {...getRootProps()} 
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-300 ${
          isDragActive 
            ? 'border-blue-400 bg-blue-400/10' 
            : 'border-gray-600 hover:border-gray-400 bg-white/5'
        }`}
      >
        <input {...getInputProps()} />
        <FiUploadCloud className={`mx-auto text-4xl mb-3 ${isDragActive ? 'text-blue-400' : 'text-gray-400'}`} />
        <p className="text-sm text-gray-300">
          {isDragActive
            ? "Drop resumes here..."
            : "Drag & drop PDF/DOCX resumes, or click to select"}
        </p>
      </div>

      {isUploading && (
        <div className="mt-3 text-sm text-blue-400 flex items-center justify-center gap-2">
          <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
          Processing files...
        </div>
      )}

      {uploadedFiles.length > 0 && (
        <div className="mt-4 space-y-2">
          <p className="text-xs text-gray-400 font-semibold uppercase">Recent Uploads</p>
          {uploadedFiles.slice(-3).map((name, i) => (
            <div key={i} className="flex items-center gap-2 text-sm text-gray-300 bg-white/5 px-3 py-2 rounded-lg">
              <FiFileText className="text-purple-400" />
              <span className="truncate">{name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
