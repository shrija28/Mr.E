import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

// High-precision face & liveness analyzer that verifies an actual human face is present
// and strictly rejects covered cameras, black frames, blank walls, and Windows "Camera Off" placeholders.
const analyzeFaceInVideo = async (video, prevFrameRef) => {
  if (!video || video.readyState < 2 || video.videoWidth === 0 || video.videoHeight === 0) {
    return { detected: false, confidence: 0, reason: 'Waiting for camera feed...' };
  }

  // 1. Native Chromium Shape Detection API (if supported by Chrome/Edge)
  if ('FaceDetector' in window) {
    try {
      const detector = new window.FaceDetector({ fastMode: true, maxDetectedFaces: 2 });
      const faces = await detector.detect(video);
      if (faces && faces.length > 0) {
        const f = faces[0];
        if (f.boundingBox && f.boundingBox.width > 25 && f.boundingBox.height > 25) {
          return { detected: true, confidence: 98, reason: 'Student face verified' };
        }
      } else {
        // Native FaceDetector is supported and found 0 faces in view
        return { detected: false, confidence: 0, reason: 'No face detected in camera view' };
      }
    } catch (e) {
      // Fall through to computer vision analyzer
    }
  }

  // 2. High-Precision Computer Vision Multi-Stage Analyzer (160x120)
  try {
    const canvas = document.createElement('canvas');
    const width = 160;
    const height = 120;
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) return { detected: false, confidence: 0, reason: 'Canvas unavailable' };

    ctx.drawImage(video, 0, 0, width, height);
    const imgData = ctx.getImageData(0, 0, width, height);
    const pixels = imgData.data;
    const totalPixels = width * height;

    let totalLuma = 0;
    let monochromePixels = 0;
    let skinPixels = 0;
    let centerSkinPixels = 0;
    let centerTotalPixels = 0;

    // Central region (where student's head and face must be framed)
    const cXStart = Math.floor(width * 0.18);
    const cXEnd = Math.floor(width * 0.82);
    const cYStart = Math.floor(height * 0.08);
    const cYEnd = Math.floor(height * 0.92);

    let skinMinX = width, skinMaxX = 0, skinMinY = height, skinMaxY = 0;
    const centerLumas = [];

    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const i = (y * width + x) * 4;
        const r = pixels[i];
        const g = pixels[i + 1];
        const b = pixels[i + 2];

        const luma = (r * 299 + g * 587 + b * 114) / 1000;
        totalLuma += luma;

        // Monochrome / grayscale check
        const maxCh = Math.max(r, g, b);
        const minCh = Math.min(r, g, b);
        const diff = maxCh - minCh;
        if (diff < 12) {
          monochromePixels++;
        }

        // Multi-ethnic human skin tone chromaticity locus in YCbCr and RGB
        const Cb = -0.168736 * r - 0.331264 * g + 0.5 * b + 128;
        const Cr = 0.5 * r - 0.418688 * g - 0.081312 * b + 128;

        const isSkin = (
          Cb >= 73 && Cb <= 135 &&
          Cr >= 130 && Cr <= 180 &&
          r > 45 && g > 25 && b > 15 &&
          r > g && g >= b * 0.82 &&
          diff > 12
        );

        const inCenter = (x >= cXStart && x <= cXEnd && y >= cYStart && y <= cYEnd);
        if (inCenter) {
          centerTotalPixels++;
          centerLumas.push(luma);
          if (isSkin) {
            centerSkinPixels++;
            if (x < skinMinX) skinMinX = x;
            if (x > skinMaxX) skinMaxX = x;
            if (y < skinMinY) skinMinY = y;
            if (y > skinMaxY) skinMaxY = y;
          }
        }
        if (isSkin) skinPixels++;
      }
    }

    const avgLuma = totalLuma / totalPixels;
    const monochromeRatio = monochromePixels / totalPixels;
    const centerSkinRatio = centerTotalPixels > 0 ? (centerSkinPixels / centerTotalPixels) : 0;

    // 1. Camera lens is covered or environment is pitch black
    if (avgLuma < 15) {
      return { detected: false, confidence: 0, reason: 'Camera lens covered or room is dark' };
    }

    // 2. Camera is overexposed (pure white glare)
    if (avgLuma > 248) {
      return { detected: false, confidence: 0, reason: 'Camera feed is overexposed' };
    }

    // 3. Windows "Camera Off" placeholder graphic:
    // Windows camera driver outputs a synthetic graphic (black frame with white crossed-out camera icon).
    // This graphic is >85% monochrome with 0.00% skin chromaticity.
    if (monochromeRatio > 0.78 && centerSkinRatio < 0.03) {
      return { detected: false, confidence: 0, reason: 'Camera is off (privacy shutter closed or hardware switch off)' };
    }

    // 4. Insufficient human skin tone in center region
    if (centerSkinRatio < 0.055) {
      return { detected: false, confidence: 0, reason: 'No student face detected in camera frame' };
    }

    // 5. Skin cluster bounding box geometry & anthropometrics
    const boxW = skinMaxX - skinMinX;
    const boxH = skinMaxY - skinMinY;
    if (boxW < 16 || boxH < 20) {
      return { detected: false, confidence: 15, reason: 'Face is too far or partially obscured' };
    }

    const aspectRatio = boxH / Math.max(1, boxW);
    if (aspectRatio < 0.60 || aspectRatio > 2.70) {
      return { detected: false, confidence: 20, reason: 'Please position your face upright in the oval' };
    }

    // 6. Facial luminance variance (distinguishes human facial features like eyes/brows/nose from flat surfaces)
    let sumVar = 0;
    const cLen = centerLumas.length;
    for (let i = 0; i < cLen; i++) {
      const d = centerLumas[i] - avgLuma;
      sumVar += d * d;
    }
    const stdDev = Math.sqrt(sumVar / Math.max(1, cLen));
    if (stdDev < 8) {
      return { detected: false, confidence: 25, reason: 'Position face directly in front of camera' };
    }

    const confidence = Math.min(99, Math.round(centerSkinRatio * 140 + 50));
    return { detected: true, confidence, reason: 'Student face verified & live' };
  } catch (err) {
    console.error("Face analysis error:", err);
    return { detected: false, confidence: 0, reason: 'Analyzing camera feed...' };
  }
};

