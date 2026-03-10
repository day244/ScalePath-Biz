/* ============================================================
   ScalePath.biz — Human Interactions
   Paste this at the bottom of your JS in Base44
   ============================================================ */

/* ── 1. TYPEWRITER EFFECT ───────────────────────────────────
   Cycles through value props in the hero heading
   ─────────────────────────────────────────────────────────── */
(function initTypewriter() {
  const target = document.querySelector('.gradient-text');
  if (!target) return;

  const phrases = [
    'predictable revenue',
    'qualified meetings',
    'faster deal cycles',
    'scalable pipeline',
    'real growth',
  ];

  let phraseIndex = 0;
  let charIndex   = 0;
  let isDeleting  = false;
  let isPaused    = false;

  function type() {
    const current = phrases[phraseIndex];

    if (isPaused) return;

    if (!isDeleting) {
      target.textContent = current.slice(0, charIndex + 1);
      charIndex++;
      if (charIndex === current.length) {
        isPaused = true;
        setTimeout(() => { isPaused = false; isDeleting = true; }, 2200);
      }
    } else {
      target.textContent = current.slice(0, charIndex - 1);
      charIndex--;
      if (charIndex === 0) {
        isDeleting = false;
        phraseIndex = (phraseIndex + 1) % phrases.length;
      }
    }

    setTimeout(type, isDeleting ? 45 : 90);
  }

  // Add blinking cursor style
  target.style.borderRight = '3px solid #60a5fa';
  target.style.paddingRight = '4px';
  setInterval(() => {
    target.style.borderRightColor =
      target.style.borderRightColor === 'transparent' ? '#60a5fa' : 'transparent';
  }, 530);

  setTimeout(type, 1200);
})();


/* ── 2. SOCIAL PROOF TOAST NOTIFICATIONS ───────────────────
   Shows "Alex from Chicago just booked a call" every 25–45s
   ─────────────────────────────────────────────────────────── */
(function initSocialProofToasts() {
  const proofs = [
    { name: 'Alex M.',     city: 'New York',      action: 'just booked a strategy call' },
    { name: 'Sarah K.',    city: 'San Francisco',  action: 'just requested a proposal'   },
    { name: 'James T.',    city: 'Austin',         action: 'just booked a strategy call' },
    { name: 'Rachel D.',   city: 'Chicago',        action: 'started a free trial'        },
    { name: 'Marcus L.',   city: 'London',         action: 'just booked a strategy call' },
    { name: 'Priya S.',    city: 'Toronto',        action: 'just requested a proposal'   },
    { name: 'Ben W.',      city: 'Seattle',        action: 'just booked a strategy call' },
    { name: 'Dana H.',     city: 'Boston',         action: 'just requested a proposal'   },
    { name: 'Carlos R.',   city: 'Miami',          action: 'just booked a strategy call' },
    { name: 'Emily F.',    city: 'Atlanta',        action: 'started a free trial'        },
  ];

  // Create container
  const container = document.createElement('div');
  container.id = 'sp-toast-container';
  document.body.appendChild(container);

  let idx = Math.floor(Math.random() * proofs.length);

  function showToast() {
    const p = proofs[idx % proofs.length];
    idx++;

    const toast = document.createElement('div');
    toast.className = 'sp-toast';
    toast.innerHTML = `
      <div class="sp-toast-avatar">${p.name.charAt(0)}</div>
      <div class="sp-toast-body">
        <strong>${p.name}</strong> from ${p.city}
        <span>${p.action}</span>
      </div>
      <button class="sp-toast-close" aria-label="Dismiss">×</button>
    `;

    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('sp-toast--in'));

    const dismiss = () => {
      toast.classList.remove('sp-toast--in');
      toast.classList.add('sp-toast--out');
      setTimeout(() => toast.remove(), 400);
    };

    toast.querySelector('.sp-toast-close').addEventListener('click', dismiss);
    setTimeout(dismiss, 5500);
  }

  // First toast after 8s, then every 30–48s
  setTimeout(() => {
    showToast();
    setInterval(showToast, Math.random() * 18000 + 30000);
  }, 8000);
})();


/* ── 3. FLOATING CHAT WIDGET ────────────────────────────────
   A "Talk to us" button in the corner with a quick message
   ─────────────────────────────────────────────────────────── */
