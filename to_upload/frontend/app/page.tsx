'use client';

import { useState } from 'react';
import { FileUploader } from '@/components/FileUploader';
import { Header } from '@/components/Header';

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [result, setResult] = useState<any>(null);

  const handleFilesUpload = async (files: File[]) => {
    setLoading(true);
    setError('');
    setSuccess('');
    setResult(null);
    
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    formData.append('analysis_type', 'full');

    try {
      const response = await fetch('http://127.0.0.1:8000/api/process-multiple', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Ошибка при обработке файлов');
      }

      if (data.success) {
        setSuccess(`✅ Успешно обработано ${data.processed} из ${data.total_files} файлов!
                  Всего транзакций: ${data.total_transactions}
                  Результат сохранен в: ${data.output_filename}`);
        setResult(data);
      } else {
        setError('Не удалось обработать файлы');
      }
      
    } catch (err: any) {
      setError(err.message || 'Ошибка при обработке файлов');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (result?.output_filename) {
      window.open(`http://127.0.0.1:8000/api/download/${result.output_filename}`, '_blank');
    }
  };

  const openResultsFolder = () => {
    // Инструкция для пользователя, так как из браузера нельзя открыть папку
    alert('Результаты сохранены в папку:\nC:\\Users\\Александр\\Desktop\\bank-analyzer\\uploads\\results');
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <Header />
      
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-800 mb-4">
              🤖 AI Анализ банковских выписок
            </h1>
            <p className="text-lg text-gray-600">
              Загрузите несколько выписок и получите единый отчет в Excel
            </p>
          </div>

          <FileUploader onFilesUpload={handleFilesUpload} loading={loading} />
          
          {/* Статус обработки */}
          {error && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600">❌ {error}</p>
            </div>
          )}
          
          {success && (
            <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-700 whitespace-pre-line">{success}</p>
              
              {result && (
                <div className="mt-4 flex space-x-3">
                  <button
                    onClick={handleDownload}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    📥 Скачать результат
                  </button>
                  <button
                    onClick={openResultsFolder}
                    className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                  >
                    📁 Открыть папку с результатами
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Детальная информация */}
          {result && result.results && (
            <div className="mt-6 bg-white rounded-xl shadow-lg p-6 border border-gray-100">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">
                📊 Детали обработки
              </h2>
              <div className="space-y-2">
                {result.results.map((r: any, index: number) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-600 truncate flex-1 mr-4">
                      {r.filename}
                    </span>
                    <span className={`text-sm font-medium ${
                      r.status.includes('✅') ? 'text-green-600' : 
                      r.status.includes('⚠️') ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {r.status}
                      {r.transactions && ` (${r.transactions} тр.)`}
                      {r.error && ` - ${r.error}`}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}