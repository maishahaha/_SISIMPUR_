export default function SettingsPage() {
  return (
    <div className="max-w-2xl mx-auto space-y-6 fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-white/40 text-sm mt-1">Manage your preferences</p>
      </div>

      {[
        {
          title: "Notifications",
          items: [
            { label: "Email notifications", description: "Receive updates about your quizzes via email", id: "notif-email" },
            { label: "Processing alerts", description: "Get notified when document processing completes", id: "notif-proc" },
          ],
        },
        {
          title: "Quiz Defaults",
          items: [
            { label: "Auto-start polling", description: "Automatically poll job status after upload", id: "auto-poll" },
          ],
        },
      ].map((section) => (
        <div key={section.title} className="glass border border-white/10 rounded-2xl p-6 space-y-4">
          <h3 className="text-sm font-semibold text-white/60 uppercase tracking-wider">{section.title}</h3>
          <div className="space-y-4">
            {section.items.map((item) => (
              <label key={item.id} htmlFor={item.id} className="flex items-start justify-between gap-4 cursor-pointer group">
                <div>
                  <p className="text-sm text-white group-hover:text-white/90">{item.label}</p>
                  <p className="text-xs text-white/30 mt-0.5">{item.description}</p>
                </div>
                <div className="relative">
                  <input type="checkbox" id={item.id} defaultChecked className="peer sr-only" />
                  <div className="w-10 h-5 bg-white/10 rounded-full peer-checked:bg-purple-600 transition-colors" />
                  <div className="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
                </div>
              </label>
            ))}
          </div>
        </div>
      ))}

      <div className="glass border border-red-500/20 rounded-2xl p-6 space-y-3">
        <h3 className="text-sm font-semibold text-red-400 uppercase tracking-wider">Danger Zone</h3>
        <p className="text-xs text-white/30">These actions are irreversible.</p>
        <button className="px-4 py-2 rounded-xl text-sm text-red-400 border border-red-500/30 hover:bg-red-500/10 transition">
          Delete Account
        </button>
      </div>
    </div>
  );
}
