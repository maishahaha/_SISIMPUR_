export default function HelpPage() {
  const sections = [
    {
      icon: "ri-upload-cloud-2-line",
      title: "Creating a Quiz",
      content: "Go to the Dashboard and drag & drop a PDF, image, or text file. Choose the number of questions, question type, and language, then click Generate Quiz. The AI will process your document and create questions automatically.",
    },
    {
      icon: "ri-pencil-ruler-2-line",
      title: "Taking an Exam",
      content: "Navigate to Give Exam, select a completed quiz, and choose Exam Mode. Answer each question and click Next. Submit when done — you'll see your score breakdown with detailed feedback.",
    },
    {
      icon: "ri-stack-line",
      title: "Flashcard Mode",
      content: "Select Flashcard Mode in Give Exam. Tap a card to reveal the answer, then rate your confidence as Easy, Medium, or Hard. This helps schedule future review sessions optimally.",
    },
    {
      icon: "ri-trophy-line",
      title: "Leaderboard",
      content: "The Leaderboard shows top performers across All Time, This Week, and This Month. Your score improves as you complete more exams.",
    },
    {
      icon: "ri-file-text-line",
      title: "Supported File Formats",
      content: "PDF documents (multi-page supported), Images (JPG, PNG — OCR extracts text), and plain text files (.txt). Maximum file size is 10 MB.",
    },
    {
      icon: "ri-question-answer-line",
      title: "Question Types",
      content: "MCQ (Multiple Choice): 4 options, one correct. True/False: binary answer. Short Answer: open-ended text response. Mixed: a combination of all types.",
    },
  ];

  return (
    <div className="max-w-3xl mx-auto space-y-6 fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Help & Guide</h1>
        <p className="text-white/40 text-sm mt-1">Everything you need to know about Sisimpur</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sections.map((s) => (
          <div key={s.title} className="glass border border-white/10 rounded-2xl p-5 space-y-3 hover:border-white/20 transition">
            <div className="w-10 h-10 rounded-xl bg-purple-600/20 flex items-center justify-center">
              <i className={`${s.icon} text-purple-400 text-xl`} />
            </div>
            <h3 className="text-sm font-semibold text-white">{s.title}</h3>
            <p className="text-xs text-white/50 leading-relaxed"
              dangerouslySetInnerHTML={{ __html: s.content }}
            />
          </div>
        ))}
      </div>

      <div className="glass border border-white/10 rounded-2xl p-6 text-center space-y-3">
        <i className="ri-customer-service-2-line text-3xl text-purple-400" />
        <p className="text-sm text-white">Need more help?</p>
        <p className="text-xs text-white/40">
          Open an issue on GitHub or check the{" "}
          <a href="/README.md" className="text-purple-400 hover:underline">README</a>.
        </p>
      </div>
    </div>
  );
}
