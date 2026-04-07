import { useState } from "react";

import { apiPostJson } from "@/services/apiClient";
import type { FeedbackPayload, FeedbackResponse } from "@/types/api";


export interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  payload: Omit<FeedbackPayload, "assessment" | "comment">;
}

export function useFeedbackModal({ payload, onClose }: FeedbackModalProps) {
  const [assessment, setAssessment] = useState<"correct" | "incorrect">("incorrect");
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await apiPostJson<FeedbackResponse>("/feedbacks", {
        ...payload,
        assessment,
        comment,
      });
      setSubmitted(true);
      setTimeout(() => {
        onClose();
        setSubmitted(false);
        setAssessment("incorrect");
        setComment("");
      }, 1200);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit feedback.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!submitting) {
      onClose();
      setAssessment("incorrect");
      setComment("");
      setError(null);
      setSubmitted(false);
    }
  };

  return { assessment, comment, submitting, submitted, error, setAssessment, setComment, handleSubmit, handleClose };
}
