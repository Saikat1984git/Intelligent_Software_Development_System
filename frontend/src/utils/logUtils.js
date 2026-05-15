/* ============================================================
   logUtils.js
   Utility functions extracted from Codegen.jsx.
   Used by Codegen page and ConsoleLog molecule.
   ============================================================ */

/**
 * Strip ANSI escape codes from terminal output strings.
 */
export const stripAnsi = (text) => {
  if (!text) return '';
  return text
    .replace(/\x1b\[[0-9;]*[a-zA-Z]/g, '')
    .replace(/\x1b\][^\x07]*\x07/g, '')
    .replace(/\x1bP[^\x07]*\x07/g, '')
    .replace(/\x1b\^[^\x07]*\x07/g, '')
    .replace(/\x1b_[^\x07]*\x07/g, '')
    .replace(/\[([0-9;]+)?m/g, '')
    .replace(/\[.*?[@-~]/g, '')
    .trim();
};

/**
 * Categorize a log line into a display type.
 * Checks success/complete BEFORE error to avoid false positives.
 */
export const categorizeLog = (text) => {
  const lower = text.toLowerCase();
  if (
    lower.includes('success') ||
    lower.includes('complete') ||
    lower.includes('done') ||
    lower.includes('ready') ||
    lower.includes('generated')
  ) return 'success';
  if (lower.includes('warning') || lower.includes('warn')) return 'warning';
  if (
    lower.includes('error') ||
    lower.includes('failed') ||
    lower.includes('exception')
  ) return 'error';
  if (
    lower.includes('debugging') ||
    lower.includes('fixing') ||
    lower.includes('retry')
  ) return 'debug';
  return 'info';
};

/**
 * Format a raw log string for cleaner terminal display.
 * Strips markdown, truncates long lines, condenses large summaries.
 */
export const formatLogText = (text) => {
  if (!text) return '';

  // Condense large codebase summaries
  if (text.length > 200 && text.includes('Summary of Codebase')) {
    const lines = text.split('\n').filter(l => l.trim().startsWith('*'));
    const keyItems = lines
      .slice(0, 3)
      .map(l => l.replace(/^\*\s*\*?\*/g, '').trim())
      .join(' | ');
    if (keyItems) return keyItems;
    return text.substring(0, 100).replace(/\n/g, ' ') + '...';
  }

  // Strip markdown formatting
  let formatted = text
    .replace(/###\s*/g, '')
    .replace(/##\s*/g, '')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/```[\s\S]*?```/g, '[code]')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/^\s*[-*]\s+/gm, '• ')
    .replace(/^\s*\d+\.\s+/gm, '• ');

  if (formatted.length > 150) {
    formatted = formatted.substring(0, 150) + '...';
  }

  return formatted;
};

/**
 * Parse a terminal summary string into a structured object
 * suitable for rendering in SummaryCard / ChatSummaryMessage.
 * Returns null if the text doesn't look like a summary.
 */
export const parseSummary = (text) => {
  if (!text || typeof text !== 'string') return null;

  const isSummary =
    text.toLowerCase().includes('summary of codebase') ||
    text.toLowerCase().includes('project summary') ||
    text.toLowerCase().includes('accomplishments') ||
    text.toLowerCase().includes('execution highlights') ||
    text.toLowerCase().includes('codebase generation') ||
    (text.includes('*') && text.includes(':') && text.length > 100);

  if (!isSummary) return null;

  const result = {
    title: '',
    sections: [],
    stats: {},
    raw: text,
  };

  // Extract title
  const titlePatterns = [
    /###?\s*\*\*Project Summary:\*\*\s*(.+?)(?:\n|$)/i,
    /Project Summary:?\s*(.+?)(?:\n|$)/i,
    /##?\s*(.+? Application)/i,
    /^(.+? To-Do Application)/i,
  ];
  for (const pattern of titlePatterns) {
    const match = text.match(pattern);
    if (match) {
      result.title = match[1].trim();
      break;
    }
  }
  if (!result.title) {
    const firstLine = text.split('\n').find(l => l.trim() && l.includes('*'));
    if (firstLine) result.title = 'Code Generation Complete';
  }

  // Parse bullet points and key-value pairs
  const lines = text.split('\n');
  const bullets = [];

  lines.forEach(line => {
    line = line.trim();
    if (!line) return;

    const bulletMatch = line.match(/^\*\*?\s*(.+?)(?:\*\*:?|\s*:\s*)(.+)$/);
    if (bulletMatch) {
      const key   = bulletMatch[1].trim().replace(/\*\*?/g, '').trim();
      const value = bulletMatch[2].trim();
      if (
        value &&
        (
          key.toLowerCase().includes('rate') ||
          key.toLowerCase().includes('files') ||
          key.toLowerCase().includes('error') ||
          key.toLowerCase().includes('success')
        )
      ) {
        result.stats[key] = value;
      } else {
        bullets.push(`${key}: ${value}`);
      }
    } else if (line.startsWith('* ')) {
      const content = line.replace(/^\*\s*/, '').trim();
      if (content) bullets.push(content);
    }
  });

  // Extract numeric stats from raw text
  const successMatch = text.match(/success.*?rate.*?(\d+%)/i);
  if (successMatch) result.stats['Success Rate'] = successMatch[1];

  const filesMatch = text.match(/(?:generated|files?)\D*(\d+)/i);
  if (filesMatch) result.stats['Files Generated'] = filesMatch[1];

  const errorsMatch = text.match(/errors?.*?(\d+)/i);
  if (errorsMatch) result.stats['Errors'] = errorsMatch[1];

  if (bullets.length > 0) {
    result.sections.push({
      title: 'Key Accomplishments',
      bullets: bullets.slice(0, 8),
      stats: { ...result.stats },
    });
  }

  if (Object.keys(result.stats).length > 0 && result.sections.length === 0) {
    result.sections.push({
      title: 'Results',
      bullets: [],
      stats: { ...result.stats },
    });
  }

  return result;
};
