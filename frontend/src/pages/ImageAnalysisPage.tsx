import React, { useEffect, useRef, useState } from 'react';
import { AlertTriangle, Flame, ImagePlus, UploadCloud } from 'lucide-react';
import { api, resolveMediaUrl } from '../services/api';
import { AnalysisProvider, PredictionResponse } from '../types';

export const ImageAnalysisPage: React.FC = () => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [provider, setProvider] = useState<AnalysisProvider>('gemini');
  const [loading, setLoading] = useState(false);
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

  const chooseFile = (nextFile?: File) => {
    if (!nextFile) return;
    setFile(nextFile);
    setResult(null);
    setError(null);
  };

  const analyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await api.predictImage(file, undefined, provider));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Image analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container analysis-page">
      <header className="analysis-heading">
        <p className="demo-eyebrow">FIRESNET-CNN / GRAD-CAM</p>
        <h1>Image Upload and Verification</h1>
        <p>Analyze a still image independently from live CCTV monitoring.</p>
        <label className="analysis-provider-control">
          Analysis provider
          <select value={provider} onChange={(event) => setProvider(event.target.value as AnalysisProvider)}>
            <option value="gemini">Gemini AI (informational)</option>
            <option value="firenet">FireNet-CNN (trained checkpoint required)</option>
          </select>
        </label>
      </header>
      {error && <div className="demo-error" role="alert"><AlertTriangle size={18} />{error}</div>}
      {result?.demo_mode && <div className="demo-warning"><AlertTriangle size={18} />Demo model mode is active; results are not operationally reliable without a trained checkpoint.</div>}
      <section className="analysis-upload-layout reveal-up delay-1">
        <div className="analysis-panel reveal-left">
          <input
            ref={inputRef}
            className="visually-hidden"
            type="file"
            accept="image/jpeg,image/png,image/webp,image/bmp"
            onChange={(event) => chooseFile(event.target.files?.[0])}
          />
          <button
            className="analysis-dropzone"
            type="button"
            onClick={() => inputRef.current?.click()}
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              chooseFile(event.dataTransfer.files[0]);
            }}
          >
            {previewUrl ? <img src={previewUrl} alt="Selected image preview" /> : (
              <>
                <UploadCloud size={30} />
                <strong>Drop an image here or browse</strong>
                <span>JPG, PNG, WEBP, BMP</span>
              </>
            )}
          </button>
          <div className="analysis-actions">
            <span>{file?.name ?? 'No image selected'}</span>
            <button className="demo-action-button primary" onClick={() => void analyze()} disabled={!file || loading}>
              {loading ? 'Analyzing...' : <><ImagePlus size={16} /> Analyze image</>}
            </button>
          </div>
        </div>
        <div className="analysis-result-panel" aria-live="polite">
          <h2>Classification result</h2>
          {result ? (
            <>
              <div className={`analysis-classification class-${result.predicted_class}`}>
                <Flame size={20} />
                <strong>{result.predicted_class.toUpperCase()}</strong>
                <span>{result.confidence == null ? 'Confidence not calibrated' : `${(result.confidence * 100).toFixed(1)}% confidence`}</span>
              </div>
              <dl className="analysis-metadata">
                <div><dt>Analyzed at</dt><dd>{new Date().toLocaleString()}</dd></div>
                <div><dt>Inference time</dt><dd>{result.inference_ms.toFixed(1)} ms</dd></div>
                <div><dt>Provider</dt><dd>{result.analysis_provider === 'gemini' ? `Gemini (${result.model_version})` : result.model_version}</dd></div>
              </dl>
              {result.analysis_text && <p className="gemini-analysis-text">{result.analysis_text}</p>}
              {!!result.analysis_evidence?.length && (
                <ul className="gemini-analysis-evidence">
                  {result.analysis_evidence.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}
                </ul>
              )}
              {result.analysis_caveat && <p className="gemini-analysis-caveat">{result.analysis_caveat}</p>}
              {result.heatmap_image_url && (
                <figure className="analysis-heatmap">
                  <img src={resolveMediaUrl(result.heatmap_image_url)} alt="Grad-CAM heatmap for selected image" />
                  <figcaption>Grad-CAM attention evidence</figcaption>
                </figure>
              )}
            </>
          ) : <p className="demo-empty-state">Select an image and run analysis to see the model output and explanation.</p>}
        </div>
      </section>
    </div>
  );
};
