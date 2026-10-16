() => {
  document.body.classList.add('dark');  // Darkroom: always dark

  // Tabs: draw the "1 ·" prefix of each tab label in small mono (Gradio tab labels are plain text).
  const numberTabs = () => {
    document.querySelectorAll('.tab-wrapper button').forEach((b) => {
      if (b.querySelector('.n')) return;
      const m = b.textContent.match(/^\s*(\d+ ·|⚙)\s*(.*)$/);
      if (!m) return;
      b.textContent = '';
      const n = document.createElement('span');
      n.className = 'n';
      n.textContent = m[1];
      b.append(n, document.createTextNode(m[2]));
    });
  };
  new MutationObserver(numberTabs).observe(document.body, { childList: true, subtree: true });
  numberTabs();

  // Review shortcuts: only while the Review tab is visible and you're not typing in a field.
  const keys = { a: 'rv-approve', f: 'rv-fix', r: 'rv-redo', t: 'rv-touch', ArrowRight: 'rv-next', ArrowLeft: 'rv-prev' };
  document.addEventListener('keydown', (e) => {
    if (e.ctrlKey || e.altKey || e.metaKey) return;
    if (e.target.closest('input, textarea, select, [contenteditable="true"]')) return;
    const id = keys[e.key.length === 1 ? e.key.toLowerCase() : e.key];
    const panel = document.getElementById('review-panel');
    if (!id || !panel || panel.offsetParent === null) return;
    const btn = document.getElementById(id);
    if (btn && !btn.disabled) { e.preventDefault(); btn.click(); }
  });
}
