/**
 * Frontend logging utility for debugging user actions
 */

interface LogEntry {
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
  category: string;
  message: string;
  details?: any;
  user?: string;
  location?: string;
}

class Logger {
  private logs: LogEntry[] = [];
  private maxLogs = 1000; // Keep last 1000 logs in memory

  private createEntry(
    level: LogEntry['level'],
    category: string,
    message: string,
    details?: any
  ): LogEntry {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      category,
      message,
      details,
      location: window.location.pathname,
    };

    // Add user info if available
    try {
      const authStorage = sessionStorage.getItem('auth-storage');
      if (authStorage) {
        const auth = JSON.parse(authStorage);
        if (auth.state?.user) {
          entry.user = `${auth.state.user.username} (${auth.state.user.role})`;
        }
      }
    } catch (e) {
      // Ignore errors getting user info
    }

    return entry;
  }

  private log(entry: LogEntry) {
    // Add to in-memory logs
    this.logs.push(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift(); // Remove oldest
    }

    // Console output with styling
    const styles = {
      DEBUG: 'color: gray',
      INFO: 'color: blue',
      WARN: 'color: orange',
      ERROR: 'color: red; font-weight: bold',
    };

    const prefix = `[${entry.timestamp}] [${entry.level}] [${entry.category}]`;
    
    if (entry.details) {
      console.log(`%c${prefix} ${entry.message}`, styles[entry.level], entry.details);
    } else {
      console.log(`%c${prefix} ${entry.message}`, styles[entry.level]);
    }

    // Send important logs to backend (optional - implement later)
    if (entry.level === 'ERROR') {
      this.sendToBackend(entry);
    }
  }

  private async sendToBackend(_entry: LogEntry) {
    try {
      // Optional: Send to backend logging endpoint
      // await fetch('/api/logs/frontend', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(_entry)
      // });
    } catch (e) {
      // Ignore errors sending logs
    }
  }

  debug(category: string, message: string, details?: any) {
    this.log(this.createEntry('DEBUG', category, message, details));
  }

  info(category: string, message: string, details?: any) {
    this.log(this.createEntry('INFO', category, message, details));
  }

  warn(category: string, message: string, details?: any) {
    this.log(this.createEntry('WARN', category, message, details));
  }

  error(category: string, message: string, details?: any) {
    this.log(this.createEntry('ERROR', category, message, details));
  }

  // User action logging - high-level tracking
  userAction(action: string, details?: any) {
    this.info('USER_ACTION', action, details);
  }

  // API call logging
  apiCall(method: string, url: string, data?: any) {
    this.debug('API', `${method} ${url}`, data);
  }

  apiResponse(method: string, url: string, status: number, data?: any) {
    const level = status >= 400 ? 'ERROR' : 'DEBUG';
    this.log(
      this.createEntry(level, 'API', `${method} ${url} -> ${status}`, data)
    );
  }

  // Navigation logging
  navigation(from: string, to: string) {
    this.info('NAVIGATION', `${from} -> ${to}`);
  }

  // Medication administration flow
  medicationFlow(step: string, details?: any) {
    this.info('MEDICATION_FLOW', step, details);
  }

  // Get all logs (for debugging)
  getAllLogs(): LogEntry[] {
    return [...this.logs];
  }

  // Export logs as text
  exportLogs(): string {
    return this.logs
      .map(
        (log) =>
          `${log.timestamp} | ${log.level.padEnd(5)} | ${log.category.padEnd(
            15
          )} | ${log.user || 'N/A'} | ${log.message}${
            log.details ? ` | ${JSON.stringify(log.details)}` : ''
          }`
      )
      .join('\n');
  }

  // Clear logs
  clear() {
    this.logs = [];
    console.clear();
    this.info('LOGGER', 'Logs cleared');
  }
}

// Create singleton instance
export const logger = new Logger();

// Make available in console for debugging
if (typeof window !== 'undefined') {
  (window as any).logger = logger;
}

// Log page loads
logger.info('APP', 'Application loaded');