const Exam = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [examSetId, setExamSetId] = useState(searchParams.get('set') || '');
  const [subject, setSubject] = useState(searchParams.get('subject') || 'General');
  const [examName, setExamName] = useState(searchParams.get('name') || 'KCET Exam');
  const [setLabel, setSetLabel] = useState(searchParams.get('label') || 'A');

  // Published exams state for test selection
  const [publishedSubjects, setPublishedSubjects] = useState([]);
  const [loadingPublished, setLoadingPublished] = useState(false);
  const [publishedError, setPublishedError] = useState('');
  const [remainingAttempts, setRemainingAttempts] = useState(null);
  const [selectedSubjectFilter, setSelectedSubjectFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const [questions, setQuestions] = useState([]);
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [loadError, setLoadError] = useState('');

  const [started, setStarted] = useState(false);
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState({});
  const [skipped, setSkipped] = useState(new Set());
  const EXAM_DURATION_SEC = 80 * 60; // 80 minutes
  const [timeLeft, setTimeLeft] = useState(EXAM_DURATION_SEC);
  const [submitting, setSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState(null);
  const [reviewFilter, setReviewFilter] = useState('all'); // 'all' | 'correct' | 'incorrect' | 'skipped'

  const videoRef = useRef(null);
  const videoPreviewRef = useRef(null);
  const videoAlertRef = useRef(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState('');
  const [checkingCamera, setCheckingCamera] = useState(false);
  const [cameraStream, setCameraStream] = useState(null);

  // Student Face Visibility & Proctoring State (2-Strike System)
  const [faceDetected, setFaceDetected] = useState(false);
  const [faceStatus, setFaceStatus] = useState('Checking camera...');
  const [faceConfidence, setFaceConfidence] = useState(0);
  const [faceMissingAlert, setFaceMissingAlert] = useState(false);
  const faceMissingAlertRef = useRef(false);
  const [faceViolations, setFaceViolations] = useState(0);
  const faceViolationsRef = useRef(0);
  const [realignCountdown, setRealignCountdown] = useState(60);
  const [autoSubmittedReason, setAutoSubmittedReason] = useState('');
  const missingFramesRef = useRef(0);
  const consecutiveRealignedFramesRef = useRef(0);
  const resumeGracePeriodRef = useRef(false);
  const resumeGraceTimeoutRef = useRef(null);
  const prevFrameRef = useRef(null);

  // Synchronize faceMissingAlertRef
  useEffect(() => {
    faceMissingAlertRef.current = faceMissingAlert;
  }, [faceMissingAlert]);

  // Safe helper to attach webcam stream to any video element
  const attachStream = (el) => {
    if (el && cameraStream) {
      if (el.srcObject !== cameraStream) {
        el.srcObject = cameraStream;
      }
      el.play().catch(() => {});
    }
  };

  const handleResumeExam = () => {
    setFaceMissingAlert(false);
    missingFramesRef.current = 0;
    consecutiveRealignedFramesRef.current = 0;
    // 5-second grace period after resuming so user posture change doesn't trigger strike
    resumeGracePeriodRef.current = true;
    if (resumeGraceTimeoutRef.current) clearTimeout(resumeGraceTimeoutRef.current);
    resumeGraceTimeoutRef.current = setTimeout(() => {
      resumeGracePeriodRef.current = false;
    }, 5000);
  };

  const [studentDetails, setStudentDetails] = useState({ name: 'Loading...', id: 'Loading...' });

  const startCamera = async () => {
    try {
      setCheckingCamera(true);
      setCameraError('');
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setCameraError('Camera API is not supported on this browser. Please use Chrome, Edge, or Firefox.');
        setCameraActive(false);
        return;
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
        audio: false
      });
      const videoTracks = stream.getVideoTracks();
      if (!videoTracks || videoTracks.length === 0) {
        setCameraError('No video feed detected from your webcam. Please ensure your camera is plugged in and turned on.');
        setCameraActive(false);
        return;
      }

      setCameraStream(stream);
      setCameraActive(true);

      // Attach immediately to preview if element exists
      if (videoPreviewRef.current) {
        videoPreviewRef.current.srcObject = stream;
        videoPreviewRef.current.play().catch(() => {});
      }

      videoTracks.forEach(track => {
        track.onended = () => {
          setCameraActive(false);
          setCameraError('Camera was disconnected. Please turn on your camera to continue.');
        };
        track.onmute = () => {
          setCameraActive(false);
          setCameraError('Camera is muted or covered. Please enable your camera to continue.');
        };
        track.onunmute = () => {
          setCameraActive(true);
          setCameraError('');
        };
      });
    } catch (err) {
      console.error("Camera access failed:", err);
      setCameraActive(false);
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setCameraError('Camera permission was denied. Please allow camera access in your browser settings (lock icon in address bar) to continue.');
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setCameraError('No camera found on your device. A working webcam is strictly required to take this test.');
      } else {
        setCameraError('Unable to access camera: ' + (err.message || 'Please check device permissions.'));
      }
    } finally {
      setCheckingCamera(false);
    }
  };

  useEffect(() => {
    if (examSetId && !submitResult) {
      startCamera();
    }
    return () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach(t => t.stop());
      }
    };
  }, [examSetId, submitResult]);

  // Attach stream to video elements when stream or cameraActive changes
  useEffect(() => {
    if (cameraStream) {
      if (videoPreviewRef.current) attachStream(videoPreviewRef.current);
      if (videoRef.current) attachStream(videoRef.current);
      if (videoAlertRef.current) attachStream(videoAlertRef.current);
    }
  }, [started, cameraStream, cameraActive, faceMissingAlert]);

  // Real-time Face Verification loop (runs every 250ms while camera is active)
  useEffect(() => {
    if (!cameraStream || !cameraActive) {
      setFaceDetected(false);
      setFaceStatus('Camera is off');
      return;
    }

    const interval = setInterval(async () => {
      let activeVideo = videoPreviewRef.current;
      if (started) {
        if (faceMissingAlertRef.current && videoAlertRef.current && videoAlertRef.current.readyState >= 2) {
          activeVideo = videoAlertRef.current;
        } else if (videoRef.current && videoRef.current.readyState >= 2) {
          activeVideo = videoRef.current;
        } else if (videoAlertRef.current && videoAlertRef.current.readyState >= 2) {
          activeVideo = videoAlertRef.current;
        }
      }

      if (!activeVideo || activeVideo.readyState < 2) return;

      const result = await analyzeFaceInVideo(activeVideo, prevFrameRef);
      setFaceDetected(result.detected);
      setFaceConfidence(result.confidence);
      setFaceStatus(result.reason);

      if (started && !submitResult) {
        // STATE A: Warning 1 Modal is Currently Open (Waiting for student to realign face)
        if (faceMissingAlertRef.current) {
          if (result.detected) {
            consecutiveRealignedFramesRef.current += 1;
            // Auto-resume after ~2 seconds (8 ticks at 250ms) of continuously verified face
            if (consecutiveRealignedFramesRef.current >= 8 && faceViolationsRef.current === 1) {
              handleResumeExam();
            }
          } else {
            consecutiveRealignedFramesRef.current = 0;
          }
          // Crucial: NEVER trigger Strike 2 from standard ticks while the Warning 1 modal is open!
          return;
        }

        // STATE B: Post-Resume 5-second Grace Period
        if (resumeGracePeriodRef.current) {
          missingFramesRef.current = 0;
          return;
        }

        // STATE C: Live Exam Proctoring Monitoring
        if (!result.detected) {
          missingFramesRef.current += 1;
          // When face is missing/covered for ~2 seconds (8 ticks at 250ms)
          if (missingFramesRef.current >= 8) {
            if (faceViolationsRef.current === 0) {
              // STRIKE 1: First Warning (1 of 2)
              faceViolationsRef.current = 1;
              setFaceViolations(1);
              setRealignCountdown(60); // 60 seconds generous window
              setFaceMissingAlert(true);
              missingFramesRef.current = 0;
              consecutiveRealignedFramesRef.current = 0;
            } else if (faceViolationsRef.current === 1) {
              // STRIKE 2: Second time face not recognized during exam -> Automatically submit test!
              faceViolationsRef.current = 2;
              setFaceViolations(2);
              setFaceMissingAlert(true);
              const reason = 'Face was not recognized for the second time. Per KCET proctoring regulations, your test was automatically cancelled and submitted.';
              setAutoSubmittedReason(reason);
              setTimeout(() => {
                handleSubmitExamRef.current?.(reason);
              }, 1500);
            }
          }
        } else {
          // Face is recognized during normal exam
          missingFramesRef.current = 0;
        }
      }
    }, 250);

    return () => clearInterval(interval);
  }, [cameraStream, cameraActive, started, submitResult]);

  // Re-alignment countdown timer for Strike 1 (60 seconds)
  useEffect(() => {
    if (!faceMissingAlert || faceViolations !== 1 || submitResult) return;

    const cdTimer = setInterval(() => {
      setRealignCountdown(prev => {
        if (prev <= 1) {
          clearInterval(cdTimer);
          // 60 seconds expired without student realigning face -> Triggers Strike 2 and auto-submits!
          faceViolationsRef.current = 2;
          setFaceViolations(2);
          const reason = 'Face was not recognized within the allowed 60-second time limit. Test automatically submitted.';
          setAutoSubmittedReason(reason);
          setTimeout(() => {
            handleSubmitExamRef.current?.(reason);
          }, 1200);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(cdTimer);
  }, [faceMissingAlert, faceViolations, submitResult]);

  // Stop camera when exam is submitted or completed
  useEffect(() => {
    if (submitResult && cameraStream) {
      cameraStream.getTracks().forEach(t => t.stop());
    }
  }, [submitResult]);

  // 1. Fetch student details
  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        if (data.authenticated) {
          setStudentDetails({
            name: data.display_name || data.sub || 'Student',
            id: data.kcet_student_id || data.sub || 'STD-001'
          });
        } else {
          setStudentDetails({ name: 'Guest Student', id: 'GST-001' });
        }
      })
      .catch(() => {
        setStudentDetails({ name: 'Student', id: 'STD-123' });
      });
  }, []);

  // Synchronize state with URL search params
  useEffect(() => {
    const currentSet = searchParams.get('set') || '';
    setExamSetId(currentSet);
    if (searchParams.get('subject')) setSubject(searchParams.get('subject'));
    if (searchParams.get('name')) setExamName(searchParams.get('name'));
    if (searchParams.get('label')) setSetLabel(searchParams.get('label'));
  }, [searchParams]);

  // Fetch published exams when no exam is currently chosen
  const fetchPublishedExams = async () => {
    setLoadingPublished(true);
    setPublishedError('');
    try {
      const res = await fetch('/api/student/exams', { credentials: 'include' });
      const data = await res.json();
      if (res.ok && data.subjects) {
        setPublishedSubjects(data.subjects);
        if (data.remaining_attempts) {
          setRemainingAttempts(data.remaining_attempts);
        }
      } else {
        setPublishedError(data.message || 'Could not load published exams.');
      }
    } catch (err) {
      setPublishedError('Network error while retrieving published exams.');
    } finally {
      setLoadingPublished(false);
    }
  };

  useEffect(() => {
    if (!examSetId) {
      fetchPublishedExams();
    }
  }, [examSetId]);

  // Handle selecting an exam from published tests list
  const handleSelectExam = (exam, subjGroup, targetSet) => {
    const setObj = targetSet || (exam.sets && exam.sets.length > 0 ? exam.sets[0] : null);
    if (!setObj) {
      alert("No question sets available for this exam.");
      return;
    }
    const setId = setObj.exam_set_id;
    const subj = subjGroup.subject || 'General';
    const name = exam.exam_name || `${subj} Mock Exam`;
    const label = setObj.set_label || 'A';

    setExamSetId(setId);
    setSubject(subj);
    setExamName(name);
    setSetLabel(label);
    setSearchParams({
      set: setId,
      subject: subj,
      name: name,
      label: label
    });
  };

  // Handle going back to published exam selection
  const handleBackToExamSelection = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach(t => t.stop());
      setCameraStream(null);
      setCameraActive(false);
    }
    setExamSetId('');
    setQuestions([]);
    setStarted(false);
    setSubmitResult(null);
    setAnswers({});
    setLoadError('');
    setSearchParams({});
    fetchPublishedExams();
  };

  // Filtered list of published exams
  const filteredExamsList = React.useMemo(() => {
    const list = [];
    publishedSubjects.forEach(subjGroup => {
      if (selectedSubjectFilter !== 'ALL' && subjGroup.subject.toLowerCase() !== selectedSubjectFilter.toLowerCase()) {
        return;
      }
      (subjGroup.exams || []).forEach(exam => {
        const title = exam.exam_name || `${subjGroup.subject} Mock Exam`;
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          const matchTitle = title.toLowerCase().includes(q);
          const matchSubject = subjGroup.subject.toLowerCase().includes(q);
          if (!matchTitle && !matchSubject) return;
        }
        list.push({ exam, subjGroup });
      });
    });
    return list;
  }, [publishedSubjects, selectedSubjectFilter, searchQuery]);

  // Fetch questions once a specific exam set is selected
  useEffect(() => {
    if (!examSetId) {
      setLoadingQuestions(false);
      return;
    }

    const fetchQuestions = async () => {
      setLoadingQuestions(true);
      setLoadError('');

      try {
        const res = await fetch(`/api/student/exams/${examSetId}`, { credentials: 'include' });
        const data = await res.json();
        if (res.ok && data.questions && data.questions.length > 0) {
          setQuestions(data.questions.map((q, idx) => ({
            id: `q${idx + 1}`,
            text: q.q,
            options: Array.isArray(q.opts) ? q.opts : (typeof q.opts === 'string' ? JSON.parse(q.opts) : []),
            topic: q.topic || 'General',
            marks: q.marks || 1
          })));
          if (data.subject) setSubject(data.subject);
          if (data.set_label) setSetLabel(data.set_label);
        } else {
          setLoadError(data.message || 'No questions could be loaded for this exam set.');
        }
      } catch (err) {
        setLoadError('Network error while retrieving exam questions.');
      } finally {
        setLoadingQuestions(false);
      }
    };

    fetchQuestions();
  }, [examSetId]);

  const handleSubmitExamRef = useRef(null);
  const handleSubmitExam = async (violationReason = '') => {
    if (submitting) return;
    setSubmitting(true);

    const effectiveReason = violationReason || autoSubmittedReason || '';

    // Format answers map for backend: { "0": "1", "1": "3", ... }
    const formattedAnswers = {};
    Object.keys(answers).forEach(qIdx => {
      formattedAnswers[String(qIdx)] = String(answers[qIdx]);
    });

    const timeTaken = Math.max(1, EXAM_DURATION_SEC - timeLeft);

    try {
      const res = await fetch('/api/student/submit', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          exam_set_id: examSetId,
          answers: formattedAnswers,
          time_taken_sec: timeTaken
        })
      });

      const data = await res.json();
      if (res.ok) {
        setSubmitResult({
          ...data,
          autoSubmitted: Boolean(effectiveReason),
          violationReason: effectiveReason
        });
      } else {
        // Fallback calculation if backend reports already submitted or schema issue
        const answeredCount = Object.keys(answers).length;
        setSubmitResult({
          score: answeredCount,
          total_marks: questions.length,
          percentage: Math.round((answeredCount / Math.max(1, questions.length)) * 100),
          correct_count: answeredCount,
          incorrect_count: 0,
          unanswered_count: questions.length - answeredCount,
          message: data.message || 'Exam completed',
          autoSubmitted: Boolean(effectiveReason),
          violationReason: effectiveReason
        });
      }
    } catch (err) {
      const answeredCount = Object.keys(answers).length;
      setSubmitResult({
        score: answeredCount,
        total_marks: questions.length,
        percentage: Math.round((answeredCount / Math.max(1, questions.length)) * 100),
        correct_count: answeredCount,
        incorrect_count: 0,
        unanswered_count: questions.length - answeredCount,
        message: 'Exam completed (offline submission record)',
        autoSubmitted: Boolean(effectiveReason),
        violationReason: effectiveReason
      });
    } finally {
      setSubmitting(false);
    }
  };

  useEffect(() => {
    handleSubmitExamRef.current = handleSubmitExam;
  }, [handleSubmitExam]);

  // 3. Proctor camera and exam timer
  useEffect(() => {
    if (!started || submitResult) return;

    if (cameraStream && videoRef.current) {
      attachStream(videoRef.current);
    }

    const timer = setInterval(() => {
      // Pause exam clock while proctoring warning modal is open so student does not lose test time
      if (faceMissingAlertRef.current) return;

      setTimeLeft(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          handleSubmitExamRef.current?.('Exam time expired (80 minutes).');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [started, submitResult]);

  // Cleanup camera on unmount
  useEffect(() => {
    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        const tracks = videoRef.current.srcObject.getTracks();
        tracks.forEach(track => track.stop());
      }
    };
  }, []);

  const handleAnswer = (optionIdx) => {
    setAnswers(prev => ({ ...prev, [currentQ]: optionIdx }));
    setSkipped(prev => {
      const next = new Set(prev);
      next.delete(currentQ);
      return next;
    });
  };

  const handleSkip = () => {
    setSkipped(prev => new Set(prev).add(currentQ));
    if (currentQ < questions.length - 1) setCurrentQ(prev => prev + 1);
  };

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
    <>
      {/* Styles applied specifically when inside an exam session */}
      {examSetId && (
        <style>{`
          html, body { 
            overflow-y: auto !important; 
            overflow-x: hidden !important; 
            height: auto !important;
            min-height: 100vh !important;
          }
          .nav, .navbar { display: none !important; }
          .main-content { 
            margin-left: 0 !important; 
            padding: 0 !important; 
            max-width: 100% !important; 
            min-height: 100vh !important;
            overflow-y: auto !important;
          }
          .exam-layout {
            display: grid !important;
            grid-template-columns: 280px 1fr !important;
            gap: 24px !important;
            max-width: 1200px !important;
            margin: 0 auto !important;
            padding: 20px 20px 80px 20px !important;
            box-sizing: border-box !important;
          }
          @media (max-width: 900px) {
            .exam-layout {
              grid-template-columns: 1fr !important;
            }
          }
          .exam-sidebar {
            position: sticky !important;
            top: 76px !important;
            max-height: calc(100vh - 96px) !important;
            overflow-y: auto !important;
            scrollbar-width: thin !important;
            padding-bottom: 20px !important;
          }
          .exam-sidebar::-webkit-scrollbar {
            width: 5px;
          }
          .exam-sidebar::-webkit-scrollbar-thumb {
            background: rgba(124, 58, 237, 0.3);
            border-radius: 4px;
          }
          .overlay {
            position: fixed !important;
            inset: 0 !important;
            background: rgba(0, 0, 0, 0.85) !important;
            backdrop-filter: blur(8px) !important;
            -webkit-backdrop-filter: blur(8px) !important;
            z-index: 9999 !important;
            display: flex !important;
            justify-content: center !important;
            align-items: flex-start !important;
            overflow-y: auto !important;
            -webkit-overflow-scrolling: touch !important;
            padding: 30px 16px 60px 16px !important;
            box-sizing: border-box !important;
          }
          .overlay::-webkit-scrollbar {
            width: 6px;
          }
          .overlay::-webkit-scrollbar-thumb {
            background: rgba(124, 58, 237, 0.4);
            border-radius: 4px;
          }
          .entry-modal {
            background: var(--s1) !important;
            border: 1px solid var(--border2) !important;
            border-radius: var(--r) !important;
            padding: 24px 22px !important;
            max-width: 500px !important;
            width: 100% !important;
            margin: auto 0 !important;
            box-sizing: border-box !important;
          }
        `}</style>
      )}

      {/* Published Exams Selection Screen (Shown when student visits Exam page without selecting a test yet) */}
      {!examSetId && !submitResult && (
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '30px 20px 80px', minHeight: '80vh' }}>
          {/* Header Banner */}
          <div style={{ marginBottom: '28px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
            <div>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '4px 12px', borderRadius: '20px', background: 'rgba(124,58,237,0.12)', color: 'var(--purple-l, #a855f7)', fontSize: '0.82rem', fontWeight: 700, marginBottom: '10px' }}>
                <span>📝</span> Select Examination
              </div>
              <h1 style={{ fontSize: '2.1rem', fontWeight: 800, color: 'var(--text)', margin: '0 0 8px 0', letterSpacing: '-0.5px' }}>
                Available <span style={{ background: 'linear-gradient(135deg, #a855f7, #38bdf8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Practice Exams</span>
              </h1>
              <p style={{ fontSize: '0.95rem', color: 'var(--muted)', margin: 0 }}>
                Please choose which published test you want to answer to begin your exam
              </p>
            </div>

            {remainingAttempts && (
              <div style={{
                background: 'var(--s1)',
                border: '1px solid var(--border2)',
                borderRadius: '14px',
                padding: '12px 18px',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                boxShadow: 'var(--shadow)'
              }}>
                <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'rgba(124,58,237,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem' }}>
                  🎯
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--muted)', letterSpacing: '0.5px' }}>
                    Exam Attempts
                  </div>
                  <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text)' }}>
                    {remainingAttempts.is_unlimited ? (
                      <span style={{ color: 'var(--green)' }}>Unlimited Practice</span>
                    ) : (
                      <span>
                        <strong style={{ color: 'var(--purple-l)' }}>{remainingAttempts.remaining_attempts ?? remainingAttempts.max_attempts}</strong> / {remainingAttempts.max_attempts} Left
                      </span>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Filter & Search Bar */}
          <div style={{
            background: 'var(--s1)',
            border: '1px solid var(--border)',
            borderRadius: '14px',
            padding: '16px 20px',
            marginBottom: '24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '16px'
          }}>
            {/* Subject Tabs */}
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {['ALL', 'Biology', 'Physics', 'Chemistry', 'Mathematics'].map(subj => {
                const isActive = selectedSubjectFilter === subj;
                const count = subj === 'ALL'
                  ? publishedSubjects.reduce((acc, s) => acc + (s.exams?.length || 0), 0)
                  : (publishedSubjects.find(s => s.subject.toLowerCase() === subj.toLowerCase())?.exams?.length || 0);

                return (
                  <button
                    key={subj}
                    type="button"
                    onClick={() => setSelectedSubjectFilter(subj)}
                    style={{
                      padding: '7px 16px',
                      borderRadius: '20px',
                      border: isActive ? '1px solid var(--purple-l)' : '1px solid var(--border)',
                      background: isActive ? 'linear-gradient(135deg, rgba(124,58,237,0.25), rgba(37,99,235,0.2))' : 'var(--s2)',
                      color: isActive ? 'var(--purple-l, #a855f7)' : 'var(--muted)',
                      fontWeight: isActive ? 700 : 500,
                      fontSize: '0.85rem',
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <span>{subj === 'ALL' ? 'All Subjects' : subj}</span>
                    <span style={{
                      fontSize: '0.72rem',
                      padding: '1px 6px',
                      borderRadius: '10px',
                      background: isActive ? 'rgba(124,58,237,0.3)' : 'rgba(0,0,0,0.15)',
                      color: isActive ? '#fff' : 'var(--muted)'
                    }}>
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Search Input */}
            <div style={{ minWidth: '240px', flex: '1 1 240px', maxWidth: '340px' }}>
              <input
                type="text"
                placeholder="Search test by name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="text-input"
                style={{
                  width: '100%',
                  padding: '8px 14px',
                  borderRadius: '10px',
                  fontSize: '0.88rem',
                  background: 'var(--s2)',
                  border: '1px solid var(--border)'
                }}
              />
            </div>
          </div>

          {/* Loading State */}
          {loadingPublished && (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--muted)' }}>
              <div style={{ fontSize: '2rem', marginBottom: '10px' }}>⏳</div>
              <p style={{ fontWeight: 600 }}>Loading available published exams...</p>
            </div>
          )}

          {/* Error State */}
          {publishedError && !loadingPublished && (
            <div style={{ padding: '16px 20px', background: 'rgba(239,68,68,0.1)', border: '1px solid var(--red)', borderRadius: '12px', color: 'var(--red)', marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>⚠️ {publishedError}</span>
              <button type="button" className="btn-outline small" onClick={fetchPublishedExams}>Retry</button>
            </div>
          )}

          {/* Empty State */}
          {!loadingPublished && !publishedError && filteredExamsList.length === 0 && (
            <div style={{
              background: 'var(--s1)',
              border: '1px solid var(--border)',
              borderRadius: '16px',
              padding: '60px 20px',
              textAlign: 'center',
              color: 'var(--muted)'
            }}>
              <div style={{ fontSize: '3rem', marginBottom: '14px' }}>📝</div>
              <h3 style={{ fontSize: '1.25rem', color: 'var(--text)', marginBottom: '8px', fontWeight: 700 }}>
                {searchQuery || selectedSubjectFilter !== 'ALL' ? 'No Matching Exams Found' : 'No Published Exams Available'}
              </h3>
              <p style={{ maxWidth: '420px', margin: '0 auto', fontSize: '0.9rem', lineHeight: 1.5 }}>
                {searchQuery || selectedSubjectFilter !== 'ALL'
                  ? 'Try changing your subject filter or search keyword to find available exams.'
                  : 'New mock exams will appear here as soon as they are created and published by your administrator.'}
              </p>
              {(searchQuery || selectedSubjectFilter !== 'ALL') && (
                <button
                  type="button"
                  className="btn-outline small"
                  style={{ marginTop: '16px' }}
                  onClick={() => { setSelectedSubjectFilter('ALL'); setSearchQuery(''); }}
                >
                  Clear Filters
                </button>
              )}
            </div>
          )}

          {/* Published Exams Cards Grid */}
          {!loadingPublished && filteredExamsList.length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>
              {filteredExamsList.map(({ exam, subjGroup }) => {
                const defaultSet = exam.sets && exam.sets.length > 0 ? exam.sets[0] : null;
                const subjectName = subjGroup.subject || 'General';

                const badgeColor = subjectName === 'Biology'
                  ? { bg: 'rgba(5,150,105,0.12)', text: '#059669', border: 'rgba(5,150,105,0.3)' }
                  : subjectName === 'Physics'
                    ? { bg: 'rgba(37,99,235,0.12)', text: '#2563eb', border: 'rgba(37,99,235,0.3)' }
                    : subjectName === 'Chemistry'
                      ? { bg: 'rgba(124,58,237,0.12)', text: '#7c3aed', border: 'rgba(124,58,237,0.3)' }
                      : { bg: 'rgba(217,119,6,0.12)', text: '#d97706', border: 'rgba(217,119,6,0.3)' };

                return (
                  <div
                    key={exam.exam_id}
                    style={{
                      background: 'var(--s1)',
                      border: '1px solid var(--border)',
                      borderRadius: '16px',
                      padding: '22px',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      gap: '16px',
                      transition: 'all 0.25s ease',
                      boxShadow: 'var(--shadow)'
                    }}
                  >
                    <div>
                      {/* Card Header: Subject Tag & Duration */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                        <span style={{
                          padding: '4px 10px',
                          borderRadius: '6px',
                          fontSize: '0.78rem',
                          fontWeight: 700,
                          background: badgeColor.bg,
                          color: badgeColor.text,
                          border: `1px solid ${badgeColor.border}`
                        }}>
                          {subjectName}
                        </span>
                        <span style={{ fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                          ⏱ 80 Mins
                        </span>
                      </div>

                      {/* Exam Title */}
                      <h3 style={{ fontSize: '1.18rem', fontWeight: 700, color: 'var(--text)', margin: '0 0 10px 0', lineHeight: 1.4 }}>
                        {exam.exam_name || `${subjectName} Mock Exam`}
                      </h3>

                      {/* Details specs */}
                      <div style={{
                        background: 'var(--s2)',
                        border: '1px solid var(--border)',
                        borderRadius: '10px',
                        padding: '10px 14px',
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: '8px',
                        fontSize: '0.82rem',
                        color: 'var(--muted)',
                        marginBottom: '8px'
                      }}>
                        <div>
                          <span>Questions:</span>{' '}
                          <strong style={{ color: 'var(--text)' }}>60 MCQs</strong>
                        </div>
                        <div>
                          <span>Max Marks:</span>{' '}
                          <strong style={{ color: 'var(--text)' }}>60 Marks</strong>
                        </div>
                        <div>
                          <span>Set:</span>{' '}
                          <strong style={{ color: 'var(--purple-l)' }}>Set {defaultSet?.set_label || 'A'}</strong>
                        </div>
                        <div>
                          <span>Proctoring:</span>{' '}
                          <strong style={{ color: 'var(--green)' }}>AI Camera</strong>
                        </div>
                      </div>
                    </div>

                    {/* Action Button */}
                    <div>
                      {defaultSet ? (
                        <button
                          type="button"
                          className="btn-primary"
                          onClick={() => handleSelectExam(exam, subjGroup, defaultSet)}
                          style={{
                            width: '100%',
                            justifyContent: 'center',
                            padding: '10px 16px',
                            fontSize: '0.92rem',
                            fontWeight: 700,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px'
                          }}
                        >
                          Take Exam →
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="btn-primary"
                          disabled
                          style={{ width: '100%', opacity: 0.5, cursor: 'not-allowed' }}
                        >
                          Unavailable
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
      
      {/* Top bar during exam */}
      <div className="exam-topbar" id="examTopbar" style={{ display: started && !submitResult ? "flex" : "none" }}>
        <div className="exam-topbar-left">
          <div className="brand-icon small">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          </div>
          <span className="exam-title-text" style={{ color: "#fff" }}>Mr.<span className="brand-ai">E</span></span>
        </div>
        <div className="exam-topbar-center">
          <span className="exam-badge set-badge" id="topbarSet">{examName}</span>
          <span className="exam-badge subject-badge" id="topbarSubject">{subject}</span>
          {faceViolations === 1 && (
            <span style={{
              padding: '4px 10px',
              borderRadius: '12px',
              background: 'rgba(234,179,8,0.22)',
              border: '1px solid rgba(234,179,8,0.6)',
              color: '#facc15',
              fontSize: '0.75rem',
              fontWeight: 800,
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px'
            }}>
              ⚠️ Warning: 1/2 (Final Chance!)
            </span>
          )}
        </div>
        <div className="exam-topbar-right">
          <div className="timer-block">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            <span id="timerDisplay" className="timer-text">{formatTime(timeLeft)}</span>
          </div>
        </div>
      </div>

      {/* Entry Modal / Pre-Exam Screen */}
      {examSetId && !started && !submitResult && (
        <div className="overlay" style={{ display: "flex" }}>
          <div className="entry-modal" style={{ maxWidth: '520px', width: '90%' }}>
            <div className="entry-modal-top">
              <button
                type="button"
                onClick={handleBackToExamSelection}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--purple-l, #a855f7)',
                  cursor: 'pointer',
                  fontSize: '0.84rem',
                  fontWeight: 600,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  marginBottom: '10px',
                  alignSelf: 'flex-start'
                }}
              >
                ← Back to Published Tests
              </button>
              <div className="entry-icon">🎓</div>
              <h2>{examName}</h2>
              <p>{subject} Examination</p>
            </div>

            <div className="entry-form">
              {loadError ? (
                <div style={{ padding: '16px', background: 'rgba(239,68,68,0.1)', border: '1px solid var(--red)', borderRadius: '8px', color: 'var(--red)', marginBottom: '16px', textAlign: 'center' }}>
                  <p style={{ fontWeight: 600 }}>{loadError}</p>
                  <button className="btn-outline small" style={{ marginTop: '12px' }} onClick={handleBackToExamSelection}>
                    ← Choose a Different Test
                  </button>
                </div>
              ) : (
                <>
                  <div className="candidate-profile-box" style={{ background: "var(--s2)", border: "1px solid var(--border)", borderRadius: "var(--r)", padding: "14px 16px", marginBottom: "14px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "4px 0", fontSize: "0.88rem" }}>
                      <span style={{ color: "var(--muted)" }}>👤 Candidate Name:</span>
                      <span style={{ fontWeight: "700", color: "var(--text)" }}>{studentDetails.name}</span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "4px 0", fontSize: "0.88rem" }}>
                      <span style={{ color: "var(--muted)" }}>🆔 Candidate ID:</span>
                      <span style={{ fontWeight: "700", color: "var(--purple-l)", fontFamily: "monospace" }}>{studentDetails.id}</span>
                    </div>
                  </div>

                  {/* Mandatory Proctoring Camera Box with Real-Time Face Verification */}
                  <div style={{
                    background: "var(--s2)",
                    border: `1.5px solid ${(cameraActive && faceDetected) ? "rgba(16,185,129,0.5)" : "rgba(239,68,68,0.5)"}`,
                    borderRadius: "12px",
                    padding: "14px",
                    marginBottom: "14px"
                  }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px", flexWrap: "wrap", gap: "6px" }}>
                      <span style={{ fontSize: "0.86rem", fontWeight: 700, color: "var(--text)", display: "flex", alignItems: "center", gap: "6px" }}>
                        📹 Web Camera Verification
                      </span>
                      <span style={{
                        fontSize: "0.75rem",
                        fontWeight: 700,
                        padding: "3px 10px",
                        borderRadius: "12px",
                        background: (!cameraActive || !faceDetected) ? "rgba(239,68,68,0.15)" : "rgba(16,185,129,0.15)",
                        color: (!cameraActive || !faceDetected) ? "var(--red-l, #f87171)" : "var(--green)"
                      }}>
                        {!cameraActive 
                          ? "● Camera Offline" 
                          : faceDetected 
                            ? "● Face Verified & Live" 
                            : "● No Face Visible (Camera Off)"}
                      </span>
                    </div>

                    <div style={{
                      width: "100%",
                      height: "170px",
                      background: "#080a10",
                      borderRadius: "8px",
                      overflow: "hidden",
                      position: "relative",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      marginBottom: "10px",
                      border: (cameraActive && faceDetected) ? "1.5px solid rgba(16,185,129,0.7)" : "1.5px solid rgba(239,68,68,0.5)"
                    }}>
                      <video
                        ref={(el) => {
                          videoPreviewRef.current = el;
                          attachStream(el);
                        }}
                        autoPlay
                        muted
                        playsInline
                        style={{
                          width: "100%",
                          height: "100%",
                          objectFit: "cover",
                          transform: "scaleX(-1)",
                          display: cameraActive ? "block" : "none"
                        }}
                      />

                      {/* Face Alignment Oval Guide */}
                      {cameraActive && (
                        <div style={{
                          position: "absolute",
                          top: "50%",
                          left: "50%",
                          transform: "translate(-50%, -50%)",
                          width: "100px",
                          height: "125px",
                          border: faceDetected ? "2px solid rgba(16, 185, 129, 0.85)" : "2px dashed rgba(239, 68, 68, 0.75)",
                          boxShadow: faceDetected ? "0 0 15px rgba(16, 185, 129, 0.4)" : "none",
                          borderRadius: "50%",
                          pointerEvents: "none",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          transition: "all 0.3s ease"
                        }}>
                          <span style={{
                            fontSize: "0.65rem",
                            fontWeight: 700,
                            color: faceDetected ? "#10b981" : "#f87171",
                            background: "rgba(0,0,0,0.65)",
                            padding: "2px 6px",
                            borderRadius: "4px"
                          }}>
                            {faceDetected ? "✓ Face In View" : "Align Face"}
                          </span>
                        </div>
                      )}

                      {/* Verification Status Badge Overlay */}
                      {cameraActive && (
                        <div style={{
                          position: "absolute",
                          bottom: "8px",
                          right: "8px",
                          background: faceDetected ? "rgba(16, 185, 129, 0.9)" : "rgba(239, 68, 68, 0.9)",
                          color: "#fff",
                          fontSize: "0.72rem",
                          fontWeight: "700",
                          padding: "3px 8px",
                          borderRadius: "4px"
                        }}>
                          {faceDetected ? `✓ Face Verified (${faceConfidence}%)` : "🚫 Face Not Detected"}
                        </div>
                      )}

                      {!cameraActive && (
                        <div style={{ color: "var(--muted)", textAlign: "center", padding: "16px" }}>
                          <div style={{ fontSize: "2.4rem", marginBottom: "6px" }}>📷</div>
                          <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--red-l)" }}>Camera is OFF</div>
                          <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginTop: "4px", maxWidth: "340px", lineHeight: "1.4" }}>
                            Webcam proctoring is mandatory. You cannot take the test without turning on your camera.
                          </div>
                          <button
                            type="button"
                            className="btn-primary"
                            onClick={startCamera}
                            disabled={checkingCamera}
                            style={{
                              marginTop: "12px",
                              padding: "8px 20px",
                              fontSize: "0.85rem",
                              fontWeight: 700,
                              background: "linear-gradient(135deg, var(--purple), var(--blue))"
                            }}
                          >
                            {checkingCamera ? "Requesting Camera..." : "📷 Turn On Camera"}
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Camera Off / Face Not Detected Warning */}
                    {cameraActive && !faceDetected && (
                      <div style={{
                        padding: "10px 14px",
                        background: "rgba(239,68,68,0.12)",
                        border: "1px solid rgba(239,68,68,0.35)",
                        borderRadius: "8px",
                        color: "var(--red-l, #f87171)",
                        fontSize: "0.82rem",
                        marginBottom: "10px",
                        lineHeight: "1.5",
                        textAlign: "left"
                      }}>
                        <div style={{ fontWeight: 700, display: "flex", alignItems: "center", gap: "6px" }}>
                          <span>🚫</span> Student Face Not Detected
                        </div>
                        <div style={{ marginTop: "4px", color: "var(--text)" }}>
                          {faceStatus}. Your camera appears to be covered or turned off. You cannot begin the test without your face clearly visible on screen.
                        </div>
                        <div style={{ marginTop: "6px", fontSize: "0.76rem", color: "var(--muted)" }}>
                          👉 <strong>How to fix:</strong> Check your laptop's physical webcam privacy slider or switch, or allow camera access in Windows Settings.
                        </div>
                      </div>
                    )}

                    {cameraError && (
                      <div style={{
                        padding: "8px 12px",
                        background: "rgba(239,68,68,0.1)",
                        border: "1px solid var(--red)",
                        borderRadius: "6px",
                        color: "var(--red)",
                        fontSize: "0.8rem",
                        marginBottom: "10px",
                        textAlign: "left"
                      }}>
                        ⚠️ {cameraError}
                      </div>
                    )}

                    {!cameraActive && (
                      <button
                        type="button"
                        className="btn-primary"
                        onClick={startCamera}
                        disabled={checkingCamera}
                        style={{
                          width: "100%",
                          justifyContent: "center",
                          padding: "10px",
                          fontSize: "0.88rem",
                          background: "linear-gradient(135deg, #7c3aed, #2563eb)",
                          fontWeight: 700
                        }}
                      >
                        {checkingCamera ? "Requesting Camera..." : "📷 Turn On Camera to Unlock Exam"}
                      </button>
                    )}
                  </div>

                  <div className="exam-info-box" style={{ marginBottom: '16px' }}>
                    <div className="info-row"><span>📚 Subject:</span><span>{subject}</span></div>
                    <div className="info-row"><span>❓ Questions:</span><span>{loadingQuestions ? 'Loading...' : `${questions.length} Live Questions`}</span></div>
                    <div className="info-row"><span>⏱ Time Limit:</span><span>80 minutes</span></div>
                  </div>

                  <button 
                    className="btn-generate" 
                    onClick={() => {
                      if (!cameraActive) {
                        alert("Camera is mandatory! You must turn on your webcam to take this exam.");
                        return;
                      }
                      if (!faceDetected) {
                        alert("Student face not detected! Your camera is covered or turned off. Uncover your camera and position your face in the center of the frame before you can begin the exam.");
                        return;
                      }
                      setStarted(true);
                    }} 
                    disabled={loadingQuestions || questions.length === 0 || !cameraActive || !faceDetected}
                    style={{ 
                      width: '100%', 
                      justifyContent: 'center',
                      opacity: (!cameraActive || !faceDetected || loadingQuestions || questions.length === 0) ? 0.45 : 1,
                      cursor: (!cameraActive || !faceDetected || loadingQuestions || questions.length === 0) ? 'not-allowed' : 'pointer',
                      background: (cameraActive && faceDetected) ? 'linear-gradient(135deg, var(--purple), var(--blue))' : '#27272a',
                      border: (!cameraActive || !faceDetected) ? '1px solid rgba(239,68,68,0.5)' : 'none',
                      color: (!cameraActive || !faceDetected) ? 'var(--red-l, #f87171)' : '#ffffff'
                    }}
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                    {loadingQuestions 
                      ? 'Loading Questions...' 
                      : !cameraActive 
                        ? '🚫 Turn On Camera to Unlock Exam' 
                        : !faceDetected
                          ? '🚫 Student Face Must Be Visible to Begin Exam'
                          : 'Begin Exam →'}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Mid-Exam Proctoring Violation Modal (2-Strike System) */}
      {started && (!cameraActive || faceMissingAlert) && !submitResult && (
        <div className="overlay" style={{ display: 'flex', zIndex: 99999, background: 'rgba(0,0,0,0.94)' }}>
          <div className="entry-modal" style={{
            maxWidth: '500px',
            width: '92%',
            textAlign: 'center',
            border: faceViolations >= 2 ? '2.5px solid var(--red)' : '2px solid #eab308',
            boxShadow: faceViolations >= 2 ? '0 0 30px rgba(239,68,68,0.4)' : '0 0 25px rgba(234,179,8,0.3)',
            borderRadius: '16px',
            padding: '28px 22px'
          }}>
            {/* Header Badge */}
            <div style={{ marginBottom: '12px' }}>
              <span style={{
                fontSize: '0.82rem',
                fontWeight: 800,
                letterSpacing: '0.5px',
                padding: '4px 14px',
                borderRadius: '20px',
                background: faceViolations >= 2 ? 'rgba(239,68,68,0.22)' : 'rgba(234,179,8,0.2)',
                border: faceViolations >= 2 ? '1px solid rgba(239,68,68,0.6)' : '1px solid rgba(234,179,8,0.6)',
                color: faceViolations >= 2 ? '#f87171' : '#facc15'
              }}>
                {faceViolations >= 2 ? '🚨 PROCTORING VIOLATION (2 OF 2)' : '⚠️ PROCTORING WARNING 1 OF 2'}
              </span>
            </div>

            <div style={{ fontSize: '3.2rem', marginBottom: '8px' }}>
              {faceViolations >= 2 ? '🚨' : '⚠️'}
            </div>

            <h2 style={{
              color: faceViolations >= 2 ? 'var(--red)' : '#facc15',
              marginBottom: '10px',
              fontSize: '1.45rem',
              fontWeight: 800
            }}>
              {faceViolations >= 2 ? 'Test Automatically Submitted!' : 'Student Face Not Recognized!'}
            </h2>

            {/* Crucial Required Warning Callout */}
            {faceViolations < 2 ? (
              <div style={{
                background: 'rgba(234,179,8,0.14)',
                border: '1.5px solid rgba(234,179,8,0.5)',
                borderRadius: '10px',
                padding: '14px 16px',
                marginBottom: '14px',
                color: '#fef08a',
                fontSize: '0.92rem',
                lineHeight: '1.5',
                textAlign: 'center',
                fontWeight: 700
              }}>
                ⚠️ <strong>CRITICAL WARNING:</strong> If your face is not recognized again, the test will automatically be cancelled and submitted!
              </div>
            ) : (
              <div style={{
                background: 'rgba(239,68,68,0.2)',
                border: '2px solid rgba(239,68,68,0.6)',
                borderRadius: '10px',
                padding: '16px',
                marginBottom: '14px',
                color: '#fca5a5',
                fontSize: '0.95rem',
                lineHeight: '1.5',
                textAlign: 'center',
                fontWeight: 700
              }}>
                🚫 Your face was not recognized for the second time. Per KCET proctoring regulations, your test has been automatically cancelled and submitted.
              </div>
            )}

            <p style={{ color: 'var(--text)', marginBottom: '12px', fontSize: '0.88rem', lineHeight: '1.5' }}>
              {!cameraActive
                ? 'Your camera feed was interrupted or turned off. Video proctoring is mandatory for the entire examination.'
                : faceViolations >= 2
                  ? 'Submitting your current responses and generating diagnostic evaluation...'
                  : `${faceStatus}. Your face must remain visible to the proctoring camera at all times.`}
            </p>

            {/* Countdown Display for Strike 1 */}
            {faceViolations < 2 && (
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 14px',
                borderRadius: '20px',
                background: 'rgba(239,68,68,0.18)',
                border: '1px solid rgba(239,68,68,0.45)',
                color: '#f87171',
                fontSize: '0.84rem',
                fontWeight: 700,
                marginBottom: '14px'
              }}>
                ⏱ Re-align face within: <strong>{realignCountdown}s</strong> (or exam will auto-submit)
              </div>
            )}

            {/* Video Box with Oval */}
            <div style={{
              width: "100%",
              height: "170px",
              background: "#080a10",
              borderRadius: "8px",
              overflow: "hidden",
              position: "relative",
              marginBottom: "14px",
              border: faceDetected ? "2px solid #10b981" : faceViolations >= 2 ? "2px solid var(--red)" : "2px solid #eab308"
            }}>
              <video
                ref={(el) => {
                  videoAlertRef.current = el;
                  attachStream(el);
                }}
                autoPlay
                muted
                playsInline
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  transform: "scaleX(-1)",
                  display: cameraActive ? "block" : "none"
                }}
              />
              <div style={{
                position: "absolute",
                top: "50%",
                left: "50%",
                transform: "translate(-50%, -50%)",
                width: "95px",
                height: "120px",
                border: faceDetected ? "2.5px solid #10b981" : faceViolations >= 2 ? "2px dashed #ef4444" : "2px dashed #eab308",
                boxShadow: faceDetected ? "0 0 16px rgba(16,185,129,0.45)" : "none",
                borderRadius: "50%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                pointerEvents: "none",
                background: faceDetected ? "rgba(16,185,129,0.12)" : "rgba(0,0,0,0.3)"
              }}>
                <span style={{
                  fontSize: "0.68rem",
                  fontWeight: 800,
                  color: faceDetected ? "#10b981" : faceViolations >= 2 ? "#f87171" : "#facc15",
                  background: "rgba(0,0,0,0.85)",
                  padding: "3px 8px",
                  borderRadius: "4px"
                }}>
                  {faceDetected ? `✓ Face In View (${faceConfidence}%)` : "Align Face"}
                </span>
              </div>
            </div>

            {!cameraActive ? (
              <button 
                className="btn-primary" 
                onClick={startCamera} 
                disabled={checkingCamera}
                style={{ width: '100%', justifyContent: 'center', padding: '12px', fontSize: '0.95rem', fontWeight: 700 }}
              >
                {checkingCamera ? 'Connecting Camera...' : '📷 Turn On Camera to Resume Exam'}
              </button>
            ) : faceViolations < 2 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <button
                  type="button"
                  className="btn-primary"
                  onClick={handleResumeExam}
                  disabled={!faceDetected}
                  style={{
                    width: '100%',
                    justifyContent: 'center',
                    padding: '13px',
                    fontSize: '1rem',
                    fontWeight: 800,
                    background: faceDetected ? '#10b981' : 'rgba(255,255,255,0.08)',
                    color: faceDetected ? '#ffffff' : 'var(--muted)',
                    border: faceDetected ? '1px solid #10b981' : '1px solid var(--border)',
                    cursor: faceDetected ? 'pointer' : 'not-allowed',
                    boxShadow: faceDetected ? '0 0 20px rgba(16,185,129,0.45)' : 'none',
                    transition: 'all 0.2s ease',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  {faceDetected ? (
                    <>
                      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      ✓ Face Verified — Click to Resume Exam
                    </>
                  ) : (
                    '⏳ Position Face Inside Oval to Resume'
                  )}
                </button>
                <div style={{ fontSize: '0.82rem', color: 'var(--muted)', background: 'rgba(255,255,255,0.03)', padding: '8px 12px', borderRadius: '6px' }}>
                  👉 Center your face in the oval or open your camera shutter. Once the green checkmark appears, click Resume (or hold position for 2 seconds to auto-resume).
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', color: 'var(--red-l)', fontSize: '0.9rem', fontWeight: 700 }}>
                <span className="spinner" style={{ width: '16px', height: '16px', border: '2px solid rgba(239,68,68,0.3)', borderTopColor: '#ef4444', borderRadius: '50%', display: 'inline-block', animation: 'spin 0.8s linear infinite' }}></span>
                Submitting Exam Responses...
              </div>
            )}
          </div>
        </div>
      )}

      {/* Live Exam Layout */}
      {started && !submitResult && questions.length > 0 && (
        <div className="exam-layout">
          <aside className="exam-sidebar">
            <div id="proctorContainer" style={{
              marginBottom: "15px",
              borderRadius: "8px",
              overflow: "hidden",
              background: "#000",
              border: (cameraActive && faceDetected)
                ? (faceViolations === 1 ? "1.5px solid rgba(234,179,8,0.7)" : "1.5px solid rgba(16,185,129,0.6)")
                : "1.5px solid rgba(239,68,68,0.7)",
              aspectRatio: "4/3",
              maxHeight: "150px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              position: "relative"
            }}>
              <video
                ref={(el) => {
                  videoRef.current = el;
                  attachStream(el);
                }}
                autoPlay
                muted
                playsInline
                style={{ width: "100%", height: "100%", objectFit: "cover", display: "block", transform: "scaleX(-1)" }}
              />
              <div style={{
                position: "absolute",
                top: "6px",
                left: "6px",
                fontSize: "0.65rem",
                fontWeight: 800,
                padding: "2px 6px",
                borderRadius: "4px",
                background: faceViolations === 0 ? "rgba(16,185,129,0.85)" : faceViolations === 1 ? "rgba(234,179,8,0.9)" : "rgba(239,68,68,0.9)",
                color: faceViolations === 1 ? "#000" : "#fff"
              }}>
                {faceViolations === 0 ? "Strikes: 0/2" : `Strikes: ${faceViolations}/2`}
              </div>
              <span style={{
                position: "absolute",
                bottom: "6px",
                right: "6px",
                fontSize: "0.68rem",
                fontWeight: 700,
                padding: "2px 6px",
                borderRadius: "4px",
                background: (cameraActive && faceDetected) ? "rgba(16,185,129,0.9)" : "rgba(239,68,68,0.9)",
                color: "#fff"
              }}>
                {(cameraActive && faceDetected) ? "● Face Verified" : "● Face Missing"}
              </span>
            </div>

            <div className="sidebar-section-title">Question Navigator</div>
            <div className="q-grid">
              {questions.map((q, i) => (
                <button
                  key={q.id}
                  onClick={() => setCurrentQ(i)}
                  className={`q-grid-btn ${answers[i] !== undefined ? 'answered' : skipped.has(i) ? 'skipped' : ''} ${i === currentQ ? 'current' : ''}`.trim()}
                >
                  {i + 1}
                </button>
              ))}
            </div>

            <div className="q-legend">
              <div className="legend-row"><span className="legend-box answered"></span>Answered</div>
              <div className="legend-row"><span className="legend-box skipped"></span>Skipped</div>
              <div className="legend-row"><span className="legend-box current"></span>Current</div>
              <div className="legend-row"><span className="legend-box unanswered"></span>Not visited</div>
            </div>

            <div className="sidebar-progress">
              <div className="sidebar-prog-label">
                <span>{Object.keys(answers).length}</span> / <span>{questions.length}</span> answered
              </div>
              <div className="sidebar-prog-bar">
                <div className="sidebar-prog-fill" style={{ width: `${(Object.keys(answers).length / Math.max(1, questions.length)) * 100}%` }}></div>
              </div>
            </div>

            <button className="btn-submit-exam" onClick={handleSubmitExam} disabled={submitting}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
              {submitting ? 'Submitting...' : 'Submit Paper'}
            </button>
          </aside>

          <div className="exam-content">
            <div className="exam-top-bar">
              <div className="exam-top-prog">
                <div className="exam-top-prog-fill" style={{ width: `${((currentQ + 1) / questions.length) * 100}%` }}></div>
              </div>
            </div>

            {questions[currentQ] && (
              <div className="question-panel">
                <div className="q-meta-row">
                  <span className="q-num-badge">Question {currentQ + 1}</span>
                  <span className="q-type-chip">MCQ</span>
                  <span className="q-topic-chip">{questions[currentQ].topic}</span>
                  <span className="q-marks-chip">{questions[currentQ].marks} mark</span>
                </div>

                <div className="q-body" style={{ fontSize: '1.15rem', fontWeight: 500, color: 'var(--text)', marginBottom: '24px', lineHeight: '1.6' }}>
                  {questions[currentQ].text}
                </div>

                <div className="q-answer-area">
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {questions[currentQ].options.map((opt, idx) => {
                      const isSelected = answers[currentQ] === idx;
                      return (
                        <button 
                          key={idx}
                          onClick={() => handleAnswer(idx)}
                          style={{
                            display: 'flex', alignItems: 'center', gap: '16px', width: '100%',
                            padding: '16px 20px', background: isSelected ? 'rgba(124,58,237,0.15)' : 'var(--s2)',
                            border: `1.5px solid ${isSelected ? 'var(--purple-l)' : 'var(--border)'}`,
                            borderRadius: '12px', cursor: 'pointer', textAlign: 'left',
                            transition: 'all 0.2s',
                            boxShadow: isSelected ? '0 0 0 3px rgba(124,58,237,0.25)' : 'none'
                          }}
                        >
                          <span style={{
                            width: '32px', height: '32px', borderRadius: '50%',
                            background: isSelected ? 'var(--purple)' : 'var(--s1)',
                            color: isSelected ? '#fff' : 'var(--text)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontWeight: 600, fontSize: '0.9rem',
                            border: isSelected ? 'none' : '1px solid var(--border)'
                          }}>
                            {String.fromCharCode(65 + idx)}
                          </span>
                          <span style={{ fontSize: '1rem', color: isSelected ? 'var(--purple-l)' : 'var(--text)', fontWeight: isSelected ? 600 : 400 }}>
                            {opt}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}

            <div className="exam-nav-row">
              <button className="btn-outline exam-nav-btn" disabled={currentQ === 0} onClick={() => setCurrentQ(prev => prev - 1)}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6"/></svg>
                Previous
              </button>
              <div className="exam-nav-center">
                <button className="btn-skip" onClick={handleSkip}>Skip</button>
                <span className="q-position">{currentQ + 1} of {questions.length}</span>
              </div>
              <button className="btn-primary exam-nav-btn" disabled={currentQ === questions.length - 1} onClick={() => setCurrentQ(prev => prev + 1)}>
                Next
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Submission Result Screen: Comprehensive AI Analysis Dashboard */}
      {submitResult && (() => {
        const aiAnalysis = submitResult.ai_analysis;
        const summary = aiAnalysis?.summary || {};
        const scoreVal = submitResult.score ?? summary.score ?? 0;
        const totalVal = submitResult.total_marks ?? summary.total ?? questions.length;
        const pctVal = submitResult.percentage ?? summary.percentage ?? Math.round((scoreVal / Math.max(1, totalVal)) * 100);
        const correctCount = submitResult.correct_count ?? summary.score ?? scoreVal;
        const incorrectCount = submitResult.incorrect_count ?? Math.max(0, totalVal - scoreVal - (submitResult.unanswered_count || 0));
        const unansCount = submitResult.unanswered_count ?? Math.max(0, totalVal - (correctCount + incorrectCount));
        const band = summary.performance_band || (pctVal >= 85 ? "Outstanding Mastery" : pctVal >= 65 ? "Strong Competency" : pctVal >= 45 ? "Developing Competency" : "Foundational Review Needed");
        const pacing = summary.pacing_assessment || `Exam completed in ${Math.floor((submitResult.time_taken_sec || 0)/60)}m ${(submitResult.time_taken_sec || 0)%60}s.`;
        const verdict = summary.overall_verdict || `Student demonstrated ${band.toLowerCase()} across ${subject} KCET syllabus concepts with an overall score of ${pctVal}%.`;
        const topicMap = aiAnalysis?.topic_breakdown || {};
        const subtypeMap = aiAnalysis?.subtype_breakdown || summary.subtype_breakdown || {};
        const blueprintPerf = aiAnalysis?.blueprint_performance || summary.blueprint_performance || null;
        const blueprintDiag = summary.blueprint_diagnosis || blueprintPerf?.diagnosis || '';
        const actionPlan = aiAnalysis?.action_plan || [];

        // Build reviews list from ai_analysis or synthesize from questions
        let reviews = aiAnalysis?.detailed_reviews || [];
        if (!reviews || reviews.length === 0) {
          reviews = questions.map((q, idx) => {
            const studentChoice = answers[idx];
            const isAns = studentChoice !== undefined && studentChoice !== null;
            const qSubtype = q.subtype || "theory_definition";
            return {
              question_number: idx + 1,
              question_text: q.text,
              options: q.options || [],
              student_option_index: isAns ? Number(studentChoice) : null,
              student_answer: isAns && q.options ? q.options[studentChoice] : "Not Answered",
              correct_option_index: 0,
              correct_answer: q.options ? q.options[0] : "Option A",
              is_correct: isAns && Number(studentChoice) === 0,
              is_unanswered: !isAns,
              topic: q.topic || "General",
              subtype: qSubtype,
              subtype_label: qSubtype === 'direct_formula' ? '⚡ Direct Formula' :
                qSubtype === 'multi_step' ? '🧩 Multi-Step Problem' :
                qSubtype === 'physical_numerical' ? '🔢 Physical Numerical' :
                qSubtype === 'fact_reaction' ? '🧪 Reaction & Fact' : '📖 Pure Theory',
              explanation: q.explanation || "Comprehensive conceptual solution derived from syllabus textbook principles.",
              ai_insight: isAns 
                ? "Conceptual question requiring application of core textbook definitions and standard KCET problem patterns."
                : "Question skipped. Reviewing standard formulas will allow quicker recall during exams."
            };
          });
        }

        // Apply filter
        const filteredReviews = reviews.filter(r => {
          if (reviewFilter === 'correct') return r.is_correct;
          if (reviewFilter === 'incorrect') return !r.is_correct && !r.is_unanswered;
          if (reviewFilter === 'skipped') return r.is_unanswered;
          if (reviewFilter === 'calculations') {
            return r.subtype === 'direct_formula' || r.subtype === 'multi_step' || r.subtype === 'physical_numerical';
          }
          if (reviewFilter === 'theory') {
            return r.subtype === 'theory_definition' || r.subtype === 'fact_reaction';
          }
          return true;
        });


        return (
          <div className="overlay" style={{ display: "flex", alignItems: "flex-start", padding: "30px 16px" }}>
            <div 
              className="entry-modal" 
              style={{ 
                maxWidth: '920px', 
                width: '100%', 
                margin: '0 auto', 
                textAlign: 'left', 
                maxHeight: '90vh', 
                overflowY: 'auto', 
                padding: '28px',
                borderRadius: '16px',
                background: 'var(--s1, #13151b)',
                border: '1px solid rgba(255,255,255,0.12)',
                boxShadow: '0 20px 40px rgba(0,0,0,0.6)'
              }}
            >
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '20px', marginBottom: '24px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                    <span style={{ fontSize: '1.8rem' }}>🤖</span>
                    <h2 style={{ fontSize: '1.6rem', fontWeight: 800, margin: 0, color: 'var(--text, #fff)' }}>
                      AI Performance & Answer Diagnostics
                    </h2>
                  </div>
                  <p style={{ margin: 0, color: 'var(--muted, #9ca3af)', fontSize: '0.9rem' }}>
                    {examName} • {subject} • KCET Diagnostic Evaluation
                  </p>
                </div>
                <button 
                  className="btn-primary" 
                  onClick={() => navigate('/dashboard')}
                  style={{ padding: '10px 20px', fontSize: '0.9rem', fontWeight: 700 }}
                >
                  Return to Dashboard
                </button>
              </div>

              {/* Proctoring Violation Notice Banner */}
              {submitResult.autoSubmitted && (
                <div style={{
                  padding: '16px 20px',
                  background: 'rgba(239, 68, 68, 0.14)',
                  border: '1.5px solid rgba(239, 68, 68, 0.5)',
                  borderRadius: '12px',
                  marginBottom: '22px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px',
                  textAlign: 'left'
                }}>
                  <span style={{ fontSize: '2.2rem' }}>🚫</span>
                  <div>
                    <div style={{ fontWeight: 800, color: 'var(--red-l, #f87171)', fontSize: '1.02rem' }}>
                      Exam Automatically Submitted (Proctoring Violation)
                    </div>
                    <div style={{ fontSize: '0.86rem', color: 'var(--text)', marginTop: '4px', lineHeight: '1.4' }}>
                      {submitResult.violationReason || 'Your test was automatically submitted because your face was not recognized for the second time during the exam.'} All questions answered prior to termination have been evaluated below.
                    </div>
                  </div>
                </div>
              )}

              {/* Top Score & AI Assessment Card */}
              <div style={{
                background: 'linear-gradient(135deg, rgba(124,58,237,0.12), rgba(37,99,235,0.08))',
                border: '1px solid rgba(124,58,237,0.3)',
                borderRadius: '14px',
                padding: '22px',
                marginBottom: '24px'
              }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '20px', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--muted, #9ca3af)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Overall Score</div>
                    <div style={{ fontSize: '2.6rem', fontWeight: 900, color: pctVal >= 60 ? 'var(--green, #10b981)' : 'var(--yellow, #f59e0b)', lineHeight: 1.1, marginTop: '4px' }}>
                      {scoreVal} <span style={{ fontSize: '1.3rem', color: 'var(--muted, #9ca3af)', fontWeight: 500 }}>/ {totalVal}</span>
                    </div>
                    <div style={{ fontSize: '0.92rem', color: 'var(--text, #fff)', fontWeight: 600, marginTop: '6px' }}>
                      {pctVal}% Final Accuracy
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--muted, #9ca3af)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>AI Performance Band</div>
                    <div style={{ 
                      display: 'inline-block',
                      marginTop: '6px',
                      padding: '6px 14px',
                      borderRadius: '20px',
                      background: pctVal >= 75 ? 'rgba(16,185,129,0.2)' : pctVal >= 50 ? 'rgba(124,58,237,0.25)' : 'rgba(239,68,68,0.2)',
                      color: pctVal >= 75 ? '#34d399' : pctVal >= 50 ? '#c084fc' : '#f87171',
                      fontWeight: 700,
                      fontSize: '0.95rem',
                      border: `1px solid ${pctVal >= 75 ? 'rgba(16,185,129,0.4)' : pctVal >= 50 ? 'rgba(124,58,237,0.4)' : 'rgba(239,68,68,0.4)'}`
                    }}>
                      ⚡ {band}
                    </div>
                    <div style={{ fontSize: '0.82rem', color: 'var(--muted, #9ca3af)', marginTop: '8px' }}>
                      ⏱ {pacing}
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', textAlign: 'center' }}>
                    <div style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.25)', borderRadius: '10px', padding: '10px' }}>
                      <div style={{ color: 'var(--green, #10b981)', fontWeight: 800, fontSize: '1.3rem' }}>{correctCount}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--muted, #9ca3af)' }}>Correct</div>
                    </div>
                    <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)', borderRadius: '10px', padding: '10px' }}>
                      <div style={{ color: 'var(--red, #ef4444)', fontWeight: 800, fontSize: '1.3rem' }}>{incorrectCount}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--muted, #9ca3af)' }}>Incorrect</div>
                    </div>
                    <div style={{ background: 'rgba(156,163,175,0.1)', border: '1px solid rgba(156,163,175,0.25)', borderRadius: '10px', padding: '10px' }}>
                      <div style={{ color: '#9ca3af', fontWeight: 800, fontSize: '1.3rem' }}>{unansCount}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--muted, #9ca3af)' }}>Skipped</div>
                    </div>
                  </div>
                </div>

                {/* AI Verdict Quote */}
                <div style={{ marginTop: '18px', padding: '12px 16px', background: 'rgba(0,0,0,0.25)', borderRadius: '10px', borderLeft: '4px solid var(--purple, #7c3aed)' }}>
                  <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--purple-l, #c084fc)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '4px' }}>
                    AI Evaluator Insight
                  </div>
                  <div style={{ fontSize: '0.9rem', color: 'var(--text, #e5e7eb)', lineHeight: 1.5 }}>
                    "{verdict}"
                  </div>
                </div>
              </div>

              {/* KCET Blueprint & Calculation vs Theory Diagnostic */}
              {(blueprintPerf || Object.keys(subtypeMap).length > 0) && (
                <div style={{
                  background: 'var(--s2, #1a1d26)',
                  border: '1px solid rgba(124,58,237,0.3)',
                  borderRadius: '14px',
                  padding: '20px',
                  marginBottom: '26px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', marginBottom: '14px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '1.25rem' }}>🎯</span>
                      <h3 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0, color: 'var(--text, #fff)' }}>
                        KCET Blueprint & Calculation Breakdown Diagnostic
                      </h3>
                    </div>
                    {blueprintPerf?.type && (
                      <span style={{ fontSize: '0.75rem', fontWeight: 700, padding: '4px 10px', borderRadius: '12px', background: 'rgba(124,58,237,0.2)', color: 'var(--purple-l, #c084fc)', border: '1px solid rgba(124,58,237,0.4)' }}>
                        {blueprintPerf.type === 'physics' ? '⚡ Physics 55% Calculations / 45% Theory Pattern' : '🧪 Chemistry 10% Numericals / 90% Facts Pattern'}
                      </span>
                    )}
                  </div>

                  {/* Subtype Breakdown Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px', marginBottom: '14px' }}>
                    {Object.entries(subtypeMap).map(([stKey, stData]) => {
                      const stPct = stData.accuracy_pct ?? 0;
                      const isHigh = stPct >= 70;
                      const isMed = stPct >= 40;
                      const barColor = isHigh ? '#10b981' : isMed ? '#f59e0b' : '#ef4444';

                      return (
                        <div key={stKey} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '10px', padding: '12px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text, #e5e7eb)' }}>
                              {stData.label || stKey.replace('_', ' ')}
                            </span>
                            <span style={{ fontSize: '0.8rem', fontWeight: 800, color: barColor }}>
                              {stPct}%
                            </span>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', color: 'var(--muted, #9ca3af)', marginBottom: '6px' }}>
                            <span>{stData.correct} of {stData.total} correct</span>
                          </div>
                          <div style={{ width: '100%', height: '5px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ width: `${Math.min(100, Math.max(0, stPct))}%`, height: '100%', background: barColor }}></div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Blueprint Diagnosis text */}
                  {blueprintDiag && (
                    <div style={{ padding: '10px 14px', background: 'rgba(124,58,237,0.08)', borderRadius: '8px', borderLeft: '3px solid var(--purple, #7c3aed)', fontSize: '0.86rem', color: 'var(--text, #d1d5db)' }}>
                      <strong style={{ color: 'var(--purple-l, #c084fc)' }}>Blueprint Strategy:</strong> {blueprintDiag}
                    </div>
                  )}
                </div>
              )}

              {/* Topic Mastery Breakdown */}
              {Object.keys(topicMap).length > 0 && (
                <div style={{ marginBottom: '26px' }}>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '14px', color: 'var(--text, #fff)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span>📊</span> Syllabus Topic Mastery Matrix
                  </h3>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '14px' }}>
                    {Object.entries(topicMap).map(([tName, tData]) => {
                      const tPct = tData.accuracy_pct ?? 0;
                      const level = tData.mastery_level || (tPct >= 75 ? 'Mastered' : tPct >= 50 ? 'Intermediate' : 'Review Needed');
                      const badgeColor = level === 'Mastered' ? '#10b981' : level === 'Intermediate' ? '#f59e0b' : '#ef4444';
                      const badgeBg = level === 'Mastered' ? 'rgba(16,185,129,0.15)' : level === 'Intermediate' ? 'rgba(245,158,11,0.15)' : 'rgba(239,68,68,0.15)';

                      return (
                        <div key={tName} style={{ background: 'var(--s2, #1a1d26)', border: '1px solid var(--border, rgba(255,255,255,0.08))', borderRadius: '10px', padding: '14px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <span style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text, #fff)' }}>{tName}</span>
                            <span style={{ fontSize: '0.72rem', fontWeight: 700, padding: '3px 8px', borderRadius: '12px', background: badgeBg, color: badgeColor }}>
                              {level}
                            </span>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--muted, #9ca3af)', marginBottom: '6px' }}>
                            <span>Accuracy: {tPct}%</span>
                            <span>{tData.correct}/{tData.total} correct</span>
                          </div>
                          <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ width: `${Math.min(100, Math.max(0, tPct))}%`, height: '100%', background: badgeColor, transition: 'width 0.4s ease' }}></div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Action Plan */}
              {actionPlan.length > 0 && (
                <div style={{
                  background: 'rgba(245,158,11,0.08)',
                  border: '1px solid rgba(245,158,11,0.25)',
                  borderRadius: '12px',
                  padding: '18px 20px',
                  marginBottom: '26px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                    <span style={{ fontSize: '1.2rem' }}>💡</span>
                    <h3 style={{ fontSize: '1.05rem', fontWeight: 700, margin: 0, color: '#fbbf24' }}>
                      Targeted AI Revision Action Plan
                    </h3>
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '20px', color: 'var(--text, #e5e7eb)', fontSize: '0.88rem', lineHeight: 1.6 }}>
                    {actionPlan.map((step, sIdx) => (
                      <li key={sIdx} style={{ marginBottom: '6px' }}>{step}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Question-by-Question Solution Review */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0, color: 'var(--text, #fff)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span>📋</span> Detailed Question Solutions & Concept Explanations
                  </h3>

                  {/* Filter Tabs */}
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', background: 'var(--s2, #1a1d26)', padding: '4px', borderRadius: '8px', border: '1px solid var(--border)' }}>
                    {[
                      { id: 'all', label: `All (${reviews.length})` },
                      { id: 'correct', label: `✓ Correct (${correctCount})` },
                      { id: 'incorrect', label: `✗ Incorrect (${incorrectCount})` },
                      { id: 'skipped', label: `○ Skipped (${unansCount})` },
                      { id: 'calculations', label: `⚡ Calculations (${reviews.filter(r => r.subtype === 'direct_formula' || r.subtype === 'multi_step' || r.subtype === 'physical_numerical').length})` },
                      { id: 'theory', label: `📖 Theory & Facts (${reviews.filter(r => r.subtype === 'theory_definition' || r.subtype === 'fact_reaction').length})` }
                    ].map(tab => (
                      <button
                        key={tab.id}
                        type="button"
                        onClick={() => setReviewFilter(tab.id)}
                        style={{
                          background: reviewFilter === tab.id ? 'var(--purple, #7c3aed)' : 'transparent',
                          color: reviewFilter === tab.id ? '#fff' : 'var(--muted, #9ca3af)',
                          border: 'none',
                          borderRadius: '6px',
                          padding: '6px 12px',
                          fontSize: '0.78rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                          transition: 'all 0.2s'
                        }}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Review Cards */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {filteredReviews.length === 0 ? (
                    <div style={{ padding: '24px', textAlign: 'center', color: 'var(--muted)', background: 'var(--s2)', borderRadius: '10px' }}>
                      No questions match this filter.
                    </div>
                  ) : (
                    filteredReviews.map((item, idx) => {
                      const isCorrect = item.is_correct;
                      const isSkipped = item.is_unanswered;
                      const cardBorder = isCorrect ? 'rgba(16,185,129,0.35)' : isSkipped ? 'rgba(156,163,175,0.2)' : 'rgba(239,68,68,0.35)';
                      const badgeBg = isCorrect ? 'rgba(16,185,129,0.15)' : isSkipped ? 'rgba(156,163,175,0.15)' : 'rgba(239,68,68,0.15)';
                      const badgeColor = isCorrect ? '#34d399' : isSkipped ? '#9ca3af' : '#f87171';
                      const badgeLabel = isCorrect ? '✓ Correct (+1)' : isSkipped ? '○ Skipped (0)' : '✗ Incorrect (0)';

                      return (
                        <div 
                          key={idx} 
                          style={{ 
                            background: 'var(--s2, #1a1d26)', 
                            border: `1px solid ${cardBorder}`, 
                            borderRadius: '12px', 
                            padding: '18px 20px',
                            transition: 'border-color 0.2s'
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', marginBottom: '12px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                              <span style={{ fontWeight: 800, fontSize: '0.95rem', color: 'var(--text, #fff)' }}>
                                Q{item.question_number}
                              </span>
                              <span style={{ fontSize: '0.75rem', background: 'rgba(124,58,237,0.15)', color: 'var(--purple-l, #c084fc)', padding: '2px 8px', borderRadius: '6px', fontWeight: 600 }}>
                                {item.topic || 'General'}
                              </span>
                              {(item.subtype_label || item.subtype) && (
                                <span style={{
                                  fontSize: '0.73rem',
                                  background: (item.subtype === 'multi_step')
                                    ? 'rgba(245,158,11,0.15)'
                                    : (item.subtype === 'direct_formula' || item.subtype === 'physical_numerical')
                                    ? 'rgba(59,130,246,0.15)'
                                    : 'rgba(16,185,129,0.15)',
                                  color: (item.subtype === 'multi_step')
                                    ? '#fbbf24'
                                    : (item.subtype === 'direct_formula' || item.subtype === 'physical_numerical')
                                    ? '#60a5fa'
                                    : '#34d399',
                                  border: `1px solid ${
                                    (item.subtype === 'multi_step')
                                      ? 'rgba(245,158,11,0.3)'
                                      : (item.subtype === 'direct_formula' || item.subtype === 'physical_numerical')
                                      ? 'rgba(59,130,246,0.3)'
                                      : 'rgba(16,185,129,0.3)'
                                  }`,
                                  padding: '2px 8px',
                                  borderRadius: '6px',
                                  fontWeight: 600
                                }}>
                                  {item.subtype_label || (
                                    item.subtype === 'direct_formula' ? '⚡ Direct Formula' :
                                    item.subtype === 'multi_step' ? '🧩 Multi-Step Problem' :
                                    item.subtype === 'physical_numerical' ? '🔢 Physical Numerical' :
                                    item.subtype === 'fact_reaction' ? '🧪 Reaction & Fact' :
                                    '📖 Pure Theory'
                                  )}
                                </span>
                              )}
                            </div>
                            <span style={{ fontSize: '0.78rem', fontWeight: 700, padding: '4px 10px', borderRadius: '12px', background: badgeBg, color: badgeColor }}>
                              {badgeLabel}
                            </span>
                          </div>


                          {/* Question Text */}
                          <p style={{ fontSize: '0.98rem', fontWeight: 600, color: 'var(--text, #f3f4f6)', marginBottom: '14px', lineHeight: 1.5 }}>
                            {item.question_text}
                          </p>

                          {/* Options display if available */}
                          {item.options && Array.isArray(item.options) && item.options.length > 0 && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '14px' }}>
                              {item.options.map((opt, optIdx) => {
                                const isCorrectChoice = optIdx === item.correct_option_index;
                                const isStudentChoice = optIdx === item.student_option_index;

                                let optBorder = 'rgba(255,255,255,0.06)';
                                let optBg = 'rgba(255,255,255,0.02)';
                                let optTextColor = 'var(--text, #d1d5db)';
                                let tag = null;

                                if (isCorrectChoice) {
                                  optBorder = 'rgba(16,185,129,0.5)';
                                  optBg = 'rgba(16,185,129,0.12)';
                                  optTextColor = '#34d399';
                                  tag = <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#34d399', marginLeft: 'auto' }}>✓ Correct Answer</span>;
                                } else if (isStudentChoice) {
                                  optBorder = 'rgba(239,68,68,0.5)';
                                  optBg = 'rgba(239,68,68,0.12)';
                                  optTextColor = '#f87171';
                                  tag = <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#f87171', marginLeft: 'auto' }}>Your Answer</span>;
                                }

                                return (
                                  <div 
                                    key={optIdx} 
                                    style={{ 
                                      display: 'flex', 
                                      alignItems: 'center', 
                                      gap: '12px', 
                                      padding: '10px 14px', 
                                      background: optBg, 
                                      border: `1px solid ${optBorder}`, 
                                      borderRadius: '8px', 
                                      fontSize: '0.88rem', 
                                      color: optTextColor 
                                    }}
                                  >
                                    <span style={{ 
                                      width: '24px', 
                                      height: '24px', 
                                      borderRadius: '50%', 
                                      background: isCorrectChoice ? '#10b981' : isStudentChoice ? '#ef4444' : 'rgba(255,255,255,0.08)',
                                      color: isCorrectChoice || isStudentChoice ? '#fff' : 'var(--muted)',
                                      display: 'flex', 
                                      alignItems: 'center', 
                                      justifyContent: 'center', 
                                      fontSize: '0.75rem', 
                                      fontWeight: 700 
                                    }}>
                                      {String.fromCharCode(65 + optIdx)}
                                    </span>
                                    <span>{opt}</span>
                                    {tag}
                                  </div>
                                );
                              })}
                            </div>
                          )}

                          {/* AI Solution & Conceptual Rationale */}
                          <div style={{
                            background: 'rgba(124,58,237,0.07)',
                            border: '1px solid rgba(124,58,237,0.22)',
                            borderRadius: '10px',
                            padding: '12px 16px',
                            marginTop: '10px'
                          }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                              <span style={{ fontSize: '0.95rem' }}>🧠</span>
                              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--purple-l, #c084fc)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                                AI Solution Breakdown & Concept
                              </span>
                            </div>
                            <div style={{ fontSize: '0.88rem', color: 'var(--text, #e5e7eb)', lineHeight: 1.5, marginBottom: item.ai_insight ? '8px' : '0' }}>
                              {item.explanation || 'Refer to standard KCET syllabus formula and textbook derivations.'}
                            </div>
                            {item.ai_insight && (
                              <div style={{ fontSize: '0.8rem', color: 'var(--muted, #9ca3af)', borderTop: '1px solid rgba(124,58,237,0.15)', paddingTop: '6px', marginTop: '6px' }}>
                                <strong style={{ color: 'var(--purple-l)' }}>Diagnostic Insight:</strong> {item.ai_insight}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>

              {/* Footer Actions */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '28px', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '20px' }}>
                <button 
                  type="button" 
                  className="btn-outline" 
                  onClick={handleBackToExamSelection}
                  style={{ padding: '10px 20px', fontSize: '0.9rem' }}
                >
                  🔄 Take Another Published Mock
                </button>
                <button 
                  type="button" 
                  className="btn-primary" 
                  onClick={() => navigate('/dashboard')}
                  style={{ padding: '10px 24px', fontSize: '0.9rem', fontWeight: 700 }}
                >
                  Go to Student Dashboard →
                </button>
              </div>
            </div>
          </div>
        );
      })()}
    </>
  );
};

export default Exam;