(function initChatWidget() {
  const widget = document.createElement('div');
  widget.id = 'sp-chat';
  widget.innerHTML = `
    <button class="sp-chat-btn" id="spChatBtn" aria-label="Open chat">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
      </svg>
      <span class="sp-chat-label">Chat with us</span>
      <span class="sp-chat-badge">1</span>
    </button>
    <div class="sp-chat-panel" id="spChatPanel" hidden>
      <div class="sp-chat-header">
        <div class="sp-chat-avatar">SP</div>
        <div>
          <div class="sp-chat-name">ScalePath Team</div>
          <div class="sp-chat-status">
            <span class="sp-status-dot"></span> Online now
          </div>
        </div>
        <button class="sp-chat-x" id="spChatClose">×</button>
      </div>
      <div class="sp-chat-messages" id="spChatMessages">
        <div class="sp-msg sp-msg--agent">
          <div class="sp-msg-bubble">
            Hey 👋 Ready to scale your B2B pipeline? Book a free strategy call and we'll show you exactly how.
          </div>
          <div class="sp-msg-time">just now</div>
        </div>
      </div>
      <div class="sp-chat-input-row">
        <a href="#contact" class="sp-chat-cta" id="spChatCta">Book a Free Call →</a>
      </div>
    </div>
  `;
  document.body.appendChild(widget);

  const btn   = document.getElementById('spChatBtn');
  const panel = document.getElementById('spChatPanel');
  const close = document.getElementById('spChatClose');
  const badge = btn.querySelector('.sp-chat-badge');
  const cta   = document.getElementById('spChatCta');

  function openPanel() {
    panel.hidden = false;
    panel.classList.add('sp-chat-panel--in');
    badge.style.display = 'none';
    btn.querySelector('.sp-chat-label').textContent = 'Chat with us';

    // Simulate a follow-up message after 4s
    setTimeout(() => {
      const messages = document.getElementById('spChatMessages');
      if (!messages) return;
      const msg = document.createElement('div');
      msg.className = 'sp-msg sp-msg--agent';
      msg.innerHTML = `
        <div class="sp-msg-bubble">Most clients see their first booked meeting within 3–4 weeks. Want to see how?</div>
        <div class="sp-msg-time">just now</div>
      `;
      messages.appendChild(msg);
      messages.scrollTop = messages.scrollHeight;
    }, 4000);
  }

  function closePanel() {
    panel.classList.remove('sp-chat-panel--in');
    setTimeout(() => { panel.hidden = true; }, 280);
  }

  btn.addEventListener('click', () => panel.hidden ? openPanel() : closePanel());
  close.addEventListener('click', closePanel);

  cta.addEventListener('click', () => {
    closePanel();
    const contact = document.getElementById('contact');
    if (contact) {
      setTimeout(() => contact.scrollIntoView({ behavior: 'smooth', block: 'start' }), 300);
    }
  });

  // Show badge pulse after 6s
  setTimeout(() => {
    badge.style.display = 'flex';
    btn.classList.add('sp-chat-btn--pulse');
  }, 6000);
})();


/* ── 4. STICKY SCROLL CTA BAR ───────────────────────────────
   Appears at bottom after user scrolls past the hero
   ─────────────────────────────────────────────────────────── */
(function initStickyBar() {
  const bar = document.createElement('div');
  bar.id = 'sp-sticky-bar';
  bar.innerHTML = `
    <div class="sp-sticky-inner">
      <div class="sp-sticky-text">
        <strong>Ready to scale?</strong>
        <span>Book your free 30-min strategy call — no commitment.</span>
      </div>
      <a href="#contact" class="sp-sticky-btn">Book a Free Call →</a>
      <button class="sp-sticky-close" id="spStickyClose" aria-label="Dismiss">×</button>
    </div>
  `;
  document.body.appendChild(bar);

  const close = document.getElementById('spStickyClose');
  let dismissed = false;

  window.addEventListener('scroll', () => {
    if (dismissed) return;
    const heroHeight = document.querySelector('.hero')?.offsetHeight || 600;
    if (window.scrollY > heroHeight * 0.8) {
      bar.classList.add('sp-sticky-bar--in');
    } else {
      bar.classList.remove('sp-sticky-bar--in');
    }
  }, { passive: true });

  close.addEventListener('click', () => {
    dismissed = true;
    bar.classList.remove('sp-sticky-bar--in');
  });
})();


