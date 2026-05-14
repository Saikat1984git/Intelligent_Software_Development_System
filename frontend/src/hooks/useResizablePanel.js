import { useState, useRef, useCallback } from 'react';

/**
 * useResizablePanel
 *
 * FIX: The previous version used moveEvent.clientX directly,
 * which made the panel snap to wherever the mouse was relative
 * to the full viewport on mousedown — causing a jump.
 *
 * The correct approach:
 * 1. On mousedown, record the current leftPanelWidth as a %.
 * 2. Record the mousedown X position.
 * 3. On mousemove, calculate how many px the mouse has moved,
 *    convert that delta to a %, and ADD it to the start width.
 *
 * This means the divider always moves from wherever it already
 * is — no jump, no snap, drag starts exactly where you click.
 *
 * @param {number} initialWidth  Starting left % (default 40)
 * @param {number} minWidth      Min left % (default 25)
 * @param {number} maxWidth      Max left % (default 75)
 */
const useResizablePanel = (initialWidth = 40, minWidth = 25, maxWidth = 75) => {
  const [leftPanelWidth, setLeftPanelWidth] = useState(initialWidth);
  const containerRef = useRef(null);

  const handleMouseDown = useCallback((e) => {
    e.preventDefault();

    // Capture starting state at the moment of click
    const startX         = e.clientX;
    const startWidth     = leftPanelWidth; // % at time of click
    const containerWidth = containerRef.current?.offsetWidth;

    if (!containerWidth) return;

    const onMouseMove = (moveEvent) => {
      // How far has the mouse moved in px since mousedown?
      const deltaPx = moveEvent.clientX - startX;

      // Convert px delta to percentage of container width
      const deltaPercent = (deltaPx / containerWidth) * 100;

      // New width = where we started + how far we moved
      const newWidth = startWidth + deltaPercent;

      if (newWidth >= minWidth && newWidth <= maxWidth) {
        setLeftPanelWidth(newWidth);
      }
    };

    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup',   onMouseUp);
    };

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup',   onMouseUp);
  }, [leftPanelWidth, minWidth, maxWidth]);

  return { leftPanelWidth, handleMouseDown, containerRef };
};

export default useResizablePanel;