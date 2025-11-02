/**
 * Utility functions for formatting financial numbers
 */

export const formatCurrency = (value, decimals = 2) => {
  if (!value && value !== 0) return 'N/A';
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return 'N/A';
  
  // Determine unit (Crores, Millions, etc.)
  let unit = '';
  let displayValue = num;
  
  if (Math.abs(num) >= 10000000) { // >= 10 Crores
    displayValue = num / 10000000;
    unit = 'Cr';
  } else if (Math.abs(num) >= 100000) { // >= 1 Lakh
    displayValue = num / 100000;
    unit = 'L';
  } else if (Math.abs(num) >= 1000) { // >= 1 Thousand
    displayValue = num / 1000;
    unit = 'K';
  }
  
  return `₹${displayValue.toFixed(decimals)} ${unit}`.trim();
};

export const formatPercentage = (value, decimals = 2) => {
  if (!value && value !== 0) return 'N/A';
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return 'N/A';
  return `${num >= 0 ? '+' : ''}${num.toFixed(decimals)}%`;
};

export const formatRatio = (value, decimals = 2) => {
  if (!value && value !== 0) return 'N/A';
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return 'N/A';
  return num.toFixed(decimals);
};

export const formatNumber = (value, decimals = 0) => {
  if (!value && value !== 0) return 'N/A';
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return 'N/A';
  return new Intl.NumberFormat('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
};

