interface AnalysisResultProps {
  result: any;
}

export const AnalysisResult = ({ result }: AnalysisResultProps) => {
  if (!result) return null;

  return (
    <div className="mt-8 bg-white rounded-xl shadow-lg p-6 border border-gray-100">
      <h2 className="text-2xl font-semibold text-gray-800 mb-4 flex items-center">
        <span className="mr-2">📊</span>
        Результат анализа
      </h2>
      
      <div className="mb-4 p-3 bg-blue-50 rounded-lg">
        <p className="text-sm text-blue-700">
          📄 Файл: <span className="font-medium">{result.filename}</span>
        </p>
      </div>
      
      <div className="prose max-w-none">
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <pre className="whitespace-pre-wrap font-sans text-gray-700">
            {result.analysis}
          </pre>
        </div>
      </div>
      
      <div className="mt-4 text-right">
        <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-green-100 text-green-700">
          ✅ Анализ завершен
        </span>
      </div>
    </div>
  );
};