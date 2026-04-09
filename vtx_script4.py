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

    // ── MASSIVE CUBE QUALITY UPGRADE ──
    // 128x128 high-res rendering with true isometric geometry, glowing cores, and sharp glass speculars
    function generateUltraPremiumCubeCanvas(hue) {
        var c = document.createElement('canvas');
        var size = 128; 
        c.width = size; c.height = size;
        var x = c.getContext('2d');
        
        var R = 54; // Hexagon Radius
        var CX = 64; 
        var CY = 64;
        var DX = R * 0.866025; // cos(30) * R
        var DY = R * 0.5;      // sin(30) * R

        // 1. Draw glowing inner CPU core (volumetric light sphere behind the glass)
        var core = x.createRadialGradient(CX, CY, 0, CX, CY, R * 0.9);
        core.addColorStop(0, `hsla(${hue}, 100%, 80%, 0.8)`);
        core.addColorStop(0.4, `hsla(${hue}, 100%, 50%, 0.4)`);
        core.addColorStop(1, `hsla(${hue}, 100%, 20%, 0.0)`);
        x.fillStyle = core;
        x.beginPath(); x.arc(CX, CY, R*0.9, 0, Math.PI*2); x.fill();

        // 2. Front Left Face (Dark shading)
        var gL = x.createLinearGradient(CX - DX, CY + DY, CX, CY + R);
        gL.addColorStop(0, `hsla(${hue}, 100%, 60%, 0.65)`);
        gL.addColorStop(1, `hsla(${hue+30}, 100%, 10%, 0.95)`);
        x.fillStyle = gL;
        x.beginPath(); 
        x.moveTo(CX, CY); 
        x.lineTo(CX - DX, CY - DY);
        x.lineTo(CX - DX, CY + DY);
        x.lineTo(CX, CY + R);
        x.fill();

        // 3. Front Right Face (Medium shading)
        var gR = x.createLinearGradient(CX + DX, CY + DY, CX, CY + R);
        gR.addColorStop(0, `hsla(${hue}, 100%, 40%, 0.75)`);
        gR.addColorStop(1, `hsla(${hue-20}, 100%, 5%, 0.95)`);
        x.fillStyle = gR;
        x.beginPath();
        x.moveTo(CX, CY);
        x.lineTo(CX + DX, CY - DY);
        x.lineTo(CX + DX, CY + DY);
        x.lineTo(CX, CY + R);
        x.fill();

        // 4. Top Face (Intense Sky Specular Reflection)
        var gT = x.createLinearGradient(CX, CY, CX, CY - R);
        gT.addColorStop(0, `hsla(${hue}, 40%, 100%, 0.95)`); // Pure white hit hot-spot
        gT.addColorStop(1, `hsla(${hue}, 100%, 60%, 0.3)`);
        x.fillStyle = gT;
        x.beginPath();
        x.moveTo(CX, CY);
        x.lineTo(CX - DX, CY - DY);
        x.lineTo(CX, CY - R);
        x.lineTo(CX + DX, CY - DY);
        x.fill();

        // 5. Razor Sharp Inner Wireframe Lighting
        x.lineJoin = "round";
        x.lineWidth = 2.5; // Thicker inner rims for bold sci-fi look
        x.strokeStyle = `hsla(${hue}, 100%, 90%, 0.8)`;
        x.beginPath(); x.moveTo(CX, CY); x.lineTo(CX, CY + R); x.stroke();
        x.beginPath(); x.moveTo(CX, CY); x.lineTo(CX - DX, CY - DY); x.stroke();
        x.beginPath(); x.moveTo(CX, CY); x.lineTo(CX + DX, CY - DY); x.stroke();

        // 6. Outer Hexagon Perimeter (Soft edge glow)
        x.lineWidth = 1.0;
        x.strokeStyle = `hsla(${hue}, 100%, 100%, 0.5)`;
        x.beginPath();
        x.moveTo(CX, CY - R);
        x.lineTo(CX + DX, CY - DY);
        x.lineTo(CX + DX, CY + DY);
        x.lineTo(CX, CY + R);
        x.lineTo(CX - DX, CY + DY);
        x.lineTo(CX - DX, CY - DY);
        x.closePath();
        x.stroke();

        return c;
    }

    const premiumCubes = [
        generateUltraPremiumCubeCanvas(180), generateUltraPremiumCubeCanvas(200),
        generateUltraPremiumCubeCanvas(260), generateUltraPremiumCubeCanvas(280)
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
            var startZ = 2000 + Math.random() * 8000;
            var r = W * 2 + Math.random() * W * 2;
            var startX = Math.cos(a) * r;
            var startY = Math.sin(a) * r;

            var cpX = (Math.random() - 0.5) * W * 6;
            var cpY = -H * 2 - Math.random() * H * 4;
            var cpZ = -1000 - Math.random() * 4000; 

            particles.push({
                sx: startX, sy: startY, sz: startZ,
                cpX: cpX, cpY: cpY, cpZ: cpZ,
                tx: targets[i].x, ty: targets[i].y, tz: 0,
                delay: Math.random() * 3000, 
                sz: 3 + Math.random() * 4,
                rotSpeed: (Math.random() - 0.5) * 0.02, 
                wobbleFreq: 0.005 + Math.random() * 0.015,
                wobbleAmp: 100 + Math.random() * 400,
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
                rotSpeed: (Math.random() - 0.5) * 0.02,
                rot: Math.random() * Math.PI,
                isText: false, px: 0, py: 0, lpx: 0, lpy: 0
            });
        }

        // Expanded timeline! SLOWED DOWN BY ALMOST DOUBLE.
        const T_ASSEMBLE = 8000, T_SOLID = 8100, T_GLOW = 8500, T_EXIT = 10000;
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

        function playCinematicAudio() {
            try {
                var ac = new (window.AudioContext || window.webkitAudioContext)();
                var master = ac.createGain(); 
                master.gain.value = 0.9; 
                master.connect(ac.destination);
                
                var createPanner = () => {
                    var panner = ac.createStereoPanner ? ac.createStereoPanner() : ac.createGain();
                    panner.connect(master);
                    return panner;
                };

                var riserPanner = createPanner();
                if (riserPanner.pan) {
                    riserPanner.pan.setValueAtTime(1.0, ac.currentTime);
                    riserPanner.pan.linearRampToValueAtTime(-1.0, ac.currentTime + 3.0);
                    riserPanner.pan.linearRampToValueAtTime(0.5, ac.currentTime + 6.0);
                    riserPanner.pan.linearRampToValueAtTime(0.0, ac.currentTime + 7.8);
                }

                const freqs = [55, 110, 165, 220, 275, 440];
                freqs.forEach(f => {
                    var osc = ac.createOscillator(); osc.type = 'sawtooth';
                    var oscFilter = ac.createBiquadFilter(); oscFilter.type = 'lowpass';
                    oscFilter.frequency.setValueAtTime(50, ac.currentTime);
                    oscFilter.frequency.exponentialRampToValueAtTime(10000, ac.currentTime + 7.9);
                    
                    var lfo = ac.createOscillator(); lfo.type = 'sine'; lfo.frequency.value = 0.5 + Math.random() * 2;
                    var lfoGain = ac.createGain(); lfoGain.gain.value = 3; 
                    lfo.connect(lfoGain); lfoGain.connect(osc.detune);
                    lfo.start(ac.currentTime);

                    var oscGain = ac.createGain();
                    oscGain.gain.setValueAtTime(0.01, ac.currentTime);
                    oscGain.gain.exponentialRampToValueAtTime(0.15, ac.currentTime + 7.5);
                    oscGain.gain.linearRampToValueAtTime(0, ac.currentTime + 8.1);
                    
                    osc.frequency.setValueAtTime(f * 0.25, ac.currentTime); 
                    osc.frequency.exponentialRampToValueAtTime(f, ac.currentTime + 7.9);
                    
                    osc.connect(oscFilter).connect(oscGain).connect(riserPanner);
                    osc.start(ac.currentTime);
                });

                var swarmPanner = createPanner();
                if (swarmPanner.pan) {
                    swarmPanner.pan.setValueAtTime(0.0, ac.currentTime);
                    for(let t=1; t<=7; t++) {
                        swarmPanner.pan.linearRampToValueAtTime((Math.random()-0.5)*2, ac.currentTime + t);
                    }
                    swarmPanner.pan.linearRampToValueAtTime(0, ac.currentTime + 7.8);
                }

                var bufferSize = ac.sampleRate * 2; 
                var noiseBuffer = ac.createBuffer(1, bufferSize, ac.sampleRate);
                var output = noiseBuffer.getChannelData(0);
                var lastOut = 0;
                for (let i = 0; i < bufferSize; i++) {
                    var white = Math.random() * 2 - 1;
                    output[i] = (lastOut + (0.02 * white)) / 1.02; 
                    lastOut = output[i];
                    output[i] *= 4.5; 
                }
                var noise = ac.createBufferSource(); 
                noise.buffer = noiseBuffer;
                noise.loop = true;
                
                var noiseFilter = ac.createBiquadFilter(); 
                noiseFilter.type = 'bandpass';
                noiseFilter.Q.value = 1.5;
                noiseFilter.frequency.setValueAtTime(100, ac.currentTime);
                noiseFilter.frequency.exponentialRampToValueAtTime(6000, ac.currentTime + 7.8);
                
                var noiseGain = ac.createGain(); 
                noiseGain.gain.setValueAtTime(0.01, ac.currentTime);
                noiseGain.gain.exponentialRampToValueAtTime(0.3, ac.currentTime + 4.0);
                noiseGain.gain.exponentialRampToValueAtTime(1.5, ac.currentTime + 7.8);
                noiseGain.gain.setTargetAtTime(0, ac.currentTime + 8.1, 0.1); 

                noise.connect(noiseFilter).connect(noiseGain).connect(swarmPanner);
                noise.start(ac.currentTime);
                noise.stop(ac.currentTime + 9);

                var impactPanner = createPanner();
                if (impactPanner.pan) impactPanner.pan.value = 0;

                var snapOsc = ac.createOscillator(); snapOsc.type = 'square';
                snapOsc.frequency.setValueAtTime(8000, ac.currentTime + 8.0);
                snapOsc.frequency.exponentialRampToValueAtTime(100, ac.currentTime + 8.15);
                var snapGain = ac.createGain();
                snapGain.gain.setValueAtTime(0, ac.currentTime + 7.99);
                snapGain.gain.setValueAtTime(0.8, ac.currentTime + 8.0);
                snapGain.gain.exponentialRampToValueAtTime(0.01, ac.currentTime + 8.3);
                snapOsc.connect(snapGain).connect(impactPanner);
                snapOsc.start(ac.currentTime + 8.0);

                var subPanner = createPanner();
                if (subPanner.pan) subPanner.pan.value = 0;

                var sub = ac.createOscillator(); sub.type = 'sine';
                sub.frequency.setValueAtTime(150, ac.currentTime + 8.0);
                sub.frequency.exponentialRampToValueAtTime(20, ac.currentTime + 9.5);
                var subGain = ac.createGain(); 
                subGain.gain.setValueAtTime(0, ac.currentTime + 7.99);
                subGain.gain.setValueAtTime(1.5, ac.currentTime + 8.0);
                subGain.gain.exponentialRampToValueAtTime(0.01, ac.currentTime + 10.0);
                sub.connect(subGain).connect(subPanner);
                sub.start(ac.currentTime + 8.0);

            } catch (e) {}
        }

        function runSequence() {
            t0 = performance.now();
            playCinematicAudio();
            frame();
        }

        function frame() {
            raf = requestAnimationFrame(frame);
            var dt = performance.now() - t0;

            // ── MASSIVE CINEMATIC BACKGROUND ──
            // Simulates deep volumetric space fog instead of flat color
            var sway1 = Math.sin(dt*0.001)*100;
            var sway2 = Math.cos(dt*0.001)*100;
            var bgGrad = ctx.createRadialGradient(W/2 + sway1, H/2 + sway2, 0, W/2, H/2, W);
            bgGrad.addColorStop(0, '#0a1a3a'); // Luminous deep blue flare
            bgGrad.addColorStop(0.3, '#040b17'); // Pitch space
            bgGrad.addColorStop(0.8, '#010305'); // Abyss
            bgGrad.addColorStop(1, '#000000'); // Void
            ctx.fillStyle = bgGrad; 
            ctx.fillRect(0, 0, W, H);
            
            // ── HI-TECH HORIZON GRID ──
            // Gives the cubes a physical space to orbit within instead of floating endlessly in empty space
            ctx.save();
            ctx.translate(W/2, H/2);
            var gScale = 1 + Math.sin(dt*0.0005)*0.1;
            ctx.scale(gScale, gScale);
            // Dynamic Grid alpha based on camera flash
            var gridAlpha = 0.05 + (dt < T_ASSEMBLE ? Math.sin(dt*0.002)*0.02 : 0);
            ctx.strokeStyle = `rgba(0, 240, 255, ${gridAlpha})`;
            ctx.lineWidth = 1;
            var gap = 150;
            var ext = Math.max(W, H) * 1.5;
            ctx.beginPath();
            for(var x = -ext; x <= ext; x+=gap) {
                ctx.moveTo(x, -ext); ctx.lineTo(x, ext);
            }
            for(var y = -ext; y <= ext; y+=gap) {
                ctx.moveTo(-ext, y); ctx.lineTo(ext, y);
            }
            ctx.stroke();
            ctx.restore();

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

            // Shockwave glow pre-render
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
                        var pRot = 0;
                        
                        if (dt < T_ASSEMBLE) {
                            var fp = Math.min(activeTime / localAssemble, 1);
                            var t = 1 - Math.pow(1 - fp, 3);
                            var u = 1 - t;

                            var wobbleX = Math.cos(activeTime * p.wobbleFreq) * p.wobbleAmp * u;
                            var wobbleY = Math.sin(activeTime * p.wobbleFreq) * p.wobbleAmp * u;

                            p.x = u*u*p.sx + 2*u*t*p.cpX + t*t*p.tx + wobbleX;
                            p.y = u*u*p.sy + 2*u*t*p.cpY + t*t*p.ty + wobbleY;
                            p.z = u*u*p.sz + 2*u*t*p.cpZ + t*t*p.tz;

                            pRot = p.rotSpeed * activeTime * u;
                        } else {
                            p.x = p.tx; p.y = p.ty; p.z = p.tz;
                            pRot = 0;
                        }

                        var depthScale = FL / (FL + Math.max(1, p.z));
                        p.px = W / 2 + p.x * depthScale; p.py = H / 2 + p.y * depthScale;

                        if (p.z < -FL * 0.9) continue; 
                        
                        var renderAlpha = particleAlphaMaster;
                        if (activeTime < 700) renderAlpha *= (activeTime / 700); 

                        if (activeTime > 0) {
                            var w = Math.max(0.1, p.sz * depthScale) * 0.8; // Adjusted down slightly due to higher res source
                            
                            if (p.lpx !== 0 && dt < T_ASSEMBLE && p.z > -FL + 10) {
                                var dispX = p.px - p.lpx, dispY = p.py - p.lpy;
                                var speed = Math.sqrt(dispX*dispX + dispY*dispY);
                                if (speed > 4) {
                                    ctx.beginPath(); ctx.moveTo(p.lpx, p.lpy); ctx.lineTo(p.px, p.py);
                                    ctx.lineWidth = w * 0.4; ctx.strokeStyle = `hsla(${p.hue}, 100%, 65%, ${0.5 * renderAlpha})`;
                                    ctx.stroke();
                                }
                            }
                            ctx.save();
                            ctx.translate(p.px, p.py);
                            // Draw the Ultra Premium Hexagon Cube using precise size constraints
                            ctx.rotate(pRot);
                            ctx.globalAlpha = renderAlpha;
                            // Width is 128px in source. To map tightly to W, we draw w*4
                            var ds = w*3.5;
                            ctx.drawImage(premiumCubes[p.cubeIdx], -ds/2, -ds/2, ds, ds);
                            ctx.restore();
                        }
                    } else {
                        p.z += p.vz;
                        p.rot += p.rotSpeed * 10;
                        if (p.z < -FL + 100) {
                            p.z = 8000; p.x = (Math.random() - 0.5) * W * 5; p.y = (Math.random() - 0.5) * H * 5; p.lpx = 0;
                        }
                        var scale = FL / (FL + Math.max(1, p.z));
                        p.px = W / 2 + p.x * scale; p.py = H / 2 + p.y * scale;
                        var w = p.sz * scale * 0.8;
                        if (p.lpx !== 0 && scale > 0) {
                            ctx.save();
                            ctx.translate(p.px, p.py);
                            ctx.rotate(p.rot);
                            ctx.globalAlpha = 0.15 + flashAlpha * 0.3;
                            var ds = w*3.5;
                            ctx.drawImage(premiumCubes[p.cubeIdx], -ds/2, -ds/2, ds, ds);
                            ctx.restore();
                        }
                    }
                }
            }
            ctx.restore(); 

            if (dt < T_ASSEMBLE) {
                ctx.save();
                ctx.fillStyle = '#00F0FF';
                ctx.font = '500 12px "Courier New", monospace';
                ctx.textAlign = 'left';
                var progress = Math.min((dt / T_ASSEMBLE) * 100, 100).toFixed(2);
                ctx.fillText(`[ MAIN.PROC ] FLIGHT DYNAMICS: ${progress}%`, 30, 40);
                ctx.fillText(`> RECTIFYING 3D TRAJECTORY...`, 30, 60);
                ctx.fillText(`> LOCKING ALL SENSOR MATRICES`, 30, 80);
                
                ctx.beginPath();
                var radarCenterY = H - 60, radarCenterX = 60;
                var radarSweep = (dt * 0.003) % (Math.PI * 2);
                ctx.arc(radarCenterX, radarCenterY, 30, 0, Math.PI * 2);
                ctx.strokeStyle = 'rgba(0, 240, 255, 0.3)'; ctx.stroke();
                ctx.moveTo(radarCenterX, radarCenterY);
                ctx.lineTo(radarCenterX + Math.cos(radarSweep)*30, radarCenterY + Math.sin(radarSweep)*30);
                ctx.strokeStyle = '#00F0FF'; ctx.stroke();
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
