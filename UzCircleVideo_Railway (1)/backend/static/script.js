
const form = document.getElementById('uploadForm');
const videoInput = document.getElementById('videoInput');
const downloadLink = document.getElementById('downloadLink');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if(videoInput.files.length === 0) return alert("Videoni tanlang!");
    const file = videoInput.files[0];
    if(file.size > 5*60*1024*1024) return alert("⚠️ Video 5 daqiqadan uzun bo'lmasligi kerak!");
    const formData = new FormData();
    formData.append("video", file);

    downloadLink.style.display = "none";
    downloadLink.innerText = "⏳ Qayta ishlanmoqda...";

    try {
        const res = await fetch("/upload", { method:"POST", body: formData });
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        downloadLink.href = url;
        downloadLink.download = "dumaloq_video.mp4";
        downloadLink.style.display = "block";
        downloadLink.innerText = "📥 Yuklab olish";
    } catch(err) {
        alert("❌ Xatolik yuz berdi!");
        downloadLink.style.display = "none";
    }
});
