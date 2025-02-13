import { DFTError } from '../types';

export const readFileContent = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target?.result as string);
    reader.onerror = (e) => reject(new DFTError('Error reading file'));
    reader.readAsText(file);
  });
};

export const parseFileContent = (content: string): number[] => {
  return content
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0)
    .map(line => {
      const num = parseFloat(line);
      if (isNaN(num)) {
        throw new DFTError('Invalid number in data');
      }
      return num;
    });
};

export const validateSignalData = (data: number[]) => {
  if (data.length === 0) {
    throw new DFTError('File contains no valid data');
  }
  
  if (data.length > 1000000) {
    throw new DFTError('File too large: maximum 1,000,000 points allowed');
  }

  if (data.some(val => !isFinite(val))) {
    throw new DFTError('Data contains invalid values (infinity or NaN)');
  }
};
