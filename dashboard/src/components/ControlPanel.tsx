'use client';

import { useState } from 'react';
import { AlertTriangle, StopCircle, Play, Pause } from 'lucide-react';

interface ControlPanelProps {
  isActive: boolean;
  isAccumulating: boolean;
  onPanicClose: () => Promise<void>;
  onHaltAccumulation: () => Promise<void>;
  onResumeAccumulation: () => Promise<void>;
}

export default function ControlPanel({
  isActive,
  isAccumulating,
  onPanicClose,
  onHaltAccumulation,
  onResumeAccumulation,
}: ControlPanelProps) {
  const [showPanicConfirm, setShowPanicConfirm] = useState(false);
  const [showHaltConfirm, setShowHaltConfirm] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const handlePanicClick = () => {
    setShowPanicConfirm(true);
  };

  const handlePanicConfirm = async () => {
    setIsProcessing(true);
    try {
      await onPanicClose();
    } finally {
      setIsProcessing(false);
      setShowPanicConfirm(false);
    }
  };

  const handleHaltClick = () => {
    setShowHaltConfirm(true);
  };

  const handleHaltConfirm = async () => {
    setIsProcessing(true);
    try {
      await onHaltAccumulation();
    } finally {
      setIsProcessing(false);
      setShowHaltConfirm(false);
    }
  };

  const handleResumeClick = async () => {
    setIsProcessing(true);
    try {
      await onResumeAccumulation();
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg shadow-xl">
      <div className="px-4 py-3 border-b border-gray-800">
        <h3 className="text-lg font-bold text-white">Control Panel</h3>
        <p className="text-sm text-gray-400">Manual override controls</p>
      </div>

      <div className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Bot Status */}
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="text-sm text-gray-400 mb-2">Bot Status</div>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${isActive ? 'bg-green-500' : 'bg-gray-600'} animate-pulse`} />
              <span className={`text-lg font-bold ${isActive ? 'text-green-400' : 'text-gray-500'}`}>
                {isActive ? 'ACTIVE' : 'INACTIVE'}
              </span>
            </div>
          </div>

          {/* Accumulation Status */}
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="text-sm text-gray-400 mb-2">Accumulation</div>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${isAccumulating ? 'bg-blue-500' : 'bg-yellow-500'}`} />
              <span className={`text-lg font-bold ${isAccumulating ? 'text-blue-400' : 'text-yellow-400'}`}>
                {isAccumulating ? 'RUNNING' : 'HALTED'}
              </span>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="text-sm text-gray-400 mb-2">Quick Actions</div>
            {isAccumulating ? (
              <button
                onClick={handleHaltClick}
                disabled={isProcessing}
                className="flex items-center gap-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-600 text-white rounded-lg font-semibold transition-colors w-full justify-center"
              >
                <Pause className="w-4 h-4" />
                Halt
              </button>
            ) : (
              <button
                onClick={handleResumeClick}
                disabled={isProcessing}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded-lg font-semibold transition-colors w-full justify-center"
              >
                <Play className="w-4 h-4" />
                Resume
              </button>
            )}
          </div>
        </div>

        {/* Emergency Controls */}
        <div className="mt-4 pt-4 border-t border-gray-800">
          <div className="text-sm text-gray-400 mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-500" />
            Emergency Controls
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              onClick={handlePanicClick}
              disabled={isProcessing}
              className="flex items-center justify-center gap-2 px-6 py-4 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white rounded-lg font-bold text-lg transition-colors shadow-lg hover:shadow-red-900/50"
            >
              <StopCircle className="w-6 h-6" />
              PANIC - CLOSE ALL POSITIONS
            </button>

            <div className="bg-gray-800 rounded-lg p-4 flex items-center">
              <p className="text-xs text-gray-400">
                <strong className="text-red-400">Warning:</strong> Emergency controls will execute market orders immediately.
                Use only in critical situations. Halting stops new accumulation but maintains current positions.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Panic Confirmation Modal */}
      {showPanicConfirm && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-gray-900 border-2 border-red-600 rounded-lg p-6 max-w-md mx-4">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle className="w-8 h-8 text-red-500" />
              <h3 className="text-xl font-bold text-white">Confirm Panic Close</h3>
            </div>
            <p className="text-gray-300 mb-6">
              This will immediately close ALL positions using market orders. This action cannot be undone.
              Are you sure you want to proceed?
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowPanicConfirm(false)}
                disabled={isProcessing}
                className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-semibold transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handlePanicConfirm}
                disabled={isProcessing}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-bold transition-colors"
              >
                {isProcessing ? 'Closing...' : 'YES, CLOSE ALL'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Halt Confirmation Modal */}
      {showHaltConfirm && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-gray-900 border-2 border-yellow-600 rounded-lg p-6 max-w-md mx-4">
            <div className="flex items-center gap-3 mb-4">
              <Pause className="w-8 h-8 text-yellow-500" />
              <h3 className="text-xl font-bold text-white">Confirm Halt Accumulation</h3>
            </div>
            <p className="text-gray-300 mb-6">
              This will stop the bot from making new purchases. Current positions will be maintained.
              You can resume accumulation at any time.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowHaltConfirm(false)}
                disabled={isProcessing}
                className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-semibold transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleHaltConfirm}
                disabled={isProcessing}
                className="flex-1 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg font-bold transition-colors"
              >
                {isProcessing ? 'Halting...' : 'YES, HALT'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
