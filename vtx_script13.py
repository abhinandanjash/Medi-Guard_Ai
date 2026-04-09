import re
with open("app/static/app.js", "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

NEW_INIT_LANDING_PAGE = """function initLandingPage() {
    const landing = document.getElementById('medi-guard-landing');
    const canvas = document.getElementById('vfx-canvas');
    var video = document.getElementById('vfx-video');
    if (!canvas || !landing || !video) return;

    const ctx = canvas.getContext('2d');
    let W, H;
    
    function resize() {
        const dpr = window.devicePixelRatio || 1;
        W = window.innerWidth;
        H = window.innerHeight;
        canvas.width = W * dpr;
        canvas.height = H * dpr;
        ctx.scale(dpr, dpr);
        canvas.style.width = W + 'px';
        canvas.style.height = H + 'px';
    }
    resize();
    window.addEventListener('resize', resize);
    
    var pCount = 300;
    var particles = [];
    for(let i=0; i<pCount; i++) {
        particles.push({
            x: Math.random() * W, y: Math.random() * H,
            r: Math.random() * (Math.max(W,H)),
            theta: Math.random() * Math.PI * 2,
            speed: 0.005 + Math.random()*0.02,
            size: 1 + Math.random()*3
        });
    }

    var t0, raf, exited = false;

    function playCinematicAudio() {
        try {
            var ac = new (window.AudioContext || window.webkitAudioContext)();
            ac.resume();
            var master = ac.createGain(); 
            master.gain.value = 0.9; 
            master.connect(ac.destination);
            
            var amb = ac.createOscillator(); amb.type = 'sine'; amb.frequency.value = 60;
            var ambG = ac.createGain(); ambG.gain.value = 0;
            ambG.gain.linearRampToValueAtTime(0.5, ac.currentTime + 1.0);
            ambG.gain.linearRampToValueAtTime(0, ac.currentTime + 7.9);
            amb.connect(ambG).connect(master);
            amb.start(ac.currentTime);
            
            var cardT = ac.createOscillator(); cardT.type = 'triangle'; cardT.frequency.value = 440;
            var cardG = ac.createGain(); cardG.gain.value = 0;
            cardG.gain.setValueAtTime(0, ac.currentTime + 2.5);
            cardG.gain.linearRampToValueAtTime(0.2, ac.currentTime + 3.5);
            cardG.gain.exponentialRampToValueAtTime(0.01, ac.currentTime + 8.0);
            cardT.connect(cardG).connect(master);
            cardT.start(ac.currentTime + 2.5);

            [55, 110, 220].forEach(f => {
                var osc = ac.createOscillator(); osc.type = 'sawtooth';
                var rG = ac.createGain();
                rG.gain.setValueAtTime(0.001, ac.currentTime + 4.0);
                rG.gain.exponentialRampToValueAtTime(0.4, ac.currentTime + 7.95);
                rG.gain.linearRampToValueAtTime(0, ac.currentTime + 8.0);
                osc.frequency.setValueAtTime(f/2, ac.currentTime + 4.0);
                osc.frequency.exponentialRampToValueAtTime(f*3.5, ac.currentTime + 7.95);
                osc.connect(rG).connect(master);
                osc.start(ac.currentTime + 4.0);
            });

            var snap = ac.createOscillator(); snap.type = 'square';
            snap.frequency.setValueAtTime(4000, ac.currentTime + 8.0);
            snap.frequency.exponentialRampToValueAtTime(100, ac.currentTime + 8.1);
            var snapG = ac.createGain(); snapG.gain.setValueAtTime(0, ac.currentTime + 7.9);
            snapG.gain.setValueAtTime(1.0, ac.currentTime + 8.0);
            snapG.gain.exponentialRampToValueAtTime(0.01, ac.currentTime + 8.5);
            snap.connect(snapG).connect(master);
            snap.start(ac.currentTime + 8.0);
            
            var sub = ac.createOscillator(); sub.type = 'sine'; sub.frequency.setValueAtTime(120, ac.currentTime+8.0);
            sub.frequency.exponentialRampToValueAtTime(20, ac.currentTime+10.0);
            var subG = ac.createGain(); subG.gain.setValueAtTime(0, ac.currentTime+7.9);
            subG.gain.setValueAtTime(1.5, ac.currentTime+8.0);
            subG.gain.exponentialRampToValueAtTime(0.01, ac.currentTime+12.0);
            sub.connect(subG).connect(master);
            sub.start(ac.currentTime+8.0);

        } catch(e) {}
    }

    const startOverlay = document.getElementById('init-overlay');
    const startBtn = document.getElementById('vfx-start-btn');
    if (!startOverlay || !startBtn) runSequence();
    else {
        startBtn.addEventListener('click', function() {
            startOverlay.style.opacity = '0';
            setTimeout(() => startOverlay.remove(), 800);
            runSequence();
        });
    }

    function runSequence() {
        t0 = performance.now();
        playCinematicAudio();
        
        var bgm = document.getElementById('ambient-sound');
        if (bgm) { bgm.volume = 0.5; bgm.play().catch(e => console.log('BGM blocked:', e)); }
        
        // --- 🔴 START THE NATIVE MP4 ENGINE ---
        video.currentTime = 0;
        video.play().catch(e => console.log('Video play failed:', e));
        
        frame();
    }

    function frame() {
        raf = requestAnimationFrame(frame);
        var dt = performance.now() - t0;
        
        ctx.fillStyle = '#000'; ctx.fillRect(0,0,W,H); 
        
        // Time parameters dynamically bound to the video file length
        var tVidSec = video.currentTime;
        var durSec = video.duration || 10; 
        
        // 1. RENDER MP4 RAW FRAMES TO CANVAS AT 60FPS
        if (video.readyState >= 2 && !video.ended) {
            var drawW, drawH;
            var vidRatio = video.videoWidth / video.videoHeight;
            var canvasRatio = W / H;
            if (canvasRatio > vidRatio) { drawW = W; drawH = W / vidRatio; } 
            else { drawH = H; drawW = H * vidRatio; }
            ctx.drawImage(video, W/2 - drawW/2, H/2 - drawH/2, drawW, drawH);
        }

        // 2. VIGNETTE OVER VIDEO
        if (tVidSec > 0.5) {
            var vigAlpha = Math.min((tVidSec - 0.5)/2.0, 0.7);
            var grad = ctx.createRadialGradient(W/2, H/2, 0, W/2, H/2, W);
            grad.addColorStop(0, 'rgba(0,0,0,0)'); grad.addColorStop(1, `rgba(0,0,0,${vigAlpha})`);
            ctx.fillStyle = grad; ctx.fillRect(0,0,W,H);
        }

        // 3. VFX ENERGY BUILD TARGETING THE CLIMAX (Last 2 seconds of video)
        if (tVidSec > durSec - 2.0 && tVidSec < durSec) {
            var nAlpha = Math.min((tVidSec - (durSec - 2.0))/1.0, 1.0);
            ctx.save();
            ctx.globalCompositeOperation = 'lighter';
            ctx.fillStyle = `rgba(0, 240, 255, ${nAlpha * 0.9})`;
            var zoomPower = Math.pow(((tVidSec - (durSec - 2.0))/2.0), 2); 
            for(let i=0; i<particles.length; i++) {
                let particle = particles[i];
                particle.theta += particle.speed;
                particle.r -= (zoomPower * 40 + 2); 
                if(particle.r < 0) particle.r = Math.max(W, H);
                let px = W/2 + Math.cos(particle.theta)*particle.r;
                let py = H/2 + Math.sin(particle.theta)*particle.r;
                ctx.beginPath(); ctx.arc(px, py, particle.size, 0, Math.PI*2); ctx.fill();
            }
            ctx.restore();
        }
        
        // --- SCENE FLASH & LOGO REVEAL AT END OF VIDEO ---
        var tEndDelta = (dt/1000) - durSec; 
        if (tEndDelta > 0 && tEndDelta < 3.0) {
            
            // White Flash
            var flashAlpha = 1.0 - (tEndDelta / 1.0);
            if(flashAlpha < 0) flashAlpha = 0;
            if(flashAlpha > 0) {
                ctx.fillStyle = `rgba(255, 255, 255, ${flashAlpha})`;
                ctx.fillRect(0,0,W,H);
            }

            // Dark space background fade in
            var logoAlpha = Math.min(tEndDelta / 0.5, 1.0);
            var bgGrad = ctx.createRadialGradient(W/2, H/2, 0, W/2, H/2, W);
            bgGrad.addColorStop(0, `rgba(4, 30, 60, ${logoAlpha})`); 
            bgGrad.addColorStop(0.5, `rgba(1, 5, 10, ${logoAlpha})`); 
            bgGrad.addColorStop(1, `rgba(0, 0, 0, ${logoAlpha})`); 
            ctx.fillStyle = bgGrad; ctx.fillRect(0,0,W,H);
            
            // Holographic MEDI-GUARD text
            var fs = Math.min(W / 6, 200);
            ctx.fillStyle = `rgba(255,255,255, ${logoAlpha})`;
            ctx.font = '900 ' + fs + 'px Outfit, Arial Black, sans-serif';
            ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            ctx.shadowColor = '#00F0FF'; ctx.shadowBlur = 40 * logoAlpha;
            ctx.fillText('MEDI-GUARD', W/2, H/2 - 40);
        }
        
        // --- AUTO DASHBOARD REDIRECT ---
        // Redirect completely 4 seconds after the video stops playing
        if (tEndDelta > 4.0 && !exited) {
            exited = true;
            window.location.href = '/dashboard';
        }
    }
}"""

start_idx = content.find("function initLandingPage() {")
end_idx = content.find("function initParticles() {")

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + NEW_INIT_LANDING_PAGE + "\n" + content[end_idx:]
    with open("app/static/app.js", "w", encoding="utf-8") as f:
        f.write(content)
    print("Success")
else:
    print("Could not find boundaries")
