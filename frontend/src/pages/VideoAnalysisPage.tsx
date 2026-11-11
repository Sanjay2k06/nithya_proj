import React, { useEffect, useRef, useState } from 'react';
import { AlertTriangle, Film, UploadCloud } from 'lucide-react';
import { api, resolveMediaUrl } from '../services/api';
import { AnalysisProvider, VideoAnalysisTask } from '../types';

export const VideoAnalysisPage: React.FC = () => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [task, setTask] = useState<VideoAnalysisTask | null>(null);
  const [provider, setProvider] = useState<AnalysisProvider>('firenet');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      return undefined;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  useEffect(() => {
    if (!task || (task.status !== 'pending' && task.status !== 'processing')) return undefined;
    const intervalId = window.setInterval(async () => {
      try {
        const status = await api.getVideoTaskStatus(task.task_id);
        setTask(status);
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : 'Could not retrieve video processing status.');
        window.clearInterval(intervalId);
      }
    }, 1200);
    return () => window.clearInterval(intervalId);
  }, [task?.task_id, task?.status]);

  const analyzeVideo = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setTask(null);
    try {
      const created = await api.uploadVideo(file, provider);
      setTask(created);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Video upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const progress = task?.total_frames
    ? Math.min(100, Math.round(((task.processed_frames ?? 0) / task.total_frames) * 100))
    : null;

  return (
    <div className="page-container analysis-page">
      <header className="analysis-heading reveal-up">
        <p className="demo-eyebrow">ASYNCHRONOUS VIDEO INFERENCE</p>
        <h1>Video Upload and Verification</h1>
        <p>Upload footage for backend frame extraction and AI-assisted analysis.</p>
        <label className="analysis-provider-control">
          Analysis provider
          <select value={provider} onChange={(event) => setProvider(event.target.value as AnalysisProvider)}>
            <option value="firenet">FireNet-CNN (Edge XAI + Grad-CAM Heatmap)</option>
            <option value="gemini">Gemini AI (Multimodal Vision Analysis)</option>
          </select>
        </label>
      </header>
      {error && <div className="demo-error" role="alert"><AlertTriangle size={18} />{error}</div>}
      <section className="analysis-upload-layout video-analysis-layout reveal-up delay-1">
        <div className="analysis-panel reveal-left">
          <input
            ref={inputRef}
            className="visually-hidden"
            type="file"
            accept="video/mp4,video/quicktime,video/x-msvideo,video/x-matroska"
            onChange={(event) => {
              setFile(event.target.files?.[0] ?? null);
              setTask(null);
              setError(null);
            }}
          />
          {previewUrl ? (
            <video className="analysis-video-preview" src={previewUrl} controls preload="metadata" />
          ) : (
            <button className="analysis-dropzone video-dropzone" type="button" onClick={() => inputRef.current?.click()}>
              <UploadCloud size={30} />
              <strong>Choose a video to analyze</strong>
              <span>MP4, MOV, AVI, MKV</span>
            </button>
          )}
          <div className="analysis-actions">
            <span>{file?.name ?? 'No video selected'}</span>
            <button className="demo-action-button primary" onClick={() => void analyzeVideo()} disabled={!file || uploading || task?.status === 'pending' || task?.status === 'processing'}>
              <Film size={16} /> {uploading ? 'Uploading...' : 'Analyze video'}
            </button>
          </div>
        </div>
        <div className="analysis-result-panel reveal-right">
          <h2>Processing status</h2>
          {!task ? (
            <p className="demo-empty-state">Choose a video to begin backend frame extraction and FireNet-CNN analysis.</p>
          ) : (
            <>
              <div className={`video-task-status status-${task.status}`}>
                <span>{task.status.toUpperCase()}</span>
                {progress !== null && <strong>{progress}%</strong>}
              </div>
              {progress !== null && <progress className="video-progress" value={progress} max={100} />}
              <dl className="analysis-metadata">
                <div><dt>Task ID</dt><dd>{task.task_id}</dd></div>
                <div><dt>Frames processed</dt><dd>{task.processed_frames ?? 0}{task.total_frames ? ` / ${task.total_frames}` : ''}</dd></div>
                <div><dt>{task.analysis_provider === 'gemini' ? 'Fire/smoke assessments' : 'Detection candidates'}</dt><dd>{task.detections_count ?? '—'}</dd></div>
                {task.analysis_provider === 'firenet' && <div><dt>Verified incidents</dt><dd>{task.alerts_count ?? '—'}</dd></div>}
              </dl>
              {task.analysis_provider === 'gemini' && (
                <p className="gemini-analysis-caveat">
                  Gemini provides multimodal visual assessments. Results are stored in surveillance history.
                </p>
              )}
              {task.analysis_summary && (
                <div style={{ marginTop: '14px', padding: '12px', background: 'var(--bg-secondary)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <p style={{ margin: 0, fontSize: '0.88rem', color: '#e2e8f0' }}>{task.analysis_summary}</p>
                </div>
              )}
              {!!task.frame_results?.length && (
                <div style={{ marginTop: '16px' }}>
                  <h3 style={{ fontSize: '0.95rem', color: '#fff', marginBottom: '8px', fontWeight: 600 }}>Analyzed Frame Sequence</h3>
                  <div style={{ maxHeight: '280px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px', paddingRight: '4px' }}>
                    {task.frame_results.map((frame, index) => {
                      const isFire = frame.classification === 'fire';
                      const isSmoke = frame.classification === 'smoke';
                      const badgeBg = isFire ? 'rgba(239, 68, 68, 0.18)' : isSmoke ? 'rgba(234, 179, 8, 0.18)' : 'rgba(34, 197, 94, 0.18)';
                      const badgeColor = isFire ? '#ef4444' : isSmoke ? '#eab308' : '#22c55e';
                      return (
                        <div
                          key={`${frame.timestamp_seconds}-${index}`}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            padding: '8px 12px',
                            borderRadius: '6px',
                            background: 'var(--bg-primary)',
                            border: '1px solid var(--border-subtle)',
                            fontSize: '0.85rem'
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <span style={{ color: 'var(--text-muted)', fontFamily: 'monospace' }}>{frame.timestamp_seconds.toFixed(2)}s</span>
                            <span style={{ padding: '2px 8px', borderRadius: '4px', fontWeight: 600, fontSize: '0.75rem', background: badgeBg, color: badgeColor }}>
                              {frame.classification.toUpperCase()}
                            </span>
                            <span style={{ color: '#cbd5e1' }}>{frame.observation}</span>
                          </div>
                          {frame.heatmap_image_url && (
                            <img
                              src={resolveMediaUrl(frame.heatmap_image_url)}
                              alt="Grad-CAM"
                              style={{ width: '42px', height: '42px', objectFit: 'cover', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}
                            />
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
              {task.status === 'completed' && (
                <p className="analysis-completion-note">
                  {task.analysis_provider === 'gemini'
                    ? 'Gemini video assessment completed. It is not recorded as FireNet detections or verified incidents.'
                    : 'Processing completed. Classification events and verified incidents are recorded in detection and incident history.'}
                </p>
              )}
              {task.status === 'failed' && (
                <p className="demo-error">
                  {task.error || 'The backend could not complete this video task. Check system health and backend logs.'}
                </p>
              )}
            </>
          )}
        </div>
      </section>
    </div>
  );
};
