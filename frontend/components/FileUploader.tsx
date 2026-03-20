'use client';

import { useState } from 'react';

interface FileUploaderProps {
  onFilesUpload: (files: File[]) => void;
  loading: boolean;
}

export const FileUploader = ({ onFilesUpload, loading }: FileUploaderProps) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [dragActive, setDragActive] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const filesArray = Array.from(e.target.files);
      setSelectedFiles(filesArray);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const filesArray = Array.from(e.dataTransfer.files);
      setSelectedFiles(filesArray);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFiles.length > 0) {
      onFilesUpload(selectedFiles);
    }
  };

  const removeFile = (indexToRemove: number) => {
    setSelectedFiles(selectedFiles.filter((_, index) => index !== indexToRemove));
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            📄 Выберите файлы с выписками (можно выбрать несколько)
          </label>
          
          {/* Область перетаскивания */}
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-300 hover:border-blue-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              onChange={handleFileChange}
              accept=".csv,.xlsx,.xls"
              multiple
              className="hidden"
              id="file-upload"
            />
            
            <label
              htmlFor="file-upload"
              className="cursor-pointer flex flex-col items-center space-y-3"
            >
              <span className="text-5xl">📂</span>
              <span className="text-lg font-medium text-gray-700">
                Нажмите для выбора файлов
              </span>
              <span className="text-sm text-gray-500">
                или перетащите их сюда
              </span>
              <span className="text-xs text-gray-400 bg-gray-50 px-3 py-1 rounded-full">
                Поддерживаются: Excel, CSV (до 20 файлов)
              </span>
            </label>
          </div>

          {/* Список выбранных файлов */}
          {selectedFiles.length > 0 && (
            <div className="mt-4">
              <p className="text-sm font-medium text-gray-700 mb-2">
                Выбрано файлов: {selectedFiles.length}
              </p>
              <div className="max-h-40 overflow-y-auto border border-gray-200 rounded-lg p-2">
                {selectedFiles.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between py-1 px-2 hover:bg-gray-50 rounded group"
                  >
                    <span className="text-sm text-gray-600 truncate flex-1">
                      📄 {file.name}
                    </span>
                    <button
                      type="button"
                      onClick={() => removeFile(index)}
                      className="text-gray-400 hover:text-red-500 transition-colors ml-2 opacity-0 group-hover:opacity-100"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={selectedFiles.length === 0 || loading}
          className={`w-full py-3 px-4 rounded-lg text-white font-medium transition-all transform hover:scale-[1.02] ${
            selectedFiles.length === 0 || loading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 shadow-lg hover:shadow-xl'
          }`}
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Обрабатываю {selectedFiles.length} файлов...
            </span>
          ) : (
            `🚀 Обработать ${selectedFiles.length > 0 ? selectedFiles.length : ''} файлов`
          )}
        </button>
      </form>
    </div>
  );
};