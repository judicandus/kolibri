(function() {
  // Apply saved theme immediately (runs before Vue mounts)
  var theme = localStorage.getItem('angels-theme') || 'light';
  document.documentElement.setAttribute('data-theme', theme);

  // Create a fixed container outside Vue's scope
  function ensureToggle() {
    if (document.querySelector('.angels-theme-toggle')) return;
    if (!document.body) return;

    var wrapper = document.createElement('div');
    wrapper.id = 'angels-theme-toggle-root';
    wrapper.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:99999;';

    var btn = document.createElement('button');
    btn.className = 'angels-theme-toggle';
    btn.setAttribute('aria-label', 'Toggle dark/light theme');
    btn.setAttribute('title', 'Toggle dark/light theme');
    var currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    btn.textContent = currentTheme === 'dark' ? '\u2600' : '\u263E';
    btn.addEventListener('click', function() {
      var cur = document.documentElement.getAttribute('data-theme');
      var next = cur === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('angels-theme', next);
      btn.textContent = next === 'dark' ? '\u2600' : '\u263E';
      styleSideNavLinks();
      applyDarkModeBackgrounds();
    });

    wrapper.appendChild(btn);
    document.body.appendChild(wrapper);
  }

  // ===== SEARCH BAR IN APP BAR =====
  // Shared reference so repositioning can be called from the MutationObserver
  var _repositionSearchBar = null;

  function repositionSearchBar() {
    if (_repositionSearchBar) _repositionSearchBar();
  }

  function ensureSearchBar() {
    if (document.querySelector('.angels-search-bar')) return;
    if (!document.body) return;

    var toolbar = document.querySelector('.app-bar');
    if (!toolbar) return;

    // Only show when navigation links are visible (Learn pages)
    var navSection = toolbar.querySelector('.k-toolbar-nav');
    if (!navSection) return;

    var toolbarRight = toolbar.querySelector('.k-toolbar-right');
    if (!toolbarRight) return;

    var wrapper = document.createElement('div');
    wrapper.className = 'angels-search-bar';

    // Magnifying glass icon
    var icon = document.createElement('span');
    icon.className = 'angels-search-icon';
    icon.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" fill="rgba(255,255,255,0.6)"/></svg>';

    var input = document.createElement('input');
    input.type = 'text';
    input.className = 'angels-search-input';
    input.placeholder = 'Search';
    input.setAttribute('aria-label', 'Search all content');

    function doSearch() {
      var value = input.value.trim();
      if (value) {
        window.location.hash = '#/library?keywords=' + encodeURIComponent(value);
      }
    }

    input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        doSearch();
      }
    });

    icon.style.cursor = 'pointer';
    icon.addEventListener('click', doSearch);

    wrapper.appendChild(icon);
    wrapper.appendChild(input);

    // Append to body (outside Vue's scope) and position over the toolbar
    document.body.appendChild(wrapper);

    _repositionSearchBar = function() {
      // Re-query DOM every time — Vue re-renders replace elements on SPA navigation
      var tb = document.querySelector('.app-bar');
      if (!tb) { wrapper.style.display = 'none'; return; }
      var nav = tb.querySelector('.k-toolbar-nav');
      if (!nav) { wrapper.style.display = 'none'; return; }
      var actions = tb.querySelector('.k-toolbar-right');
      if (!actions) { wrapper.style.display = 'none'; return; }
      wrapper.style.display = 'flex';
      var navRect = nav.getBoundingClientRect();
      var actionsRect = actions.getBoundingClientRect();
      var toolbarRect = tb.getBoundingClientRect();
      // Guard against layout not yet computed (all zeros)
      if (navRect.right === 0 && actionsRect.left === 0) return;
      var left = navRect.right + 16;
      var right = window.innerWidth - actionsRect.left + 16;
      var top = toolbarRect.top + (toolbarRect.height - 36) / 2;
      wrapper.style.top = Math.round(top) + 'px';
      wrapper.style.left = Math.round(left) + 'px';
      wrapper.style.right = Math.round(right) + 'px';
    };

    _repositionSearchBar();
    window.addEventListener('resize', _repositionSearchBar);
  }

  // Style side nav elements for dark/light mode
  function styleSideNavLinks() {
    var isDark = document.documentElement.getAttribute('data-theme') === 'dark';

    // Sub-route links: white default, green for active (bold)
    var links = document.querySelectorAll('.side-nav .link');
    links.forEach(function(link) {
      var computedWeight = window.getComputedStyle(link).fontWeight;
      var isBold = computedWeight === 'bold' || parseInt(computedWeight) >= 700;
      if (isDark) {
        link.style.setProperty('color', isBold ? '#a6c52e' : '#ffffff', 'important');
      } else {
        link.style.removeProperty('color');
      }
    });

    // Active menu option (Learn): green backdrop in dark mode
    var menuOptions = document.querySelectorAll('.side-nav .core-menu-option');
    menuOptions.forEach(function(opt) {
      var bg = window.getComputedStyle(opt).backgroundColor;
      // Active items have a non-transparent background set by Kolibri
      var hasBackground = bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent';
      if (isDark && hasBackground) {
        opt.style.setProperty('background-color', '#a6c52e', 'important');
        opt.style.setProperty('color', '#1a2e43', 'important');
      } else if (isDark) {
        opt.style.removeProperty('background-color');
      } else {
        opt.style.removeProperty('background-color');
        opt.style.removeProperty('color');
      }
    });
  }

  // Override page title to "Angels Academy"
  function ensureTitle() {
    if (document.title && document.title !== 'Angels Academy') {
      document.title = 'Angels Academy';
    }
  }

  // Force dark backgrounds on content/quiz page elements whose inline styles
  // are set by Vue and resist CSS-only overrides.
  function applyDarkModeBackgrounds() {
    var isDark = document.documentElement.getAttribute('data-theme') === 'dark';

    // page-container (KPageContainer)
    document.querySelectorAll('.page-container').forEach(function(el) {
      if (isDark) {
        el.style.setProperty('background-color', 'transparent', 'important');
        el.style.setProperty('box-shadow', 'none', 'important');
      } else {
        el.style.removeProperty('background-color');
        el.style.removeProperty('box-shadow');
      }
    });

    // BaseToolbar "Get N correct" bar (quiz mastery bar)
    document.querySelectorAll('.base-toolbar').forEach(function(el) {
      if (isDark) {
        el.style.setProperty('background-color', '#213953', 'important');
        el.style.setProperty('color', '#e0e0e0', 'important');
        el.style.setProperty('box-shadow', 'none', 'important');
      } else {
        el.style.removeProperty('background-color');
        el.style.removeProperty('color');
        el.style.removeProperty('box-shadow');
      }
    });

    // Quiz content-wrapper (question area)
    document.querySelectorAll('.content-wrapper').forEach(function(el) {
      if (isDark) {
        el.style.setProperty('background-color', 'transparent', 'important');
      } else {
        el.style.removeProperty('background-color');
      }
    });

    // Perseus exercise container (scoped background: white)
    document.querySelectorAll('.perseus').forEach(function(el) {
      if (isDark) {
        el.style.setProperty('background', 'transparent', 'important');
      } else {
        el.style.removeProperty('background');
      }
    });

    // BottomAppBar attempts-container (quiz bottom bar)
    document.querySelectorAll('.bottom.attempts-container').forEach(function(el) {
      if (isDark) {
        el.style.setProperty('background-color', '#1a2e43', 'important');
        el.style.setProperty('color', '#e0e0e0', 'important');
      } else {
        el.style.removeProperty('background-color');
        el.style.removeProperty('color');
      }
    });

    // page-status (QuizReport header with "Get 10 correct")
    document.querySelectorAll('.page-status').forEach(function(el) {
      if (isDark) {
        el.style.setProperty('background-color', '#213953', 'important');
      } else {
        el.style.removeProperty('background-color');
      }
    });

    // exercise-container (QuizReport question review area)
    document.querySelectorAll('.exercise-container').forEach(function(el) {
      if (isDark) {
        el.style.setProperty('background-color', 'transparent', 'important');
      } else {
        el.style.removeProperty('background-color');
      }
    });

    // try-selection (attempt selector dropdown)
    document.querySelectorAll('.try-selection').forEach(function(el) {
      if (isDark) {
        el.style.setProperty('background-color', '#253547', 'important');
      } else {
        el.style.removeProperty('background-color');
      }
    });

    // .content wrapper inside [role=main] (ContentPage wrapper)
    var mainEl = document.querySelector('[role="main"]');
    if (mainEl) {
      var contentEl = mainEl.querySelector('.content');
      if (contentEl) {
        if (isDark) {
          contentEl.style.setProperty('background-color', 'transparent', 'important');
        } else {
          contentEl.style.removeProperty('background-color');
        }
      }
    }

    // PDF viewer elements
    document.querySelectorAll('.pdf-sidebar').forEach(function(el) {
      if (isDark) {
        el.style.setProperty('background', '#1a2e43', 'important');
      } else {
        el.style.removeProperty('background');
      }
    });
    document.querySelectorAll('.pdf-controls-container').forEach(function(el) {
      if (isDark) {
        el.style.setProperty('background-color', '#213953', 'important');
      } else {
        el.style.removeProperty('background-color');
      }
    });

    // ImmersivePage #main.main-wrapper
    var immersiveMain = document.getElementById('main');
    if (immersiveMain && immersiveMain.classList.contains('main-wrapper')) {
      if (isDark) {
        immersiveMain.style.setProperty('background-color', 'transparent', 'important');
      } else {
        immersiveMain.style.removeProperty('background-color');
      }
    }

    // Selected quiz option: override inline styles from Perseus
    document.querySelectorAll('.perseus-widget-radio li.perseus-radio-selected').forEach(function(li) {
      if (isDark) {
        // Override inline color on description div
        var desc = li.querySelector('.description');
        if (desc) desc.style.setProperty('color', '#ffffff', 'important');
        // Override inline background/border on choice icon
        var icon = li.querySelector('[data-testid="choice-icon__library-choice-icon"]');
        if (icon) {
          icon.style.setProperty('background-color', '#a6c52e', 'important');
          icon.style.setProperty('border-color', '#a6c52e', 'important');
          icon.style.setProperty('color', '#1a2e43', 'important');
        }
      } else {
        var desc = li.querySelector('.description');
        if (desc) desc.style.removeProperty('color');
        var icon = li.querySelector('[data-testid="choice-icon__library-choice-icon"]');
        if (icon) {
          icon.style.removeProperty('background-color');
          icon.style.removeProperty('border-color');
          icon.style.removeProperty('color');
        }
      }
    });
  }

  // Observe DOM changes to re-style links, re-inject and reposition search bar
  var _rafPending = false;
  function observeDOM() {
    var observer = new MutationObserver(function() {
      styleSideNavLinks();
      ensureSearchBar();
      ensureTitle();
      // Throttle repositioning and dark bg overrides to once per animation frame
      if (!_rafPending) {
        _rafPending = true;
        requestAnimationFrame(function() {
          repositionSearchBar();
          applyDarkModeBackgrounds();
          _rafPending = false;
        });
      }
    });
    observer.observe(document.body, { childList: true, subtree: true, attributes: true });
  }

  // Keep trying until elements stick (Vue may replace body content)
  var attempts = 0;
  var interval = setInterval(function() {
    ensureToggle();
    ensureSearchBar();
    attempts++;
    if (attempts > 50 || document.querySelector('.angels-theme-toggle')) {
      clearInterval(interval);
      observeDOM();
    }
  }, 200);
})();
