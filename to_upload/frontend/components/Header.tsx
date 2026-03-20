export const Header = () => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-3xl">🤖</span>
            <span className="text-xl font-semibold text-gray-800">
              Финансовый AI-агент
            </span>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full">
              ✅ Сервер: 127.0.0.1:8000
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};