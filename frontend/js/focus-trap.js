// Mr.E — Reusable Focus Trap (Task 18.2)
// ─────────────────────────────────────────────────────────────────────────────
// Extracted from frontend/js/subscription-modal.js so every modal in the app
// can share the same accessible keyboard-handling behaviour.
//
//   • Tab / Shift+Tab cycle within the modal's focusable elements
//   • Escape closes the modal (via the optional `onEscape` callback)
//   • Focus is moved into the modal when activated and restored to the
//     element that opened the modal when deactivated
//   • Multiple modals can be stacked — only the top-most modal traps focus
//
// Public API (also attached as `window.FocusTrap`):
//
//   FocusTrap.activate(modalEl, options?)
//     options.onEscape       function called when Escape is pressed
//                            (defaults to a no-op; pass your close handler)
//     options.initialFocus   element or selector to focus first
//                            (defaults to the first focusable child)
//     options.escapeClosable boolean — when false the Escape key is ignored
//                            (defaults to true)
//
//   FocusTrap.deactivate(modalEl?)
//     Removes the trap. Pass the modal element to remove a specific trap
//     from anywhere in the stack; omit to deactivate the top-most trap.
//
//   FocusTrap.isActive(modalEl)
//     Whether the given element is currently trapping focus.
//
// Requirements: 13.6, 13.7

