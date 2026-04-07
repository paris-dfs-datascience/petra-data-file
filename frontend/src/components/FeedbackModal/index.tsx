import { useEffect, useRef } from "react";

import { useFeedbackModal, type FeedbackModalProps } from "./behaviors";


export function FeedbackModal(props: FeedbackModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const { assessment, comment, submitting, submitted, error, setAssessment, setComment, handleSubmit, handleClose } =
    useFeedbackModal(props);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (props.isOpen && !dialog.open) dialog.showModal();
    if (!props.isOpen && dialog.open) dialog.close();
  }, [props.isOpen]);

  if (!props.isOpen) return null;

  return (
    <dialog
      ref={dialogRef}
      onClose={handleClose}
      className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-xl backdrop:bg-black/40"
    >
      {submitted ? (
        <p className="text-sm font-medium text-emerald-600">Feedback submitted. Thank you!</p>
      ) : (
        <>
          <h3 className="text-base font-semibold text-slate-950">Submit Feedback</h3>
          <p className="mt-1 text-sm text-slate-500">
            Is the model&rsquo;s assessment for <strong>{props.payload.rule_name}</strong> correct?
          </p>

          <div className="mt-4 flex gap-2">
            <button
              type="button"
              onClick={() => setAssessment("correct")}
              className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                assessment === "correct" ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              Correct
            </button>
            <button
              type="button"
              onClick={() => setAssessment("incorrect")}
              className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                assessment === "incorrect" ? "bg-rose-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              Incorrect
            </button>
          </div>

          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Optional: describe what's wrong or what the correct answer should be..."
            className="mt-4 w-full rounded-xl border border-slate-200 p-3 text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-300"
            rows={3}
          />

          {error ? <p className="mt-2 text-sm text-rose-600">{error}</p> : null}

          <div className="mt-4 flex justify-end gap-2">
            <button
              type="button"
              onClick={handleClose}
              className="rounded-full bg-slate-100 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-200"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => void handleSubmit()}
              disabled={submitting}
              className="rounded-full bg-slate-950 px-4 py-2 text-sm font-medium text-white transition disabled:opacity-50"
            >
              {submitting ? "Sending..." : "Submit"}
            </button>
          </div>
        </>
      )}
    </dialog>
  );
}
