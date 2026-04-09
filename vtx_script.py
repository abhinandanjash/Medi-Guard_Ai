import re
with open("app/static/app.js", "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

NEW_INIT_LANDING_PAGE = """function initLandingPage() {
    const landing = document.getElementById('medi-guard-landing');
    const canvas = document.getElementById('vfx-canvas');
    if (!canvas || !landing) return;

    const ctx = canvas.getContext('2d');
    let W, H;
    const FL = 1000; 

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

    function generatePremiumCubeCanvas(hue) {
        var c = document.createElement('canvas');
        var size = 64; 
        c.width = size; c.height = size;
        var x = c.getContext('2d');
        
        var gF = x.createLinearGradient(16, 32, 48, 64);
        gF.addColorStop(0, `hsla(${hue}, 100%, 75%, 0.95)`);
        gF.addColorStop(1, `hsla(${hue + 20}, 100%, 35%, 0.95)`);
        x.fillStyle = gF;
        x.fillRect(16, 32, 32, 32);

        var gT = x.createLinearGradient(16, 32, 48, 0);
        gT.addColorStop(0, `hsla(${hue}, 20%, 100%, 0.95)`);
        gT.addColorStop(1, `hsla(${hue}, 100%, 65%, 0.95)`);
        x.fillStyle = gT;
        x.beginPath(); x.moveTo(16, 32); x.lineTo(32, 16); x.lineTo(64, 16); x.lineTo(48, 32); x.fill();

        var gR = x.createLinearGradient(48, 32, 64, 64);
        gR.addColorStop(0, `hsla(${hue}, 100%, 45%, 0.95)`);
        gR.addColorStop(1, `hsla(${hue - 20}, 100%, 15%, 0.95)`);
        x.fillStyle = gR;
        x.beginPath(); x.moveTo(48, 32); x.lineTo(64, 16); x.lineTo(64, 48); x.lineTo(48, 64); x.fill();
        
        x.strokeStyle = `hsla(${hue}, 100%, 95%, 0.5)`;
        x.lineWidth = 1;
        x.strokeRect(16, 32, 32, 32);
        x.beginPath(); x.moveTo(16,32); x.lineTo(32,16); x.lineTo(64,16); x.lineTo(48,32); x.closePath(); x.stroke();
        x.beginPath(); x.moveTo(48,32); x.lineTo(64,16); x.lineTo(64,48); x.lineTo(48,64); x.closePath(); x.stroke();

        return c;
    }

    const premiumCubes = [
        generatePremiumCubeCanvas(180), generatePremiumCubeCanvas(200),
        generatePremiumCubeCanvas(260), generatePremiumCubeCanvas(280)
    ];

    function sampleText() {
        const off = document.createElement('canvas');
        off.width = W; off.height = H;
        const oc = off.getContext('2d');
        const fs = Math.min(W / 7, 180);
        oc.font = '900 ' + fs + 'px Outfit, Arial Black, Impact, sans-serif';
        oc.textAlign = 'center';
        oc.textBaseline = 'middle';
        oc.fillStyle = '#fff';
        oc.fillText('MEDI-GUARD', W / 2, H / 2);
        const d = oc.getImageData(0, 0, W, H).data;
        const pts = [];
        const gap = Math.max(2, Math.floor(Math.min(W, H) / 450));
        for (let y = 0; y < H; y += gap) {
            for (let x = 0; x < W; x += gap) {
                if (d[(y * W + x) * 4 + 3] > 128) {
                    pts.push({ x: x - W/2, y: y - H/2 });
                }
            }
        }
        for (let i = pts.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            var tmp = pts[i]; pts[i] = pts[j]; pts[j] = tmp;
        }
        return pts;
    }

    document.fonts.ready.then(function() {
        var allPts = sampleText();
        var N = Math.min(allPts.length, 6000);
        var targets = allPts.slice(0, N);

        var particles = [];
        for (var i = 0; i < N; i++) {
            var a = Math.random() * Math.PI * 2;
            
            // Dramatic origin points - huge sphere around player
            var startZ = 2000 + Math.random() * 8000;
            var r = W * 2 + Math.random() * W * 2;
            var startX = Math.cos(a) * r;
            var startY = Math.sin(a) * r;

            // Grand cinematic control points for massive swooping bezier curves
            var cpX = (Math.random() - 0.5) * W * 4;
            var cpY = -H * 2 - Math.random() * H * 4; // Sweeps up high then crashes down
            var cpZ = -1000 - Math.random() * 4000; // Pulls extremely close to camera on the way in

            particles.push({
                sx: startX, sy: startY, sz: startZ,
                cpX: cpX, cpY: cpY, cpZ: cpZ,
                tx: targets[i].x, ty: targets[i].y, tz: 0,
                delay: Math.random() * 2000, // Stagger over a 2 second period
                sz: 3 + Math.random() * 4,
                cubeIdx: Math.floor(Math.random() * premiumCubes.length),
                hue: 180 + Math.random() * 100,
                isText: true,
                px: 0, py: 0, lpx: 0, lpy: 0
            });
        }

        for (var j = 0; j < 500; j++) {
            particles.push({
                x: (Math.random() - 0.5) * W * 5, y: (Math.random() - 0.5) * H * 5, z: Math.random() * 6000,
                vz: -30 - Math.random() * 60,
                sz: 1 + Math.random() * 3,
                cubeIdx: Math.floor(Math.random() * premiumCubes.length),
                isText: false, px: 0, py: 0, lpx: 0, lpy: 0
            });
        }

        const T_ASSEMBLE = 4500, T_SOLID = 4600, T_GLOW = 5000, T_EXIT = 6500;
        var t0, raf, exited = false;

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

        /* PREMIUM CINEMATIC AUDIO ENGINE 
           Synthesizing high-end sci-fi audio using complex additive + FM synthesis 
        */
        function playCinematicAudio() {
            try {
                var ac = new (window.AudioContext || window.webkitAudioContext)();
                var master = ac.createGain(); 
                master.gain.value = 0.9; 
                master.connect(ac.destination);

                // 1. Core THX-Style Rising Chord (Hans Zimmer style)
                const freqs = [55, 110, 165, 220, 275, 440]; // Deep A major complex
                freqs.forEach(f => {
                    var osc = ac.createOscillator();
                    osc.type = 'sawtooth';
                    
                    var oscFilter = ac.createBiquadFilter();
                    oscFilter.type = 'lowpass';
                    oscFilter.frequency.setValueAtTime(50, ac.currentTime);
                    oscFilter.frequency.exponentialRampToValueAtTime(10000, ac.currentTime + 4.5);
                    
                    var lfo = ac.createOscillator();
                    lfo.type = 'sine';
                    lfo.frequency.value = 0.5 + Math.random() * 2;
                    var lfoGain = ac.createGain();
                    lfoGain.gain.value = 2; // Subtle detune warble
                    lfo.connect(lfoGain);
                    lfoGain.connect(osc.detune);
                    lfo.start(ac.currentTime);

                    var oscGain = ac.createGain();
                    oscGain.gain.setValueAtTime(0, ac.currentTime);
                    oscGain.gain.exponentialRampToValueAtTime(0.15, ac.currentTime + 4.0);
                    oscGain.gain.linearRampToValueAtTime(0, ac.currentTime + 4.6);
                    
                    osc.frequency.setValueAtTime(f * 0.25, ac.currentTime); 
                    osc.frequency.exponentialRampToValueAtTime(f, ac.currentTime + 4.5);
                    
                    osc.connect(oscFilter).connect(oscGain).connect(master);
                    osc.start(ac.currentTime);
                });

                // 2. Swarm Audio - The sound of 6000 cubes moving
                // We use filtered pink-noise-like synthesis that pans and swells
                var bufferSize = ac.sampleRate * 2; 
                var noiseBuffer = ac.createBuffer(1, bufferSize, ac.sampleRate);
                var output = noiseBuffer.getChannelData(0);
                var lastOut = 0;
                for (let i = 0; i < bufferSize; i++) {
                    var white = Math.random() * 2 - 1;
                    output[i] = (lastOut + (0.02 * white)) / 1.02; // brown/pink noise approximation
                    lastOut = output[i];
                    output[i] *= 4.5; 
                }
                var noise = ac.createBufferSource(); 
                noise.buffer = noiseBuffer;
                noise.loop = true;
                
                var noiseFilter = ac.createBiquadFilter(); 
                noiseFilter.type = 'bandpass';
                noiseFilter.Q.value = 1.5;
                noiseFilter.frequency.setValueAtTime(200, ac.currentTime);
                noiseFilter.frequency.exponentialRampToValueAtTime(4000, ac.currentTime + 4.5);
                
                var noiseGain = ac.createGain(); 
                noiseGain.gain.setValueAtTime(0, ac.currentTime);
                noiseGain.gain.linearRampToValueAtTime(0.6, ac.currentTime + 2.0); // Cubes rushing in
                noiseGain.gain.exponentialRampToValueAtTime(1.0, ac.currentTime + 4.2); // Assembly peak
                noiseGain.gain.setTargetAtTime(0, ac.currentTime + 4.6, 0.1); 

                noise.connect(noiseFilter).connect(noiseGain).connect(master);
                noise.start(ac.currentTime);
                noise.stop(ac.currentTime + 6);

                // 3. Impact / Form Solidification (The Snap)
                var snapOsc = ac.createOscillator();
                snapOsc.type = 'square';
                snapOsc.frequency.setValueAtTime(8000, ac.currentTime + 4.5);
                snapOsc.frequency.exponentialRampToValueAtTime(100, ac.currentTime + 4.65);
                
                var snapGain = ac.createGain();
                snapGain.gain.setValueAtTime(0, ac.currentTime + 4.49);
                snapGain.gain.setValueAtTime(0.8, ac.currentTime + 4.5);
                snapGain.gain.exponentialRampToValueAtTime(0.01, ac.currentTime + 4.8);
                
                snapOsc.connect(snapGain).connect(master);
                snapOsc.start(ac.currentTime + 4.5);

                // Sub-Bass Boom
                var sub = ac.createOscillator(); sub.type = 'sine';
                sub.frequency.setValueAtTime(150, ac.currentTime + 4.5);
                sub.frequency.exponentialRampToValueAtTime(20, ac.currentTime + 5.5);
                var subGain = ac.createGain(); 
                subGain.gain.setValueAtTime(0, ac.currentTime + 4.49);
                subGain.gain.setValueAtTime(1.5, ac.currentTime + 4.5);
                subGain.gain.exponentialRampToValueAtTime(0.01, ac.currentTime + 7.0);
                sub.connect(subGain).connect(master);
                sub.start(ac.currentTime + 4.5);

            } catch (e) {
                console.error("Audio engine failed", e);
            }
        }

        function runSequence() {
            t0 = performance.now();
            playCinematicAudio();
            frame();
        }

        function frame() {
            raf = requestAnimationFrame(frame);
            var dt = performance.now() - t0;

            if (dt < T_ASSEMBLE) {
                ctx.fillStyle = 'rgba(2, 6, 15, 0.4)'; ctx.fillRect(0, 0, W, H);
            } else {
                var bgGrad = ctx.createRadialGradient(W/2, H/2, 0, W/2, H/2, W);
                bgGrad.addColorStop(0, '#04162a'); bgGrad.addColorStop(0.5, '#01050a'); bgGrad.addColorStop(1, '#000000'); 
                ctx.fillStyle = bgGrad; ctx.fillRect(0, 0, W, H);
            }

            var flashAlpha = 0;
            if (dt > T_ASSEMBLE && dt < T_ASSEMBLE + 800) flashAlpha = 1 - ((dt - T_ASSEMBLE) / 800);

            var shakeX = 0, shakeY = 0;
            if (flashAlpha > 0.05) {
                shakeX = (Math.random() - 0.5) * 50 * Math.pow(flashAlpha, 2);
                shakeY = (Math.random() - 0.5) * 50 * Math.pow(flashAlpha, 2);
            }

            var camScale = 1 + (dt / T_EXIT) * 0.18; 
            ctx.save();
            ctx.translate(W/2 + shakeX, H/2 + shakeY);
            ctx.scale(camScale, camScale);
            ctx.translate(-W/2, -H/2);

            if (dt > T_ASSEMBLE / 2) {
                var gp = Math.min((dt - T_ASSEMBLE / 2) / (T_GLOW - T_ASSEMBLE / 2), 1);
                var glowAlpha = 0.15 * gp + flashAlpha * 0.4;
                var rg = ctx.createRadialGradient(W/2, H/2, 0, W/2, H/2, W * 0.6);
                rg.addColorStop(0, 'rgba(0, 240, 255,' + glowAlpha * 0.4 + ')');
                rg.addColorStop(0.5, 'rgba(0, 100, 200,' + (glowAlpha * 0.2) + ')');
                rg.addColorStop(1, 'rgba(0,0,0,0)');
                ctx.fillStyle = rg; ctx.fillRect(0, 0, W, H);
            }

            ctx.save();
            ctx.globalCompositeOperation = 'lighter';
            
            var particleAlphaMaster = 1.0;
            if (dt > T_SOLID) particleAlphaMaster = 0; 
            else if (dt > T_ASSEMBLE) particleAlphaMaster = 1.0 - ((dt - T_ASSEMBLE) / (T_SOLID - T_ASSEMBLE));

            if (particleAlphaMaster > 0) {
                for (var pi = 0; pi < particles.length; pi++) {
                    var p = particles[pi];
                    p.lpx = p.px; p.lpy = p.py;

                    if (p.isText) {
                        var activeTime = Math.max(0, dt - (p.delay || 0));
                        var localAssemble = Math.max(100, T_ASSEMBLE - (p.delay || 0));
                        
                        if (dt < T_ASSEMBLE) {
                            var fp = Math.min(activeTime / localAssemble, 1);
                            
                            // ── BEZIER SWEEPING ARC PHYSICS ──
                            // Instead of a straight line or simple vortex, cubes fly on dramatic 3D Bezier curves.
                            // They sweep WAY up or down, and whip close to the camera before finding their target.
                            // We use an advanced Quintic easeout so they brake incredibly sharply at the end.
                            var t = 1 - Math.pow(1 - fp, 5);
                            var u = 1 - t;

                            p.x = u*u*p.sx + 2*u*t*p.cpX + t*t*p.tx;
                            p.y = u*u*p.sy + 2*u*t*p.cpY + t*t*p.ty;
                            
                            // Special heavy Z crash physics: Z drops dramatically to make cubes whip closely around user
                            p.z = u*u*p.sz + 2*u*t*p.cpZ + t*t*p.tz;
                            
                        } else {
                            p.x = p.tx; p.y = p.ty; p.z = p.tz;
                        }

                        var depthScale = FL / (FL + Math.max(1, p.z));
                        p.px = W / 2 + p.x * depthScale; p.py = H / 2 + p.y * depthScale;

                        if (p.z < -FL * 0.9) continue; // Behind camera plane
                        
                        var renderAlpha = particleAlphaMaster;
                        if (activeTime < 400) renderAlpha *= (activeTime / 400); // Fade in

                        if (activeTime > 0) {
                            var w = Math.max(0.1, p.sz * depthScale);
                            
                            // Extremely intense light streaks tracing the Bezier arc
                            if (p.lpx !== 0 && dt < T_ASSEMBLE && p.z > -FL + 10) {
                                var dispX = p.px - p.lpx, dispY = p.py - p.lpy;
                                var speed = Math.sqrt(dispX*dispX + dispY*dispY);
                                if (speed > 5) {
                                    ctx.beginPath(); 
                                    ctx.moveTo(p.lpx, p.lpy); 
                                    ctx.lineTo(p.px, p.py);
                                    // Scale stroke width based on Z depth dynamically!
                                    ctx.lineWidth = w * 0.8; 
                                    ctx.strokeStyle = `hsla(${p.hue}, 100%, 65%, ${0.6 * renderAlpha})`;
                                    ctx.stroke();
                                }
                            }
                            ctx.globalAlpha = renderAlpha;
                            ctx.drawImage(premiumCubes[p.cubeIdx], p.px - w*1.5, p.py - w*1.5, w * 3, w * 3);
                            ctx.globalAlpha = 1.0;
                        }
                    } else {
                        // Background particles fly relentlessly
                        p.z += p.vz;
                        if (p.z < -FL + 100) {
                            p.z = 8000; p.x = (Math.random() - 0.5) * W * 5; p.y = (Math.random() - 0.5) * H * 5; p.lpx = 0;
                        }
                        var scale = FL / (FL + Math.max(1, p.z));
                        p.px = W / 2 + p.x * scale; p.py = H / 2 + p.y * scale;
                        var w = p.sz * scale;
                        if (p.lpx !== 0 && scale > 0) {
                            ctx.globalAlpha = 0.15 + flashAlpha * 0.3;
                            ctx.drawImage(premiumCubes[p.cubeIdx], p.px - w*1.5, p.py - w*1.5, w * 3, w * 3);
                            ctx.globalAlpha = 1.0;
                        }
                    }
                }
            }
            ctx.restore(); 

            // HUD Overlays during build
            if (dt < T_ASSEMBLE) {
                ctx.save();
                ctx.fillStyle = '#00F0FF';
                ctx.font = '500 12px "Courier New", monospace';
                ctx.textAlign = 'left';
                var progress = Math.min((dt / T_ASSEMBLE) * 100, 100).toFixed(2);
                ctx.fillText(`[ SYSTEM INIT ] NEURAL ALIGNMENT: ${progress}%`, 30, 40);
                ctx.fillText(`> ENGAGING CUBIC METRICS...`, 30, 60);
                ctx.fillText(`> ALLOCATING ${particles.length} FRAGMENTS`, 30, 80);
                
                // Drawing a mini radar chart
                ctx.beginPath();
                var radarCenterY = H - 60, radarCenterX = 60;
                var radarSweep = (dt * 0.005) % (Math.PI * 2);
                ctx.arc(radarCenterX, radarCenterY, 30, 0, Math.PI * 2);
                ctx.strokeStyle = 'rgba(0, 240, 255, 0.3)';
                ctx.stroke();
                ctx.moveTo(radarCenterX, radarCenterY);
                ctx.lineTo(radarCenterX + Math.cos(radarSweep)*30, radarCenterY + Math.sin(radarSweep)*30);
                ctx.strokeStyle = '#00F0FF';
                ctx.stroke();
                ctx.restore();
            }

            if (dt > T_ASSEMBLE) {
                var solidAlpha = dt < T_SOLID ? (dt - T_ASSEMBLE) / (T_SOLID - T_ASSEMBLE) : 1.0;
                ctx.save();
                const fs = Math.min(W / 7, 180);
                ctx.font = '900 ' + fs + 'px Outfit, Arial Black, Impact, sans-serif';
                ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
                
                var pulseScale = 1 + flashAlpha * 0.05;
                ctx.translate(W/2, H/2); ctx.scale(pulseScale, pulseScale); ctx.translate(-W/2, -H/2);

                ctx.shadowColor = '#00F0FF';
                if (flashAlpha > 0) {
                    ctx.shadowBlur = 150 * Math.pow(flashAlpha, 0.5);
                    var impactGrad = ctx.createLinearGradient(0, H/2 - fs, 0, H/2 + fs);
                    impactGrad.addColorStop(0, `rgba(255, 255, 255, ${flashAlpha})`);
                    impactGrad.addColorStop(0.5, `rgba(0, 240, 255, ${flashAlpha})`);
                    impactGrad.addColorStop(1, `rgba(255, 255, 255, ${flashAlpha})`);
                    ctx.fillStyle = impactGrad; ctx.fillText('MEDI-GUARD', W / 2, H / 2);
                }
                
                ctx.shadowBlur = 40;
                var glassGrad = ctx.createLinearGradient(W/2 - W/4, H/2 - fs, W/2 + W/4, H/2 + fs);
                glassGrad.addColorStop(0, `rgba(200, 255, 255, ${solidAlpha})`); 
                glassGrad.addColorStop(0.25, `rgba(0, 240, 255, ${solidAlpha})`); 
                glassGrad.addColorStop(0.48, `rgba(0, 80, 160, ${solidAlpha})`); 
                glassGrad.addColorStop(0.52, `rgba(180, 250, 255, ${solidAlpha})`); 
                glassGrad.addColorStop(1, `rgba(0, 20, 50, ${solidAlpha})`); 
                ctx.fillStyle = glassGrad; ctx.fillText('MEDI-GUARD', W / 2, H / 2);

                ctx.shadowBlur = 5; ctx.shadowColor = `rgba(255, 255, 255, ${solidAlpha * 0.5})`;
                ctx.lineWidth = 1.5; ctx.strokeStyle = `rgba(255, 255, 255, ${solidAlpha * 0.9})`;
                ctx.strokeText('MEDI-GUARD', W / 2, H / 2);
                ctx.restore();
            }

            ctx.restore(); 

            if (dt >= T_EXIT && !exited) {
                exited = true;
                landing.classList.add('system-active');
                setTimeout(function() {
                    cancelAnimationFrame(raf);
                    landing.remove();
                    document.body.classList.remove('booting');
                    sessionStorage.setItem('bootSequencePlayed', 'true');
                }, 1500);
            }
        }
        frame();
    });
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
