import re
with open("app/static/app.js", "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

NEW_INIT_LANDING_PAGE = """function initLandingPage() {
    const landing = document.getElementById('medi-guard-landing');
    const canvas = document.getElementById('vfx-canvas');
    if (!canvas || !landing) return;

    const ctx = canvas.getContext('2d');
    let W, H;
    
    // --- 2.5D CINEMATIC MOVIE ASSETS ---
    var imgHospital = new Image(); imgHospital.src = '/static/scene_hospital.png';
    var imgCard = new Image(); imgCard.src = '/static/scene_card.png';
    
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
    
    // Tiny energy particles
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

    // DIRECTOR TIMELINE (Milliseconds)
    const T_HOSPITAL_FADE = 500;
    const T_CARD_FADEIN = 3500;
    const T_ENERGY_BUILD = 5500;
    const T_FLASH = 8000;
    const T_LOGO_REVEAL = 8200;
    const T_EXIT = 14000;
    
    var t0, raf, exited = false;

    // --- DOLBY CINEMATIC AUDIO ROUTING ---
    function playCinematicAudio() {
        try {
            var ac = new (window.AudioContext || window.webkitAudioContext)();
            var master = ac.createGain(); 
            master.gain.value = 0.9; 
            master.connect(ac.destination);
            
            // 1. Ambient Hum (0s - 8s)
            var amb = ac.createOscillator(); amb.type = 'sine'; amb.frequency.value = 60;
            var ambG = ac.createGain(); ambG.gain.value = 0;
            ambG.gain.linearRampToValueAtTime(0.5, ac.currentTime + 1.0);
            ambG.gain.linearRampToValueAtTime(0, ac.currentTime + 7.9);
            amb.connect(ambG).connect(master);
            amb.start(ac.currentTime);
            
            // 2. Card Tone (at 3.5s)
            var cardT = ac.createOscillator(); cardT.type = 'triangle'; cardT.frequency.value = 440;
            var cardG = ac.createGain(); cardG.gain.value = 0;
            cardG.gain.setValueAtTime(0, ac.currentTime + 3.4);
            cardG.gain.linearRampToValueAtTime(0.2, ac.currentTime + 4.5);
            cardG.gain.exponentialRampToValueAtTime(0.01, ac.currentTime + 8.0);
            cardT.connect(cardG).connect(master);
            cardT.start(ac.currentTime + 3.4);

            // 3. Hans Zimmer Riser (5.5s - 8s)
            [55, 110, 220].forEach(f => {
                var osc = ac.createOscillator(); osc.type = 'sawtooth';
                var rG = ac.createGain();
                rG.gain.setValueAtTime(0.001, ac.currentTime + 5.4);
                rG.gain.exponentialRampToValueAtTime(0.4, ac.currentTime + 7.95);
                rG.gain.linearRampToValueAtTime(0, ac.currentTime + 8.0);
                osc.frequency.setValueAtTime(f/2, ac.currentTime + 5.5);
                osc.frequency.exponentialRampToValueAtTime(f*2.5, ac.currentTime + 7.95);
                osc.connect(rG).connect(master);
                osc.start(ac.currentTime + 5.5);
            });

            // 4. Epic Impact Flash (8s)
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
    
    function drawCinematicImage(img, alpha, scaleMultiplier) {
        if (!img.complete || img.naturalWidth === 0) return;
        var drawW, drawH;
        var imgRatio = img.naturalWidth / img.naturalHeight;
        var canvasRatio = W / H;
        if (canvasRatio > imgRatio) {
            drawW = W; drawH = W / imgRatio;
        } else {
            drawH = H; drawW = H * imgRatio;
        }
        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.translate(W/2, H/2);
        ctx.scale(scaleMultiplier, scaleMultiplier);
        ctx.drawImage(img, -drawW/2, -drawH/2, drawW, drawH);
        ctx.restore();
    }

    function frame() {
        raf = requestAnimationFrame(frame);
        var dt = performance.now() - t0;
        
        ctx.fillStyle = '#000'; ctx.fillRect(0,0,W,H); 
        
        // --- PRE-FLASH SCENES ---
        if (dt < T_FLASH + 500) {
            // SCENE 1: HOSPITAL (Fades in, then fades out as card appears)
            var hospAlpha = Math.min(dt/T_HOSPITAL_FADE, 1.0);
            if (dt > T_CARD_FADEIN) hospAlpha = 1.0 - Math.min((dt - T_CARD_FADEIN)/1500, 1.0);
            if (hospAlpha < 0) hospAlpha = 0;
            var hospZoom = 1.0 + (dt / T_FLASH) * 0.15; // physical dolly forward
            drawCinematicImage(imgHospital, hospAlpha, hospZoom);
            
            // SCENE 2: CARD CLOSEUP (Crossfades in over hospital)
            if (dt > T_CARD_FADEIN) {
                var cardAlpha = Math.min((dt - T_CARD_FADEIN)/1500, 1.0);
                var cardZoom = 1.05 + ((dt - T_CARD_FADEIN) / T_FLASH) * 0.10; // secondary zoom
                drawCinematicImage(imgCard, cardAlpha, cardZoom);
                
                // Overlay Vignette (Background darkens slightly)
                var vigAlpha = Math.min((dt - T_CARD_FADEIN)/2000, 0.6);
                var grad = ctx.createRadialGradient(W/2, H/2, 0, W/2, H/2, W);
                grad.addColorStop(0, 'rgba(0,0,0,0)'); grad.addColorStop(1, `rgba(0,0,0,${vigAlpha})`);
                ctx.fillStyle = grad; ctx.fillRect(0,0,W,H);
                
                // SCENE 3: ENERGY BUILD UP
                if (dt > T_ENERGY_BUILD) {
                    var nAlpha = Math.min((dt - T_ENERGY_BUILD)/1000, 1.0);
                    ctx.save();
                    ctx.globalCompositeOperation = 'lighter';
                    ctx.fillStyle = `rgba(0, 240, 255, ${nAlpha * 0.9})`;
                    
                    // Acceleration curve for energy suction
                    var zoomPower = Math.pow(((dt - T_ENERGY_BUILD)/(T_FLASH - T_ENERGY_BUILD)), 2); 
                    
                    for(let i=0; i<particles.length; i++) {
                        let p = particles[i];
                        p.theta += p.speed;
                        p.r -= (zoomPower * 30 + 1); // Suck inwards faster and faster
                        if(p.r < 0) p.r = Math.max(W, H);
                        let px = W/2 + Math.cos(p.theta)*p.r;
                        let py = H/2 + Math.sin(p.theta)*p.r;
                        ctx.beginPath(); ctx.arc(px, py, p.size, 0, Math.PI*2); ctx.fill();
                    }
                    ctx.restore();
                }
            }
        }
        
        // SCENE 4: BLINDING WHITE FLASH ACCELERATION
        var flashAlpha = 0;
        if (dt >= T_FLASH && dt < T_LOGO_REVEAL + 1200) {
            flashAlpha = 1.0 - ((dt - T_FLASH) / 1200);
            if(flashAlpha < 0) flashAlpha = 0;
            ctx.fillStyle = `rgba(255, 255, 255, ${flashAlpha})`;
            ctx.fillRect(0,0,W,H);
        }

        // SCENE 5 & 6: SOLID LOGO REVEAL & TAGLINE
        if (dt >= T_LOGO_REVEAL) {
            var logoAlpha = Math.min((dt - T_LOGO_REVEAL) / 300, 1.0);
            
            // Final Sequence Fade Out
            if (dt > T_EXIT - 1000) logoAlpha = 1.0 - ((dt - (T_EXIT-1000))/1000); 
            if (logoAlpha < 0) logoAlpha = 0;

            // Brand cinematic backing
            var bgGrad = ctx.createRadialGradient(W/2, H/2, 0, W/2, H/2, W);
            bgGrad.addColorStop(0, `rgba(4, 30, 60, ${logoAlpha})`); 
            bgGrad.addColorStop(0.5, `rgba(1, 5, 10, ${logoAlpha})`); 
            bgGrad.addColorStop(1, `rgba(0, 0, 0, ${logoAlpha})`); 
            ctx.fillStyle = bgGrad; ctx.fillRect(0,0,W,H);
            
            var scale = 1.0 + ((dt - T_LOGO_REVEAL) / (T_EXIT - T_LOGO_REVEAL)) * 0.15;
            ctx.save();
            ctx.globalAlpha = logoAlpha;
            ctx.translate(W/2, H/2); ctx.scale(scale, scale); ctx.translate(-W/2, -H/2);
            
            // 3D Solid Metallic Neon Text
            const fs = Math.min(W / 6, 200);
            ctx.font = '900 ' + fs + 'px Outfit, Arial Black, sans-serif';
            ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            
            ctx.shadowColor = '#00F0FF'; ctx.shadowBlur = 60 * logoAlpha;
            
            // Inner Core Text
            var textG = ctx.createLinearGradient(0, H/2-fs, 0, H/2+fs);
            textG.addColorStop(0, '#FFFFFF'); 
            textG.addColorStop(0.3, '#00F0FF'); 
            textG.addColorStop(1, '#003080');
            ctx.fillStyle = textG; 
            ctx.fillText('MEDI-GUARD', W/2, H/2 - 40);
            
            // Stroke Highlight
            ctx.shadowBlur = 0;
            ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(255,255,255,0.6)';
            ctx.strokeText('MEDI-GUARD', W/2, H/2 - 40);
            
            // Cinematic Tagline
            if (dt > T_LOGO_REVEAL + 1500) {
                var tagAlpha = Math.min((dt - (T_LOGO_REVEAL + 1500)) / 1000, 1.0);
                if (dt > T_EXIT - 1000) tagAlpha = logoAlpha; // Link fadeout
                ctx.globalAlpha = Math.min(tagAlpha, logoAlpha);
                
                ctx.font = '300 ' + (fs * 0.22) + 'px Outfit, Arial, sans-serif';
                ctx.fillStyle = '#E0F0FF';
                ctx.letterSpacing = "6px"; // Modern cinematic spacing
                
                // Standard canvas doesn't perfectly support letterSpacing in older browsers so we use a hack if needed, 
                // but letterSpacing works in all modern Chrome/Edge for the past few years.
                if (ctx.letterSpacing !== undefined) ctx.letterSpacing = "8px";
                
                ctx.fillText('Denial-Proof Your Medical Decisions', W/2, H/2 + fs*0.65);
            }
            ctx.restore();
            
            // Reapply flash if still decaying so text reveals through the light
            if (flashAlpha > 0) {
                ctx.fillStyle = `rgba(255, 255, 255, ${flashAlpha})`; ctx.fillRect(0,0,W,H);
            }
        }
        
        // SCENE 7: AUTO DASHBOARD REDIRECT
        if (dt >= T_EXIT && !exited) {
            exited = true;
            // Bypass login screens entirely and go to dashboard
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