/* ── 5. CARD TILT ON HOVER ──────────────────────────────────
   Subtle 3-D perspective tilt on service & testimonial cards
   ─────────────────────────────────────────────────────────── */
(function initCardTilt() {
  const cards = document.querySelectorAll('.service-card, .testimonial-card, .result-num-card');

  cards.forEach(card => {
    card.addEventListener('mousemove', e => {
      const rect   = card.getBoundingClientRect();
      const x      = e.clientX - rect.left;
      const y      = e.clientY - rect.top;
      const cx     = rect.width  / 2;
      const cy     = rect.height / 2;
      const rotateX = ((y - cy) / cy) * -6;
      const rotateY = ((x - cx) / cx) *  6;
      card.style.transform = `perspective(900px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
    });

    card.addEventListener('mouseleave', () => {
      card.style.transform = '';
      card.style.transition = 'transform 0.4s ease';
    });

    card.addEventListener('mouseenter', () => {
      card.style.transition = 'transform 0.1s ease';
    });
  });
})();


/* ── 6. EXIT INTENT POPUP ───────────────────────────────────
   When the user's cursor moves to leave the page, show a popup
   ─────────────────────────────────────────────────────────── */
(function initExitIntent() {
  let shown = false;

  const overlay = document.createElement('div');
  overlay.id = 'sp-exit-overlay';
  overlay.innerHTML = `
    <div class="sp-exit-modal">
      <button class="sp-exit-close" id="spExitClose">×</button>
      <div class="sp-exit-emoji">🚀</div>
      <h2>Wait — before you go!</h2>
      <p>Get our <strong>free B2B Pipeline Checklist</strong> — 23 proven tactics our top clients use to book 3× more meetings.</p>
      <form class="sp-exit-form" id="spExitForm">
        <input type="email" placeholder="your@work-email.com" required />
        <button type="submit">Send Me the Checklist →</button>
      </form>
      <p class="sp-exit-fine">No spam. Unsubscribe anytime.</p>
    </div>
  `;
  document.body.appendChild(overlay);

  function show() {
    if (shown) return;
    shown = true;
    overlay.classList.add('sp-exit-overlay--in');
    document.body.style.overflow = 'hidden';
  }

  function hide() {
    overlay.classList.remove('sp-exit-overlay--in');
    document.body.style.overflow = '';
  }

  document.addEventListener('mouseleave', e => {
    if (e.clientY <= 0) show();
  });

  document.getElementById('spExitClose').addEventListener('click', hide);
  overlay.addEventListener('click', e => { if (e.target === overlay) hide(); });

  document.getElementById('spExitForm').addEventListener('submit', e => {
    e.preventDefault();
    const modal = overlay.querySelector('.sp-exit-modal');
    modal.innerHTML = `
      <div class="sp-exit-success">
        <div class="sp-exit-check">✓</div>
        <h2>Check your inbox!</h2>
        <p>Your B2B Pipeline Checklist is on its way. Talk soon 👋</p>
      </div>
    `;
    setTimeout(hide, 2800);
  });

  // Keyboard escape
  document.addEventListener('keydown', e => { if (e.key === 'Escape') hide(); });
})();


/* ── 7. LIVE VISITOR COUNT ──────────────────────────────────
   Shows a subtle "X people viewing this page" indicator
   ─────────────────────────────────────────────────────────── */
(function initViewerCount() {
  // Randomise between 8–23 and drift slowly
  let count = Math.floor(Math.random() * 16) + 8;

  const pill = document.createElement('div');
  pill.id = 'sp-viewers';
  pill.innerHTML = `<span class="sp-viewers-dot"></span> <span id="spViewerNum">${count}</span> people viewing this page`;
  document.querySelector('.hero-inner')?.appendChild(pill);

  setInterval(() => {
    const delta = Math.random() < 0.5 ? -1 : 1;
    count = Math.max(6, Math.min(30, count + delta));
    const num = document.getElementById('spViewerNum');
    if (num) num.textContent = count;
  }, 7000);
})();
