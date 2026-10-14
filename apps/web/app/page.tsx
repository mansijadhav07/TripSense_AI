import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-slate-900">
                TripSense AI
              </h1>
            </div>
            <div className="flex gap-4">
              <Link
                href="http://localhost:8000/docs"
                className="text-slate-600 hover:text-slate-900 px-3 py-2 rounded-md text-sm font-medium"
                target="_blank"
              >
                API Docs
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center">
          <h2 className="text-5xl font-extrabold text-slate-900 mb-4">
            Travel smarter. Stay better.
          </h2>
          <p className="text-xl text-slate-600 mb-8 max-w-2xl mx-auto">
            AI-powered hotel recommendations tailored to your preferences.
            Discover your perfect stay with personalized insights.
          </p>
          
          <div className="flex gap-4 justify-center">
            <button className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition">
              Start Discovering
            </button>
            <button className="bg-white text-blue-600 border-2 border-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-blue-50 transition">
              Learn More
            </button>
          </div>
        </div>

        {/* Features */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="text-blue-600 text-4xl mb-4">🎯</div>
            <h3 className="text-xl font-semibold mb-2">Personalized</h3>
            <p className="text-slate-600">
              Recommendations based on your unique preferences and travel style
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="text-blue-600 text-4xl mb-4">🤖</div>
            <h3 className="text-xl font-semibold mb-2">AI-Powered</h3>
            <p className="text-slate-600">
              Multiple recommendation algorithms working together for best results
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="text-blue-600 text-4xl mb-4">📊</div>
            <h3 className="text-xl font-semibold mb-2">Explainable</h3>
            <p className="text-slate-600">
              Clear reasons why each hotel matches your preferences
            </p>
          </div>
        </div>

        {/* Status Section */}
        <div className="mt-16 bg-white p-8 rounded-lg shadow-md">
          <h3 className="text-2xl font-bold mb-4 text-center">System Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border-l-4 border-green-500 pl-4">
              <p className="text-sm text-slate-600">Backend API</p>
              <p className="text-lg font-semibold text-green-600">✓ Operational</p>
            </div>
            <div className="border-l-4 border-green-500 pl-4">
              <p className="text-sm text-slate-600">Database</p>
              <p className="text-lg font-semibold text-green-600">✓ Connected</p>
            </div>
            <div className="border-l-4 border-blue-500 pl-4">
              <p className="text-sm text-slate-600">ML Models</p>
              <p className="text-lg font-semibold text-blue-600">⏳ Phase 3</p>
            </div>
            <div className="border-l-4 border-blue-500 pl-4">
              <p className="text-sm text-slate-600">Recommendations</p>
              <p className="text-lg font-semibold text-blue-600">⏳ Phase 5</p>
            </div>
          </div>
          <div className="mt-6 text-center">
            <Link
              href="http://localhost:8000/docs"
              target="_blank"
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              View API Documentation →
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <p className="text-center text-slate-600">
            © 2026 TripSense AI. Built with Next.js, FastAPI, and Apache Spark.
          </p>
        </div>
      </footer>
    </div>
  );
}
