let socket = null;
let mediaStream = null;
let audioContext = null;
let workletNode = null;

const statusDisplay = document.getElementById("status");
const startBtn = document.getElementById("start");
const stopBtn = document.getElementById("stop");

// Convert Float32 array (-1.0 to 1.0) to 16-bit signed PCM ArrayBuffer (pcm_s16le)
function convertFloat32ToPCM16(float32Array) {
    const buffer = new ArrayBuffer(float32Array.length * 2);
    const view = new DataView(buffer);
    for (let i = 0; i < float32Array.length; i++) {
        const sample = Math.max(-1.0, Math.min(1.0, float32Array[i]));
        const intSample = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
        view.setInt16(i * 2, intSample, true); // Little-endian
    }
    return buffer;
}

if (startBtn) {
    startBtn.onclick = async () => {
        try {
            statusDisplay.textContent = "Requesting microphone permission...";
            mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    channelCount: 1,
                    sampleRate: 16000
                }
            });

            statusDisplay.textContent = "Connecting WebSocket (/ws/exam)...";
            const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
            const wsUrl = `${protocol}//${window.location.host}/ws/exam/demo-audio-session`;

            socket = new WebSocket(wsUrl);

            socket.onopen = async () => {
                statusDisplay.textContent = "WebSocket Connected. Initializing AudioWorklet...";
                
                // Notify server of session audio start
                socket.send(JSON.stringify({
                    type: "audio_start",
                    data: { sample_rate: 16000, channels: 1, format: "pcm_s16le" }
                }));

                audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
                await audioContext.audioWorklet.addModule("/pcm-processor.js");

                const sourceNode = audioContext.createMediaStreamSource(mediaStream);
                workletNode = new AudioWorkletNode(audioContext, "pcm-processor");

                workletNode.port.onmessage = (event) => {
                    const float32Samples = event.data;
                    if (float32Samples && socket && socket.readyState === WebSocket.OPEN) {
                        const pcm16Buffer = convertFloat32ToPCM16(float32Samples);
                        socket.send(pcm16Buffer);
                    }
                };

                sourceNode.connect(workletNode);
                // Connect worklet node through a gain set to 0 to prevent audio feedback
                const muteGain = audioContext.createGain();
                muteGain.gain.value = 0;
                workletNode.connect(muteGain);
                muteGain.connect(audioContext.destination);

                statusDisplay.textContent = "🔴 Microphone Recording Active (16kHz PCM Streaming)";
                startBtn.disabled = true;
                if (stopBtn) stopBtn.disabled = false;
            };

            socket.onmessage = (event) => {
                const message = JSON.parse(event.data);
                console.log("[Client WebSocket Event]", message);
                if (message.type === "state") {
                    const stateData = message.data || {};
                    statusDisplay.textContent = `State: ${stateData.state || 'ACTIVE'} | Duration: ${stateData.buffered_duration_sec || 0}s`;
                }
            };

            socket.onerror = (err) => {
                console.error("WebSocket error:", err);
                statusDisplay.textContent = "WebSocket Error";
            };

            socket.onclose = () => {
                statusDisplay.textContent = "WebSocket Connection Closed";
                stopMicrophone();
            };

        } catch (err) {
            console.error("Microphone access failed:", err);
            statusDisplay.textContent = "Microphone Error: " + err.message;
        }
    };
}

if (stopBtn) {
    stopBtn.onclick = () => {
        stopMicrophone();
    };
}

function stopMicrophone() {
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }
    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: "audio_end" }));
        socket.close();
        socket = null;
    }
    statusDisplay.textContent = "Microphone stopped";
    if (startBtn) startBtn.disabled = false;
    if (stopBtn) stopBtn.disabled = true;
}
