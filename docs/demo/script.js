(function () {
  var themeBtn = document.getElementById('themeToggle');
  var themeIcon = document.getElementById('themeIcon');
  var themeText = document.getElementById('themeText');

  function updateThemeUI(theme) {
    if (themeIcon && themeText) {
      if (theme === 'dark') {
        themeIcon.textContent = '🌙';
        themeText.textContent = 'Dark';
      } else {
        themeIcon.textContent = '☀️';
        themeText.textContent = 'Light';
      }
    }
  }

  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      var cur = document.documentElement.getAttribute('data-theme') || 'light';
      var next = cur === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('acri_theme', next);
      updateThemeUI(next);
    });

    var saved = localStorage.getItem('acri_theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    updateThemeUI(saved);
  }

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { if (e.isIntersecting) e.target.classList.add('in'); });
  }, { threshold: 0.15 });
  document.querySelectorAll('.reveal').forEach(function (el) { io.observe(el); });

  var wall = document.getElementById('schemaWall');
  var hotIdx = new Set([4, 11, 19, 23, 34, 41, 52, 58, 63, 71, 77, 84, 91]);
  for (var i = 0; i < 100; i++) {
    var s = document.createElement('span');
    if (hotIdx.has(i)) s.className = 'hot';
    wall.appendChild(s);
  }

  document.querySelectorAll('.studio-tabs button').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.studio-tabs button').forEach(function (b) { b.setAttribute('aria-selected', 'false'); });
      document.querySelectorAll('.panel').forEach(function (p) { p.classList.remove('active'); });
      btn.setAttribute('aria-selected', 'true');
      document.getElementById('panel-' + btn.dataset.panel).classList.add('active');
    });
  });

  var nodes = [
    ['corpus', false], ['compass', false], ['port · gemini', false], ['port · openai-compat', false],
    ['ledger', false], ['gate', false], ['press', false], ['sandbox', false], ['router', false],
    ['github_*  (6 tools)', false], ['stripe_*  (4 tools)', false], ['postgres_*  (5 tools)', false],
    ['gemini-2.5-flash', true]
  ];
  var mesh = document.getElementById('meshNodes');
  nodes.forEach(function (n) {
    var d = document.createElement('div');
    d.className = 'node' + (n[1] ? ' model' : '');
    d.textContent = n[0];
    mesh.appendChild(d);
  });

  var sampleQueries = [
    ['merge pull request #42 into main', 'github_merge_pull_request', 5],
    ['refund the last charge for cus_18a', 'stripe_create_refund', 5],
    ['scale the api deployment to 6 replicas', 'kubernetes_scale_deployment', 5],
    ['what is the current balance on invoice 881', 'stripe_get_invoice', 3],
    ['resize db.instance to db.r6g.large', 'aws_ec2_resize_instance', 5],
    ['who commented on ticket ZD-991 last', 'zendesk_get_ticket_comments', 4]
  ];
  var feed = document.getElementById('ledgerFeed');
  var qi = 0;
  function pushRow() {
    var q = sampleQueries[qi % sampleQueries.length];
    qi++;
    var row = document.createElement('div');
    row.className = 'ledger-row';
    var t = new Date();
    var ts = String(t.getHours()).padStart(2, '0') + ':' + String(t.getMinutes()).padStart(2, '0') + ':' + String(t.getSeconds()).padStart(2, '0');
    row.innerHTML = '<span class="t">' + ts + '</span><span class="q">' + q[0] + ' → ' + q[1] + '</span><span class="k">k=' + q[2] + '</span>';
    feed.insertBefore(row, feed.firstChild);
    while (feed.children.length > 6) feed.removeChild(feed.lastChild);
  }
  pushRow();
  if (!reduceMotion) setInterval(pushRow, 2600);

  var canvas = document.getElementById('resolveCanvas');
  var ctx = canvas.getContext('2d');
  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  var W, H, pts = [];
  var styleSignal, styleLine;

  function readTokens() {
    var cs = getComputedStyle(document.documentElement);
    styleSignal = cs.getPropertyValue('--signal').trim();
    styleLine = cs.getPropertyValue('--line').trim();
  }

  function layout() {
    var rect = canvas.getBoundingClientRect();
    W = rect.width; H = rect.height;
    canvas.width = W * dpr; canvas.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    pts = [];
    var cols = 20, rows = 5;
    var padX = 40, padY = 40;
    var gx = (W - padX * 2) / (cols - 1), gy = (H - padY * 2) / (rows - 1);
    var n = 0;
    for (var r = 0; r < rows; r++) {
      for (var c = 0; c < cols; c++) {
        n++;
        pts.push({
          x: padX + c * gx + (Math.random() - 0.5) * 6,
          y: padY + r * gy + (Math.random() - 0.5) * 6,
          hit: n <= 100 && [12, 27, 41, 58, 73].includes(n)
        });
      }
    }
  }

  readTokens();
  layout();
  window.addEventListener('resize', layout);

  var start = null;
  var CYCLE = 5200;

  function frame(ts) {
    if (start === null) start = ts;
    var t = ((ts - start) % CYCLE) / CYCLE;
    ctx.clearRect(0, 0, W, H);
    var sweepX = t * W;

    pts.forEach(function (p) {
      var revealed = p.x <= sweepX + 4;
      var isHit = p.hit && revealed && t > 0.08;
      var r = isHit ? 5 : 2.6;
      ctx.beginPath();
      ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
      ctx.fillStyle = isHit ? styleSignal : styleLine;
      ctx.fill();
      if (isHit) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, r + 5, 0, Math.PI * 2);
        ctx.strokeStyle = styleSignal;
        ctx.globalAlpha = 0.35;
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.globalAlpha = 1;
      }
    });

    if (t < 0.75) {
      ctx.beginPath();
      ctx.moveTo(sweepX, 0);
      ctx.lineTo(sweepX, H);
      ctx.strokeStyle = styleSignal;
      ctx.globalAlpha = 0.45;
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    if (!reduceMotion) requestAnimationFrame(frame);
  }

  if (reduceMotion) {
    start = 0;
    frame(CYCLE * 0.9);
  } else {
    requestAnimationFrame(frame);
  }
})();