(function (root) {
  'use strict';

  // ── Internal state ──────────────────────────────────────────────────────

  // Stack of active traps so nested modals work correctly. The element at
  // the top (last) is the one currently in control of keyboard handling.
  var _stack = [];

  // Single document-level keydown listener — attached lazily when the first
  // trap is activated and detached when the stack drains.
  var _keydownAttached = false;

  // ── Helpers ─────────────────────────────────────────────────────────────

  var FOCUSABLE_SELECTOR = [
    'a[href]',
    'area[href]',
    'button:not([disabled])',
    'input:not([disabled]):not([type="hidden"])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    'iframe',
    'audio[controls]',
    'video[controls]',
    '[contenteditable]:not([contenteditable="false"])',
    '[tabindex]:not([tabindex="-1"])',
  ].join(',');

  /**
   * Return all currently-focusable descendants of `root` in document order.
   * Re-queried on every Tab keypress so dynamically added / removed elements
   * (e.g. retry buttons, billing rows) are honoured immediately.
   */
  function _getFocusable(root) {
    if (!root || typeof root.querySelectorAll !== 'function') return [];

    var nodes = Array.prototype.slice.call(
      root.querySelectorAll(FOCUSABLE_SELECTOR)
    );

    return nodes.filter(function (el) {
      if (el.hasAttribute('disabled')) return false;
      if (el.getAttribute('aria-hidden') === 'true') return false;
      if (el.getAttribute('tabindex') === '-1') return false;

      // Skip elements that are not laid out (display:none / visibility:hidden /
      // an ancestor with display:none).
      if (el.offsetParent === null && el !== document.activeElement) {
        var style = (typeof window !== 'undefined' && window.getComputedStyle)
          ? window.getComputedStyle(el)
          : null;
        if (!style) return false;
        if (style.visibility === 'hidden' || style.display === 'none') {
          return false;
        }
        // Position: fixed elements can have offsetParent === null even when
        // visible — fall through to the visibility/display check above and
        // accept them when they pass.
      }
      return true;
    });
  }

  function _safeFocus(el) {
    if (!el || typeof el.focus !== 'function') return;
    try {
      el.focus({ preventScroll: true });
    } catch (e) {
      try { el.focus(); } catch (_) { /* noop */ }
    }
  }

  function _resolveInitialFocus(modalEl, initialFocus) {
    if (!initialFocus) return null;
    if (typeof initialFocus === 'string') {
      try { return modalEl.querySelector(initialFocus); }
      catch (e) { return null; }
    }
    if (initialFocus.nodeType === 1) return initialFocus;
    return null;
  }

  function _topTrap() {
    return _stack.length ? _stack[_stack.length - 1] : null;
  }

  // ── Document-level keydown handler ──────────────────────────────────────

  function _onDocumentKeyDown(evt) {
    var trap = _topTrap();
    if (!trap || !trap.modalEl || !document.body.contains(trap.modalEl)) {
      return;
    }

    var key = evt.key;
    var keyCode = evt.keyCode;

    if (key === 'Escape' || keyCode === 27) {
      if (trap.escapeClosable === false) return;
      evt.preventDefault();
      try {
        if (typeof trap.onEscape === 'function') trap.onEscape(evt);
      } catch (e) {
        // Don't let a buggy onEscape handler crash the trap.
        if (typeof console !== 'undefined' && console.error) {
          console.error('FocusTrap onEscape handler threw:', e);
        }
      }
      return;
    }

    if (key !== 'Tab' && keyCode !== 9) return;

    var focusable = _getFocusable(trap.modalEl);

    if (focusable.length === 0) {
      // Nothing to focus inside — pin focus on the dialog itself so the
      // user can't escape into background page content with Tab.
      evt.preventDefault();
      _safeFocus(trap.modalEl);
      return;
    }

    var first = focusable[0];
    var last = focusable[focusable.length - 1];
    var active = document.activeElement;
    var insideModal = trap.modalEl.contains(active);

    if (evt.shiftKey) {
      if (active === first || !insideModal) {
        evt.preventDefault();
        _safeFocus(last);
      }
    } else {
      if (active === last || !insideModal) {
        evt.preventDefault();
        _safeFocus(first);
      }
    }
  }

  function _attachKeydown() {
    if (_keydownAttached) return;
    if (typeof document === 'undefined') return;
    document.addEventListener('keydown', _onDocumentKeyDown, true);
    _keydownAttached = true;
  }

  function _detachKeydownIfEmpty() {
    if (_stack.length > 0 || !_keydownAttached) return;
    if (typeof document === 'undefined') return;
    document.removeEventListener('keydown', _onDocumentKeyDown, true);
    _keydownAttached = false;
  }

  // ── Public API ──────────────────────────────────────────────────────────

  /**
   * Begin trapping focus inside `modalEl`. Idempotent — calling activate
   * a second time on the same element refreshes options and re-focuses
   * but does not double-stack. Pre-existing traps for other modals remain
   * on the stack so they can resume control when this one is deactivated.
   */
  function activate(modalEl, options) {
    if (!modalEl || modalEl.nodeType !== 1) return null;
    options = options || {};

    // If the same modal is already trapping focus, refresh its options
    // (callers may want to swap onEscape, etc.) and re-focus.
    var existing = null;
    for (var i = 0; i < _stack.length; i++) {
      if (_stack[i].modalEl === modalEl) { existing = _stack[i]; break; }
    }

    if (existing) {
      if (typeof options.onEscape === 'function') {
        existing.onEscape = options.onEscape;
      }
      if (typeof options.escapeClosable === 'boolean') {
        existing.escapeClosable = options.escapeClosable;
      }
      // Move it to the top so it controls keyboard handling.
      _stack = _stack.filter(function (t) { return t !== existing; });
      _stack.push(existing);
      return existing;
    }

    var trap = {
      modalEl: modalEl,
      onEscape: typeof options.onEscape === 'function' ? options.onEscape : null,
      escapeClosable: options.escapeClosable !== false,
      previouslyFocused: (typeof document !== 'undefined') ? document.activeElement : null,
    };

    _stack.push(trap);
    _attachKeydown();

    // Move focus into the dialog. Defer slightly so the browser registers
    // the visibility change before focusing — avoids transitions fighting
    // with focus and avoids unwanted scroll-into-view jumps.
    var initialTarget = _resolveInitialFocus(modalEl, options.initialFocus);

    setTimeout(function () {
      // Bail out if the trap was already deactivated before the timer fired.
      if (_stack.indexOf(trap) === -1) return;
      if (!document.body.contains(modalEl)) return;

      var target = initialTarget;
      if (!target) {
        var focusable = _getFocusable(modalEl);
        target = focusable[0] || modalEl;
      }
      _safeFocus(target);
    }, 0);

    return trap;
  }

  /**
   * Remove the focus trap. When `modalEl` is supplied the matching trap
   * is removed from the stack regardless of its position; otherwise the
   * top-most trap is deactivated. Focus is restored to whatever element
   * had focus before this trap was activated, when possible.
   */
  function deactivate(modalEl) {
    if (_stack.length === 0) return;

    var trap = null;
    if (modalEl) {
      for (var i = _stack.length - 1; i >= 0; i--) {
        if (_stack[i].modalEl === modalEl) {
          trap = _stack[i];
          _stack.splice(i, 1);
          break;
        }
      }
    } else {
      trap = _stack.pop();
    }

    if (!trap) return;

    // Only restore focus when this trap was at the top of the stack —
    // otherwise we'd steal focus from the still-active modal above us.
    var wasTop = !_topTrap() || _topTrap() !== trap;
    if (trap.previouslyFocused &&
        typeof trap.previouslyFocused.focus === 'function' &&
        wasTop) {
      // Defer slightly so browser focus rings settle after any close
      // animations.
      var prev = trap.previouslyFocused;
      setTimeout(function () { _safeFocus(prev); }, 0);
    }
    trap.previouslyFocused = null;

    _detachKeydownIfEmpty();
  }

  /**
   * Whether `modalEl` is currently trapping focus (anywhere in the stack).
   */
  function isActive(modalEl) {
    if (!modalEl) return _stack.length > 0;
    for (var i = 0; i < _stack.length; i++) {
      if (_stack[i].modalEl === modalEl) return true;
    }
    return false;
  }

  // ── Expose ──────────────────────────────────────────────────────────────

  var FocusTrap = {
    activate: activate,
    deactivate: deactivate,
    isActive: isActive,
    // Exposed for unit / property tests.
    _getFocusable: _getFocusable,
  };

  if (typeof root !== 'undefined') {
    root.FocusTrap = FocusTrap;
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = FocusTrap;
  }
})(typeof window !== 'undefined' ? window : this);
