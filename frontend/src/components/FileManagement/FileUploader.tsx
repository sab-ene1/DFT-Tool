import React, { useCallback, useMemo } from 'react';
import { useDropzone, FileRejection } from 'react-dropzone';
import { Upload, File, AlertCircle } from 'lucide-react';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

interface FileUploaderProps {
  onFileUpload: (files: File[]) => void;
  acceptedFileTypes?: string[];
  maxFileSize?: number;
}

const FileUploader: React.FC<FileUploaderProps> = React.memo(({
  onFileUpload,
  acceptedFileTypes = ['.wav', '.csv', '.txt'],
  maxFileSize = MAX_FILE_SIZE
}) => {
  const accept = useMemo(() => 
    acceptedFileTypes.reduce((acc, type) => ({
      ...acc,
      [type]: [type.replace('.', 'audio/'), type.replace('.', 'text/')]
    }), {}),
    [acceptedFileTypes]
  );

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
      if (rejectedFiles.length > 0) {
        console.error('Files rejected:', rejectedFiles);
        // Handle rejected files (could emit an event or show a notification)
        return;
      }

      const validFiles = acceptedFiles.filter(file => file.size <= maxFileSize);
      if (validFiles.length !== acceptedFiles.length) {
        console.error('Some files exceeded size limit');
        // Handle oversized files
        return;
      }

      onFileUpload(validFiles);
    },
    [onFileUpload, maxFileSize]
  );

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragReject
  } = useDropzone({
    onDrop,
    accept,
    maxSize: maxFileSize,
    multiple: true,
    preventDropOnDocument: true,
    noClick: false,
    noKeyboard: false,
  });

  const getDropzoneClass = useCallback(() => {
    if (isDragReject) return 'border-red-500 bg-red-50';
    if (isDragActive) return 'border-blue-500 bg-blue-50';
    return 'border-gray-300 hover:border-blue-400';
  }, [isDragActive, isDragReject]);

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`p-8 border-2 border-dashed rounded-lg cursor-pointer transition-colors ${getDropzoneClass()}`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center space-y-4">
          {isDragReject ? (
            <>
              <AlertCircle className="w-12 h-12 text-red-500" />
              <p className="text-red-500">File type not supported</p>
            </>
          ) : isDragActive ? (
            <Upload className="w-12 h-12 text-blue-500" />
          ) : (
            <File className="w-12 h-12 text-gray-400" />
          )}
          <div className="text-center">
            <p className="text-lg font-medium">
              {isDragActive
                ? 'Drop the file here...'
                : 'Drag & drop a file here, or click to select'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Supported formats: {acceptedFileTypes.join(', ')}
            </p>
            <p className="text-sm text-gray-500">
              Maximum file size: {(maxFileSize / (1024 * 1024)).toFixed(0)}MB
            </p>
          </div>
        </div>
      </div>
    </div>
  );
});

FileUploader.displayName = 'FileUploader';

export default FileUploader;
