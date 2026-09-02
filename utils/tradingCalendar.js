// Trading Calendar Utility
// Location: /home/ubuntu/apps/real-time-fund/utils/tradingCalendar.js

const { execSync } = require('child_process');

// Time zone constant
const TIME_ZONE = 'Asia/Shanghai';

// Chinese stock market holidays (simplified list for common holidays)
const CHINA_HOLIDAYS = [
  // 2024 Holidays
  '2024-01-01', // New Year
  '2024-02-10', '2024-02-11', '2024-02-12', '2024-02-13', '2024-02-14', '2024-02-15', '2024-02-16', '2024-02-17', // Spring Festival
  '2024-04-04', '2024-04-05', '2024-04-06', // Qingming Festival
  '2024-05-01', '2024-05-02', '2024-05-03', // Labor Day
  '2024-06-10', // Dragon Boat Festival
  '2024-09-15', '2024-09-16', '2024-09-17', // Mid-Autumn Festival
  '2024-10-01', '2024-10-02', '2024-10-03', '2024-10-04', '2024-10-05', '2024-10-06', '2024-10-07', // National Day
  
  // 2025 Holidays
  '2025-01-01', // New Year
  '2025-01-28', '2025-01-29', '2025-01-30', '2025-01-31', '2025-02-01', '2025-02-02', '2025-02-03', '2025-02-04', // Spring Festival
  '2025-04-04', '2025-04-05', '2025-04-06', // Qingming Festival
  '2025-05-01', '2025-05-02', '2025-05-03', // Labor Day
  '2025-05-31', // Dragon Boat Festival
  '2025-10-01', '2025-10-02', '2025-10-03', '2025-10-04', '2025-10-05', '2025-10-06', '2025-10-07', // National Day
];

/**
 * Format date to YYYY-MM-DD string
 * @param {Date} date 
 * @returns {string}
 */
function formatDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Format date to YYYY-MM-DD HH:MM:SS in specified timezone
 * @param {Date} date 
 * @param {string} timezone 
 * @returns {string}
 */
function formatDateTime(date, timezone = TIME_ZONE) {
  return date.toLocaleString('zh-CN', { timeZone: timezone });
}

/**
 * Check if a date is a weekend
 * @param {Date} date 
 * @returns {boolean}
 */
function isWeekend(date) {
  const day = date.getDay();
  return day === 0 || day === 6; // Sunday = 0, Saturday = 6
}

/**
 * Check if a date is a Chinese stock market holiday
 * @param {Date} date 
 * @returns {boolean}
 */
function isHoliday(date) {
  const dateStr = formatDate(date);
  return CHINA_HOLIDAYS.includes(dateStr);
}

/**
 * Check if today is a trading day
 * @param {Date} [date] - Optional date to check, defaults to today
 * @returns {boolean}
 */
function isTradingDay(date = new Date()) {
  // Check if weekend
  if (isWeekend(date)) {
    console.log(`[${formatDateTime(date)}] Weekend - Not a trading day`);
    return false;
  }
  
  // Check if holiday
  if (isHoliday(date)) {
    console.log(`[${formatDateTime(date)}] Holiday - Not a trading day`);
    return false;
  }
  
  console.log(`[${formatDateTime(date)}] Trading day confirmed`);
  return true;
}

/**
 * Get the next trading day
 * @param {Date} [fromDate] - Optional starting date, defaults to today
 * @returns {Date}
 */
function getNextTradingDay(fromDate = new Date()) {
  let nextDay = new Date(fromDate);
  nextDay.setDate(nextDay.getDate() + 1);
  
  while (!isTradingDay(nextDay)) {
    nextDay.setDate(nextDay.getDate() + 1);
  }
  
  return nextDay;
}

/**
 * Get the previous trading day
 * @param {Date} [fromDate] - Optional starting date, defaults to today
 * @returns {Date}
 */
function getPreviousTradingDay(fromDate = new Date()) {
  let prevDay = new Date(fromDate);
  prevDay.setDate(prevDay.getDate() - 1);
  
  while (!isTradingDay(prevDay)) {
    prevDay.setDate(prevDay.getDate() - 1);
  }
  
  return prevDay;
}

/**
 * Get market hours for today
 * @returns {{ open: Date, close: Date }}
 */
function getMarketHours() {
  const today = new Date();
  today.setHours(9, 30, 0, 0);
  const open = new Date(today);
  
  const close = new Date(today);
  close.setHours(16, 0, 0, 0);
  
  return { open, close };
}

/**
 * Check if current time is within market hours
 * @param {Date} [date] - Optional date to check, defaults to now
 * @returns {boolean}
 */
function isWithinMarketHours(date = new Date()) {
  const hours = getMarketHours();
  return date >= hours.open && date <= hours.close;
}

/**
 * Get time until market opens (in milliseconds)
 * @returns {number}
 */
function getTimeUntilMarketOpen() {
  const now = new Date();
  const { open } = getMarketHours();
  
  // If it's already past today's open time, get next trading day's open
  if (now > open) {
    const nextTradingDay = getNextTradingDay(now);
    nextTradingDay.setHours(9, 30, 0, 0);
    return nextTradingDay.getTime() - now.getTime();
  }
  
  return open.getTime() - now.getTime();
}

/**
 * Get time until market closes (in milliseconds)
 * @returns {number}
 */
function getTimeUntilMarketClose() {
  const now = new Date();
  const { close } = getMarketHours();
  
  if (now > close) {
    // Market closed for today
    return 0;
  }
  
  return close.getTime() - now.getTime();
}

module.exports = {
  isTradingDay,
  isWeekend,
  isHoliday,
  isWithinMarketHours,
  getNextTradingDay,
  getPreviousTradingDay,
  getMarketHours,
  getTimeUntilMarketOpen,
  getTimeUntilMarketClose,
  formatDate,
  formatDateTime,
  TIME_ZONE
};