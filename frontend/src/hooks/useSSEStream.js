import { useState, useCallback, useRef } from 'react';

/**
 * useSSEStream
 * Handles fetch → ReadableStream → SSE (Server-Sent Events) parsing.
 * Works with both JSON-line streams (Codegen) and data: SSE streams (Codeedit).
 *
 * @param {string}   url       - API endpoint
 * @param {Function} onEvent   - Called for every parsed event payload (object or string)
 * @param {Function} onDone    - Called when stream ends cleanly
 * @param {Function} onError   - Called on fetch or parse error
 *
 * @returns {{ status, trigger, reset }}
 *   status: 'idle' | 'connecting' | 'streaming' | 'done' | 'error'
 *   trigger(body, options): starts the stream  — body is FormData or plain object
 *   reset(): resets status back to idle
 *
 * Usage (JSON-line mode — Codegen style):
 *   const { status, trigger } = useSSEStream(
 *     `${API_BASE_URL}/run`,
 *     (payload) => { ... handle payload object ... },
 *     () => setStatus('completed'),
 *     (err) => console.error(err)
 *   );
 *   trigger({ requirements: userText });
 *
 * Usage (SSE data: mode — Codeedit style):
 *   const { status, trigger } = useSSEStream(
 *     `${API_BASE_URL}/rewrite`,
 *     (message) => { ... handle string message ... },
 *     () => setDone(true),
 *     (err) => console.error(err),
 *   );
 *   trigger(formData);  // pass FormData directly
 */
const useSSEStream = (url, onEvent, onDone, onError) => {
  const [status, setStatus] = useState('idle');
  const readerRef = useRef(null);

  const reset = useCallback(() => {
    setStatus('idle');
  }, []);

  const trigger = useCallback(async (body) => {
    setStatus('connecting');

    // Determine if body is FormData (Codeedit) or JSON (Codegen / BugSupport)
    const isFormData = body instanceof FormData;

    const fetchOptions = {
      method: 'POST',
      body: isFormData ? body : JSON.stringify(body),
      ...(!isFormData && { headers: { 'Content-Type': 'application/json' } }),
    };

    try {
      const response = await fetch(url, fetchOptions);

      if (!response.ok || !response.body) {
        throw new Error(`Server error: HTTP ${response.status} ${response.statusText}`);
      }

      setStatus('streaming');

      const reader = response.body.getReader();
      readerRef.current = reader;
      const decoder = new TextDecoder('utf-8', { fatal: false });
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // --- SSE format: split on double newline (data: ... \n\n) ---
        if (buffer.includes('\n\n')) {
          const parts = buffer.split('\n\n');
          buffer = parts.pop() || '';

          for (const part of parts) {
            const trimmed = part.trim();
            if (!trimmed) continue;

            if (trimmed.startsWith('data:')) {
              const message = trimmed.replace(/^data:\s*/, '').trim();
              if (message === '[DONE]') {
                setStatus('done');
                onDone?.();
                return;
              }
              onEvent?.(message);
              continue;
            }

            // --- JSON-line format (no data: prefix) ---
            try {
              const payload = JSON.parse(trimmed);
              onEvent?.(payload);
            } catch {
              // plain text line — pass through as-is
              if (trimmed.length > 2) onEvent?.(trimmed);
            }
          }
        } else {
          // --- JSON-line format: split on single newline ---
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed) continue;

            try {
              const payload = JSON.parse(trimmed);
              onEvent?.(payload);
            } catch {
              if (trimmed.length > 2) onEvent?.(trimmed);
            }
          }
        }
      }

      setStatus('done');
      onDone?.();
    } catch (err) {
      setStatus('error');
      onError?.(err);
    }
  }, [url, onEvent, onDone, onError]);

  return { status, trigger, reset };
};

export default useSSEStream;
