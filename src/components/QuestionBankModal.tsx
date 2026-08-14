import React, { useState } from 'react';
import { 
  Database, 
  X, 
  Upload, 
  Download, 
  RotateCcw, 
  Check, 
  AlertCircle, 
  Layers, 
  FileText, 
  Sparkles, 
  ExternalLink,
  BookOpen
} from 'lucide-react';
import { QuestionBank } from '../types';
import { 
  OFFICIAL_PRESETS, 
  fetchQuestionBankFromUrl, 
  parseAndImportQuestionBankJSON, 
  resetQuestionBankToDefault,
  validateQuestionBank
} from '../services/questionBankLoader';

interface QuestionBankModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentBank: QuestionBank;
  onBankChanged: (newBank: QuestionBank) => void;
}

export const QuestionBankModal: React.FC<QuestionBankModalProps> = ({
  isOpen,
  onClose,
  currentBank,
  onBankChanged,
}) => {
  const [selectedTab, setSelectedTab] = useState<'presets' | 'import' | 'view'>('presets');
  const [jsonInput, setJsonInput] = useState<string>('');
  const [urlInput, setUrlInput] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSelectPreset = async (url: string) => {
    setIsLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const bank = await fetchQuestionBankFromUrl(url);
      onBankChanged(bank);
      setSuccessMsg(`Successfully loaded "${bank.title}"`);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load question pack.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFetchCustomUrl = async () => {
    if (!urlInput.trim()) {
      setErrorMsg('Please enter a valid URL.');
      return;
    }
    setIsLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const bank = await fetchQuestionBankFromUrl(urlInput.trim());
      onBankChanged(bank);
      setSuccessMsg(`Successfully loaded "${bank.title}" from custom URL!`);
      setUrlInput('');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to fetch question bank JSON from the specified URL.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleImportJson = () => {
    setErrorMsg(null);
    setSuccessMsg(null);
    if (!jsonInput.trim()) {
      setErrorMsg('Please paste a JSON configuration first.');
      return;
    }
    try {
      const bank = parseAndImportQuestionBankJSON(jsonInput.trim());
      onBankChanged(bank);
      setSuccessMsg(`Successfully imported custom bank "${bank.title}"!`);
      setJsonInput('');
    } catch (err: any) {
      setErrorMsg(err.message || 'Invalid Question Bank JSON format.');
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMsg(null);
    setSuccessMsg(null);
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const text = event.target?.result as string;
        const bank = parseAndImportQuestionBankJSON(text);
        onBankChanged(bank);
        setSuccessMsg(`Successfully loaded "${bank.title}" from ${file.name}`);
      } catch (err: any) {
        setErrorMsg(err.message || 'Failed to parse uploaded JSON file.');
      }
    };
    reader.readAsText(file);
  };

  const handleExportJson = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(currentBank, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `ielts_question_bank_${currentBank.id || 'export'}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const handleResetDefault = () => {
    const defaultBank = resetQuestionBankToDefault();
    onBankChanged(defaultBank);
    setSuccessMsg('Reset to Default Cambridge Official IELTS Question Bank.');
    setErrorMsg(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base sm:text-lg font-bold text-white flex items-center gap-2">
                IELTS Question Bank Loader
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-mono">
                  JSON Engine
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Load official Cambridge test sets or import custom JSON configurations without editing code.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Status Alerts */}
        {errorMsg && (
          <div className="mx-6 mt-4 p-3 rounded-xl bg-red-950/50 border border-red-500/40 text-red-300 text-xs flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}
        {successMsg && (
          <div className="mx-6 mt-4 p-3 rounded-xl bg-emerald-950/50 border border-emerald-500/40 text-emerald-300 text-xs flex items-start space-x-2">
            <Check className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-800 px-6 pt-3 gap-2 bg-slate-950/30">
          <button
            onClick={() => setSelectedTab('presets')}
            className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition-colors flex items-center gap-1.5 ${
              selectedTab === 'presets'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            Official Test Packs
          </button>
          <button
            onClick={() => setSelectedTab('import')}
            className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition-colors flex items-center gap-1.5 ${
              selectedTab === 'import'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Upload className="w-3.5 h-3.5" />
            Custom JSON Import
          </button>
          <button
            onClick={() => setSelectedTab('view')}
            className={`pb-2.5 px-3 text-xs font-semibold border-b-2 transition-colors flex items-center gap-1.5 ${
              selectedTab === 'view'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            Active Bank Summary
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {selectedTab === 'presets' && (
            <div className="space-y-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block">
                Select an Official IELTS Test Bank
              </span>
              
              <div className="grid grid-cols-1 gap-3">
                {OFFICIAL_PRESETS.map((preset) => {
                  const isActive = currentBank.id === preset.id;
                  return (
                    <div
                      key={preset.id}
                      className={`p-4 rounded-xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                        isActive
                          ? 'bg-indigo-950/40 border-indigo-500/60 shadow-md shadow-indigo-950/50'
                          : 'bg-slate-800/50 border-slate-700/70 hover:border-slate-600'
                      }`}
                    >
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-bold text-white">{preset.name}</span>
                          <span className="px-2 py-0.5 text-[10px] font-bold rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                            {preset.badge}
                          </span>
                          {isActive && (
                            <span className="px-2 py-0.5 text-[10px] font-bold rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                              <Check className="w-3 h-3" /> Active
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-400 mt-1">{preset.description}</p>
                      </div>

                      <button
                        onClick={() => handleSelectPreset(preset.url)}
                        disabled={isLoading || isActive}
                        className={`text-xs px-4 py-2 rounded-lg font-semibold transition-all shrink-0 ${
                          isActive
                            ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                            : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm shadow-indigo-600/30'
                        }`}
                      >
                        {isActive ? 'Current Active' : 'Load This Set'}
                      </button>
                    </div>
                  );
                })}
              </div>

              {/* Custom URL Loader */}
              <div className="pt-3 border-t border-slate-800">
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                  Or Load from Custom JSON URL / API Endpoint:
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="https://example.com/ielts-question-bank.json"
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                  <button
                    onClick={handleFetchCustomUrl}
                    disabled={isLoading}
                    className="bg-slate-800 hover:bg-slate-700 border border-slate-600 text-white text-xs px-3 py-2 rounded-lg font-medium transition-colors"
                  >
                    Fetch
                  </button>
                </div>
              </div>
            </div>
          )}

          {selectedTab === 'import' && (
            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Upload Question Bank JSON File:
                </label>
                <input
                  type="file"
                  accept=".json"
                  onChange={handleFileUpload}
                  className="text-xs text-slate-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border file:border-slate-700 file:text-xs file:font-semibold file:bg-slate-800 file:text-slate-200 hover:file:bg-slate-700 cursor-pointer"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Or Paste Custom JSON Configuration:
                </label>
                <textarea
                  rows={8}
                  placeholder={`{\n  "id": "my-custom-test",\n  "title": "Custom IELTS Test Pack",\n  "version": "1.0",\n  "part1Topics": [...],\n  "part2CueCards": [...],\n  "part3Topics": [...]\n}`}
                  value={jsonInput}
                  onChange={(e) => setJsonInput(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 font-mono text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-2">
                <button
                  onClick={handleImportJson}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-4 py-2 rounded-lg font-semibold transition-all shadow-md shadow-indigo-600/30"
                >
                  Apply & Load Custom Bank
                </button>
              </div>
            </div>
          )}

          {selectedTab === 'view' && (
            <div className="space-y-3">
              <div className="p-4 bg-slate-950/70 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-white">{currentBank.title}</span>
                  <span className="text-xs font-mono text-indigo-400">v{currentBank.version}</span>
                </div>
                <p className="text-xs text-slate-400">{currentBank.description}</p>
                
                <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800 text-center">
                  <div className="p-2 bg-slate-900 rounded-lg border border-slate-800">
                    <span className="text-lg font-extrabold text-indigo-400">
                      {currentBank.part1Topics?.length || 0}
                    </span>
                    <span className="text-[10px] text-slate-400 block">Part 1 Categories</span>
                  </div>
                  <div className="p-2 bg-slate-900 rounded-lg border border-slate-800">
                    <span className="text-lg font-extrabold text-indigo-400">
                      {currentBank.part2CueCards?.length || 0}
                    </span>
                    <span className="text-[10px] text-slate-400 block">Part 2 Cue Cards</span>
                  </div>
                  <div className="p-2 bg-slate-900 rounded-lg border border-slate-800">
                    <span className="text-lg font-extrabold text-indigo-400">
                      {currentBank.part3Topics?.length || 0}
                    </span>
                    <span className="text-[10px] text-slate-400 block">Part 3 Themes</span>
                  </div>
                </div>
              </div>

              <div className="flex justify-between items-center pt-2">
                <button
                  onClick={handleExportJson}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs px-3.5 py-2 rounded-lg font-medium flex items-center gap-1.5 transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  Export as JSON File
                </button>

                <button
                  onClick={handleResetDefault}
                  className="bg-slate-800/80 hover:bg-rose-950/40 text-slate-400 hover:text-rose-300 border border-slate-700 hover:border-rose-800 text-xs px-3 py-2 rounded-lg font-medium flex items-center gap-1.5 transition-colors"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  Reset to Cambridge Default
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-slate-950 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center space-x-1">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>Zero-code dynamic configuration powered by standard JSON schema.</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition-colors"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
};
