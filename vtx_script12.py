import re
with open("app/static/app.js", "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

NEW_INIT_LANDING_PAGE = """function initLandingPage() {
    const landing = document.getElementById('medi-guard-landing');
    const canvas = document.getElementById('vfx-canvas');
    if (!canvas || !landing) return;

    const ctx = canvas.getContext('2d');
    let W, H;
    
    // --- PHOTOREALISTIC STORYBOARD ASSETS ---
    var imgF1 = new Image(); imgF1.src = '/static/frame1.png';
    var imgF2 = new Image(); imgF2.src = '/static/frame2.png';
    var imgF3 = new Image(); imgF3.src = '/static/frame3.png';
    
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

    const T_F1_START = 0;
    const T_F2_START = 2000;
    const T_F3_START = 4000; // Patient has card
    const T_ZOOM_START = 4500; // Wait 0.5s THEN zoom
    const T_ENERGY_BUILD = 4500;
    const T_FLASH = 8000;
    const T_LOGO_REVEAL = 8200;
    const T_EXIT = 14000;
    
    var t0, raf, exited = false;

    function playCinematicAudio() {
        try {
            var ac = new (window.AudioContext || window.webkitAudioContext)();
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
        frame();
    }
    
    function drawCinematicImage(img) {
        if (!img.complete || img.naturalWidth === 0) return;
        var drawW, drawH;
        var imgRatio = img.naturalWidth / img.naturalHeight;
        var canvasRatio = W / H;
        if (canvasRatio > imgRatio) { drawW = W; drawH = W / imgRatio; } 
        else { drawH = H; drawW = H * imgRatio; }
        ctx.drawImage(img, W/2 - drawW/2, H/2 - drawH/2, drawW, drawH);
    }

    function frame() {
        raf = requestAnimationFrame(frame);
        var dt = performance.now() - t0;
        
        ctx.fillStyle = '#000'; ctx.fillRect(0,0,W,H); 
        
        if (dt < T_FLASH + 500) {
            
            // CAMERA ZOOM LOGIC (Stays totally flat until after the handoff!)
            var camZoom = 1.0;
            if (dt > T_ZOOM_START) {
                var zoomProgress = Math.min((dt - T_ZOOM_START) / (T_FLASH - T_ZOOM_START), 1.0);
                var zEase = zoomProgress * zoomProgress * zoomProgress; // Exponential acceleration into the card
                camZoom = 1.0 + (zEase * 6.0); // 600% zoom directly into the center
            }
            
            ctx.save();
            ctx.translate(W/2, H/2);
            ctx.scale(camZoom, camZoom);
            ctx.translate(-W/2, -H/2);
            
            // FRAME 1: DOCTOR REACHING INTO POCKET
            if (dt < T_F2_START + 500) {
                var f1Alpha = Math.min(dt/500, 1.0);
                if (dt > T_F2_START) f1Alpha = 1.0 - ((dt - T_F2_START)/500); 
                ctx.save(); ctx.globalAlpha = Math.max(0, f1Alpha); drawCinematicImage(imgF1); ctx.restore();
            }
            
            // FRAME 2: DOCTOR EXTENDING GLOWING CARD
            if (dt > T_F2_START && dt < T_F3_START + 500) {
                var f2Alpha = Math.min((dt - T_F2_START)/500, 1.0);
                if (dt > T_F3_START) f2Alpha = 1.0 - ((dt - T_F3_START)/500);
                ctx.save(); ctx.globalAlpha = Math.max(0, f2Alpha); drawCinematicImage(imgF2); ctx.restore();
            }
            
            // FRAME 3: PATIENT GRABBING CARD
            if (dt > T_F3_START) {
                var f3Alpha = Math.min((dt - T_F3_START)/500, 1.0);
                ctx.save(); ctx.globalAlpha = Math.max(0, f3Alpha); drawCinematicImage(imgF3); ctx.restore();
                
                // Vignette
                var vigAlpha = Math.min((dt - T_F3_START)/2000, 0.7);
                var grad = ctx.createRadialGradient(W/2, H/2, 0, W/2, H/2, W);
                grad.addColorStop(0, 'rgba(0,0,0,0)'); grad.addColorStop(1, `rgba(0,0,0,${vigAlpha})`);
                ctx.fillStyle = grad; ctx.fillRect(0,0,W,H);
                
                // ENERGY BUILD UP SWARM AROUND HAND
                if (dt > T_ENERGY_BUILD) {
                    var nAlpha = Math.min((dt - T_ENERGY_BUILD)/1000, 1.0);
                    ctx.save();
                    ctx.globalCompositeOperation = 'lighter';
                    ctx.fillStyle = `rgba(0, 240, 255, ${nAlpha * 0.9})`;
                    var zoomPower = Math.pow(((dt - T_ENERGY_BUILD)/(T_FLASH - T_ENERGY_BUILD)), 2); 
                    for(let i=0; i<particles.length; i++) {
                        let particle = particles[i];
                        particle.theta += particle.speed;
                        particle.r -= (zoomPower * 30 + 1); 
                        if(particle.r < 0) particle.r = Math.max(W/camZoom, H/camZoom);
                        let px = W/2 + Math.cos(particle.theta)*particle.r;
                        let py = H/2 + Math.sin(particle.theta)*particle.r;
                        ctx.beginPath(); ctx.arc(px, py, particle.size / camZoom, 0, Math.PI*2); ctx.fill();
                    }
                    ctx.restore();
                }
            }
            ctx.restore(); // POP CAMERA ZOOM
        }
        
        // --- SCENE FLASH ACCELERATION ---
        var flashAlpha = 0;
        if (dt >= T_FLASH && dt < T_LOGO_REVEAL + 1200) {
            flashAlpha = 1.0 - ((dt - T_FLASH) / 1200);
            if(flashAlpha < 0) flashAlpha = 0;
            ctx.fillStyle = `rgba(255, 255, 255, ${flashAlpha})`;
            ctx.fillRect(0,0,W,H);
        }

        // --- SOLID LOGO REVEAL & TAGLINE ---
        if (dt >= T_LOGO_REVEAL) {
            var logoAlpha = Math.min((dt - T_LOGO_REVEAL) / 300, 1.0);
            
            if (dt > T_EXIT - 1000) logoAlpha = 1.0 - ((dt - (T_EXIT-1000))/1000); 
            if (logoAlpha < 0) logoAlpha = 0;

            var bgGrad = ctx.createRadialGradient(W/2, H/2, 0, W/2, H/2, W);
            bgGrad.addColorStop(0, `rgba(4, 30, 60, ${logoAlpha})`); 
            bgGrad.addColorStop(0.5, `rgba(1, 5, 10, ${logoAlpha})`); 
            bgGrad.addColorStop(1, `rgba(0, 0, 0, ${logoAlpha})`); 
            ctx.fillStyle = bgGrad; ctx.fillRect(0,0,W,H);
            
            var scale = 1.0 + ((dt - T_LOGO_REVEAL) / (T_EXIT - T_LOGO_REVEAL)) * 0.15;
            ctx.save();
            ctx.globalAlpha = logoAlpha;
            ctx.translate(W/2, H/2); ctx.scale(scale, scale); ctx.translate(-W/2, -H/2);
            
            const fs = Math.min(W / 6, 200);
            ctx.font = '900 ' + fs + 'px Outfit, Arial Black, sans-serif';
            ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            
            ctx.shadowColor = '#00F0FF'; ctx.shadowBlur = 60 * logoAlpha;
            
            var textG = ctx.createLinearGradient(0, H/2-fs, 0, H/2+fs);
            textG.addColorStop(0, '#FFFFFF'); 
            textG.addColorStop(0.3, '#00F0FF'); 
            textG.addColorStop(1, '#003080');
            ctx.fillStyle = textG; 
            ctx.fillText('MEDI-GUARD', W/2, H/2 - 40);
            
            ctx.shadowBlur = 0;
            ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(255,255,255,0.6)';
            ctx.strokeText('MEDI-GUARD', W/2, H/2 - 40);
            
            if (dt > T_LOGO_REVEAL + 1500) {
                var tagAlpha = Math.min((dt - (T_LOGO_REVEAL + 1500)) / 1000, 1.0);
                if (dt > T_EXIT - 1000) tagAlpha = logoAlpha; 
                ctx.globalAlpha = Math.min(tagAlpha, logoAlpha);
                
                ctx.font = '300 ' + (fs * 0.22) + 'px Outfit, Arial, sans-serif';
                ctx.fillStyle = '#E0F0FF';
                if (ctx.letterSpacing !== undefined) ctx.letterSpacing = "8px";
                ctx.fillText('Denial-Proof Your Medical Decisions', W/2, H/2 + fs*0.65);
            }
            ctx.restore();
            
            if (flashAlpha > 0) {
                ctx.fillStyle = `rgba(255, 255, 255, ${flashAlpha})`; ctx.fillRect(0,0,W,H);
            }
        }
        
        // --- AUTO DASHBOARD REDIRECT ---
        if (dt >= T_EXIT && !exited) {
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
